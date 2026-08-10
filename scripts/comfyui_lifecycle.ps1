[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [ValidateSet('start', 'stop', 'status')]
    [string]$Action,
    [string]$ComfyRoot = (Join-Path $PSScriptRoot '..\ComfyUI'),
    [string]$PythonPath,
    [string]$BindHost = '127.0.0.1',
    [int]$Port = 8188
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $ComfyRoot).Path
if (-not $PythonPath) {
    $PythonPath = Join-Path $resolvedRoot '.venv\Scripts\python.exe'
}
$resolvedPython = (Resolve-Path -LiteralPath $PythonPath).Path
$runtimeDir = Join-Path $resolvedRoot '.codex-runtime'
$pidFile = Join-Path $runtimeDir 'comfyui.pid'
$logFile = Join-Path $runtimeDir 'comfyui.stdout.log'
$errorFile = Join-Path $runtimeDir 'comfyui.stderr.log'

function Get-ListenerIds {
    @(Get-NetTCPConnection -LocalAddress $BindHost -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
}

function Get-VerifiedProcess([int]$ProcessId) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    $command = [string]$process.CommandLine
    if ($command -notlike "*$resolvedRoot*") { return $null }
    if ($command -notmatch '(?i)(main\.py|comfyui)') { return $null }
    return $process
}

function Show-Status {
    $listeners = Get-ListenerIds
    [pscustomobject]@{
        action = 'status'
        host = $BindHost
        port = $Port
        listener_pids = @($listeners)
        pid_file = $pidFile
        pid_file_exists = Test-Path -LiteralPath $pidFile
        verified_listener_count = @($listeners | Where-Object { Get-VerifiedProcess $_ }).Count
    } | ConvertTo-Json -Depth 4
}

if ($Action -eq 'status') {
    Show-Status
    exit 0
}

if ($Action -eq 'start') {
    if (Get-ListenerIds) {
        throw "COMFYUI_PORT_IN_USE: refusing to start another server on $BindHost`:$Port"
    }
    if (-not (Test-Path -LiteralPath $resolvedPython -PathType Leaf)) {
        throw "COMFYUI_PYTHON_MISSING: $resolvedPython"
    }
    New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
    $arguments = @('main.py', '--listen', $BindHost, '--port', [string]$Port)
    $process = Start-Process -FilePath $resolvedPython -ArgumentList $arguments -WorkingDirectory $resolvedRoot -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errorFile -PassThru
    @{ pid = $process.Id; root = $resolvedRoot; host = $BindHost; port = $Port; started_at = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding UTF8
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Get-ListenerIds) {
            Show-Status
            exit 0
        }
        if ($process.HasExited) {
            throw "COMFYUI_START_FAILED: inspect $errorFile"
        }
        Start-Sleep -Milliseconds 500
    }
    throw "COMFYUI_START_TIMEOUT: inspect $logFile and $errorFile"
}

if ($Action -eq 'stop') {
    $listeners = Get-ListenerIds
    if (-not $listeners) {
        if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile -Force }
        Show-Status
        exit 0
    }
    $verified = @($listeners | ForEach-Object { Get-VerifiedProcess $_ }) | Where-Object { $_ }
    if ($verified.Count -ne $listeners.Count) {
        throw "COMFYUI_STOP_REFUSED: port listener is not a verified process under $resolvedRoot"
    }
    foreach ($process in $verified) {
        if ($PSCmdlet.ShouldProcess("PID $($process.ProcessId) ($resolvedRoot)", 'Stop ComfyUI')) {
            Stop-Process -Id $process.ProcessId -Force
        }
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Get-ListenerIds)) {
            if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile -Force }
            Show-Status
            exit 0
        }
        Start-Sleep -Milliseconds 250
    }
    throw "COMFYUI_STOP_TIMEOUT: listener remains on $BindHost`:$Port"
}
