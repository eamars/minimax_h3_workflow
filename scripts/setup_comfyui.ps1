# MiniMax H3 + ComfyUI local setup (PowerShell 5.1+)
# Installs ComfyUI into this workspace, creates a venv with CUDA 12.8
# (Blackwell/RTX 5090 compatible) wheels, and clones the custom nodes
# needed for the GGUF path. Idempotent: existing folders are reused.
$ErrorActionPreference = 'Stop'

$Root   = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Comfy  = Join-Path $Root 'ComfyUI'
$Venv   = Join-Path $Comfy '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'

if (-not (Test-Path $Comfy)) {
    Write-Host "[1/5] Cloning ComfyUI..."
    git clone https://github.com/Comfy-Org/ComfyUI.git $Comfy
} else {
    Write-Host "[1/5] ComfyUI already exists at $Comfy - skipping clone."
}

if (-not (Test-Path $Python)) {
    Write-Host "[2/5] Creating venv (py -3.12)..."
    py -3.12 -m venv $Venv
} else {
    Write-Host "[2/5] venv already exists - skipping."
}

Write-Host "[3/5] Installing torch (cu128) + ComfyUI requirements..."
& $Python -m pip install --upgrade pip wheel
& $Python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
& $Python -m pip install -r (Join-Path $Comfy 'requirements.txt')

Write-Host "[4/5] Cloning custom nodes..."
$NodesDir = Join-Path $Comfy 'custom_nodes'
New-Item -ItemType Directory -Force -Path $NodesDir | Out-Null
$Repos = [ordered]@{
    'ComfyUI-GGUF'         = 'https://github.com/molbal/ComfyUI-GGUF.git'
    'ComfyUI-Manager'      = 'https://github.com/ltdrdata/ComfyUI-Manager.git'
    'ComfyUI-KJNodes'      = 'https://github.com/kijai/ComfyUI-KJNodes.git'
    'ComfyUI-H3-Multishot' = 'https://github.com/jlucasmcrell/ComfyUI-H3-Multishot.git'
}
foreach ($name in $Repos.Keys) {
    $target = Join-Path $NodesDir $name
    if (-not (Test-Path $target)) {
        git clone $Repos[$name] $target
    } else {
        Write-Host "  $name already present - skipping."
    }
}

Write-Host "[5/5] Installing GGUF dependency..."
& $Python -m pip install --upgrade gguf

Write-Host ""
Write-Host "Setup complete. Launch with:"
Write-Host "  cd $Comfy"
Write-Host "  python ..\scripts\launch_comfyui.py      # both GPUs visible; 4090 = cuda:0"
Write-Host "  # manual: python main.py --listen 127.0.0.1 --port 8188 --cuda-device 0,1"
