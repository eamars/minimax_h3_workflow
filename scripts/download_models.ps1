# Download the quantized MiniMax H3 stack into ComfyUI\models (Step 3).
# Usage:
#   .\scripts\download_models.ps1                      # Q8_CR (higher VRAM profile)
#   .\scripts\download_models.ps1 -Quant U16G          # lower-VRAM profile
#   .\scripts\download_models.ps1 -Quant Q4_0          # lowest VRAM
# Downloads use huggingface_hub's Python API (huggingface-cli is deprecated
# and no longer works with huggingface-hub >= 1.0).
param(
    [ValidateSet('Q8_CR', 'U16G', 'Q4_0')]
    [string]$Quant = 'Q8_CR',
    [string]$ComfyDir = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'ComfyUI')
)
$ErrorActionPreference = 'Stop'

$Python = Join-Path $ComfyDir '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) { throw "venv python not found at $Python - run scripts\setup_comfyui.ps1 first" }

$Runner = Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts\download_models_hf.py'
$Arg = if ($Quant -eq 'Q8_CR') { $null } else { "--only $Quant" }

if ($Arg) {
    & $Python $Runner --only $Quant --comfy-dir $ComfyDir
} else {
    & $Python $Runner --comfy-dir $ComfyDir
}
if ($LASTEXITCODE -ne 0) { throw "download_models_hf.py exited with code $LASTEXITCODE" }

Write-Host ""
Write-Host "Model layout:"
Get-ChildItem -Path (Join-Path $ComfyDir 'models') -Recurse -File | Where-Object { $_.Length -gt 1MB } | ForEach-Object {
    "{0,8:N2} GB  {1}" -f ($_.Length / 1GB), $_.FullName
}
Write-Host ""
Write-Host "Optional R2V (reference-to-video) model:"
Write-Host "  .\.venv\Scripts\python.exe ..\scripts\download_models_hf.py (add an R2V entry)"
