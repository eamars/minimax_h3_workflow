param(
    [int]$Port = 8188
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$comfyPython = Join-Path $repoRoot 'ComfyUI\.venv\Scripts\python.exe'
$launcher = Join-Path $repoRoot 'scripts\launch_comfyui.py'
$dtypePatch = Join-Path $repoRoot 'scripts\apply_h3_vae_dtype_patch.py'
$logDirectory = Join-Path $repoRoot 'logs'
$stdoutPath = Join-Path $logDirectory 'comfyui_takeover.stdout.log'
$stderrPath = Join-Path $logDirectory 'comfyui_takeover.stderr.log'

if (-not (Test-Path -LiteralPath $comfyPython)) {
    throw "ComfyUI virtual-environment Python was not found at $comfyPython"
}

& $comfyPython $dtypePatch
if ($LASTEXITCODE -ne 0) {
    throw "The MiniMax H3 CPU-VAE dtype patch could not be applied"
}

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

$comfyArguments = @(
    ('"' + $launcher + '"'),
    '--primary-gpu', '"RTX 4090"',
    '--port', $Port.ToString(),
    '--',
    '--disable-smart-memory',
    '--cpu-vae',
    '--fp32-vae',
    '--vram-headroom', '3',
    '--reserve-vram', '2',
    '--async-offload', '4'
) -join ' '

$process = Start-Process -FilePath $comfyPython `
    -ArgumentList $comfyArguments `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -UseBasicParsing `
            -Uri "http://127.0.0.1:$Port/system_stats" -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # ComfyUI is still loading custom nodes.
    }
}

if (-not $ready) {
    Get-Content -LiteralPath $stdoutPath -Tail 60 -ErrorAction SilentlyContinue
    Get-Content -LiteralPath $stderrPath -Tail 60 -ErrorAction SilentlyContinue
    throw "ComfyUI did not become ready on port $Port (launcher PID $($process.Id))"
}

Write-Output "ComfyUI detached and ready on port $Port (launcher PID $($process.Id))"
Write-Output "stdout: $stdoutPath"
Write-Output "stderr: $stderrPath"
