param(
    [int]$Port = 8188
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$comfyPython = Join-Path $repoRoot 'ComfyUI\.venv\Scripts\python.exe'
$launcher = Join-Path $repoRoot 'scripts\launch_comfyui.py'
$dtypePatch = Join-Path $repoRoot 'scripts\apply_h3_vae_dtype_patch.py'

if (-not (Test-Path -LiteralPath $comfyPython)) {
    throw "ComfyUI virtual-environment Python was not found at $comfyPython"
}

& $comfyPython $dtypePatch
if ($LASTEXITCODE -ne 0) {
    throw "The MiniMax H3 CPU-VAE dtype patch could not be applied"
}

# The primary GPU is reordered to cuda:0 by launch_comfyui.py. These flags make
# DynamicVRAM keep a conservative free-VRAM margin and aggressively prefer
# ordinary system RAM. CPU VAE prevents the large decode tensors from competing
# with the H3 DiT during sampling. MiniMax's fp16 video VAE also needs an
# explicit fp32 CPU dtype: its CPU linear layers reject float32 activations with
# fp16 weights otherwise.
& $comfyPython $launcher `
    --primary-gpu 'RTX 4090' `
    --port $Port `
    -- `
    --disable-smart-memory `
    --cpu-vae `
    --fp32-vae `
    --vram-headroom 3 `
    --reserve-vram 2 `
    --async-offload 4

exit $LASTEXITCODE
