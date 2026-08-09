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
- `skills/production-orchestrator/` — the invokable approval-gated router for
  the complete planning, compilation, execution, QC, repair, and delivery
  lifecycle.
- `skills/` — 15 specialist production packages covering request/canon/plot,
  performance/sound/storyboard/previs/preflight, MiniMax H3 and ComfyUI
  compilation, rendering, QC, repair, and post-production.
- `schemas/` and `workflow-catalog/` — shared artifact contracts and typed,
  live-capability-validated ComfyUI API templates.
- `skills/comfyui/` — generic ComfyUI workflow design and validation guidance.
- `skills/storyboard-director/` — model-neutral storyboard direction, blocking,
  camera/edit intent, timelines, continuity, and handoffs.
- `.gitignore` — keeps local runtime and production artifacts out of commits.

## Repository and project layout

This repository is the reusable toolkit, not a container for one production.
Keep shared implementation at the repository root and give every production a
stable project ID with its own private workspace under `projects/`:

```text
.
├── scripts/                    # reusable setup, validation, and toolkit tools
├── skills/                     # reusable Codex skills
├── schemas/                    # shared artifact contracts
├── workflow-catalog/           # shared ComfyUI templates and mappings
├── tests/                      # toolkit and non-rendering contract tests
├── examples/                   # sanitized public examples and test fixtures
│   └── general-idea/plan/      # generic PRJ99 review-pair fixture
├── projects/                   # local project workspaces; ignored by Git
│   ├── README.md
│   ├── _template/              # layout guide for a new project
│   └── <project-id>/
│       ├── seeding_material/   # canonical user-supplied seed material
│       ├── inputs/             # other project source material
│       │   ├── references/
│       │   └── audio/
│       ├── plan/               # review plan and approval record
│       ├── compiled/           # prompt packets, jobs, workflows, DAGs
│       ├── orchestrator/       # project state and execution runs
│       ├── scripts/             # project-specific adapters and repairs
│       ├── workflows/          # project-local UI exports/snapshots
│       ├── storyboards/        # project-local storyboard exports
│       ├── frames/             # keyframes and extracted endpoints
│       ├── renders/            # generated segments and masters
│       ├── bridges/            # generated bridge media
│       ├── edit/               # EDL, assembly, and mix plans
│       ├── prompts/            # project-local prompt drafts
│       ├── manifests/          # delivery and provenance manifests
│       ├── audio/              # project-local audio artifacts
│       ├── logs/               # project execution logs
│       └── outputs/            # other project-generated outputs
└── ComfyUI/                   # shared local runtime; ignored by Git
```

`<project-id>` must be stable and unique, such as `PRJ01`. Every project
artifact path is relative to that project's directory; project manifests and
state must retain the project ID, artifact version, upstream references, and
content hashes. Do not put project-specific plans, seed images, prompts,
workflow exports, renders, or run state directly in the repository root.

Seed images and other user inputs remain the source of truth. Store canonical
seed images under `projects/<project-id>/seeding_material/` and other source
material under `projects/<project-id>/inputs/`. Do not use a shared root
`seeding_material/` directory across projects. A file copied into
`ComfyUI/input/` is only runtime staging; the project copy remains canonical.

Project-only compiler, repair, and execution scripts belong in that project's
`scripts/` directory. Shared behavior belongs in the root `scripts/`,
`skills/`, `schemas/`, or `workflow-catalog/` directories. The current local
PRJ01 workspace follows this split; older or unassigned material is kept under
`projects/_archive/` until it is assigned a project ID.

To start another project, copy the layout described in `projects/_template/`,
choose a new project ID, place seed inputs under `seeding_material/` and other
source inputs under `inputs/`, and keep all generated artifacts under that
project root. Add sanitized reusable examples under `examples/`, not under a
real project workspace.

Install or refresh the complete local skill set with
`scripts\install_production_skills.ps1`, then invoke
`$production-orchestrator` after the skill registry refreshes. The default
`PLAN_ONLY` mode writes the full Markdown/YAML review document and stops for
approval; `COMPILE_APPROVED_PLAN` compiles the matching ComfyUI workflow bundle
only after the exact YAML hash is approved.

The architecture enforces independently generated video segments of at most 10
seconds. Longer intended shots are represented as dependency chains: each
continuation waits for QC and an approved stable tail frame, reuses that exact
frame as the next ComfyUI job's first frame, and trims duplicate endpoints
before final assembly.

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
