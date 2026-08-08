# MiniMax H3 ComfyUI toolkit

This public repository contains reusable setup, automation, debugging, and
Codex skill guidance for MiniMax H3 workflows in ComfyUI.

Local production material is intentionally excluded from version control. Keep
project-specific workflow JSON, prompts, storyboards, reference images, model
files, renders, logs, and machine-specific launch wrappers in a private local
workspace.

## Public contents

- `scripts/` — reusable ComfyUI setup, model-download, API, launcher, and H3
  compatibility utilities.
- `skills/comfyui/` — generic ComfyUI workflow design and validation guidance.
- `skills/storyboard/` — generic story, shot, prompt, continuity, and handoff
  planning guidance.
- `.gitignore` — keeps local runtime and production artifacts out of commits.

## Local setup

The setup script installs ComfyUI and the required dependencies into a local
`ComfyUI/` checkout, which is ignored by Git:

```powershell
.\scripts\setup_comfyui.ps1
```

Download model files into the local ComfyUI installation with the model
download script. Choose a quantization profile appropriate for the available
VRAM:

```powershell
.\scripts\download_models.ps1
.\scripts\download_models.ps1 -Quant U16G
```

Launch ComfyUI using the first detected GPU, or select a device by name:

```powershell
python scripts\launch_comfyui.py --single-gpu
python scripts\launch_comfyui.py --primary-gpu "GPU name" --single-gpu
```

Use `--print-devices` to inspect the runtime’s CUDA ordering before selecting a
device. Pass additional ComfyUI flags after `--`.

## Repository policy

Commit reusable code and generic documentation only. Do not add local
production artifacts, personal paths, private prompts, reference packs,
generated media, model weights, runtime logs, or machine-specific settings.
