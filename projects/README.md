# Project workspaces

Each production gets one private directory named with a stable project ID:

```text
projects/<project-id>/
├── seeding_material/ # immutable canonical seed images and references
├── inputs/          # other immutable user-provided source material
├── plan/            # plan and approval artifacts
├── compiled/        # compiled prompts, jobs, workflows, and DAGs
├── orchestrator/    # project state and execution runs
├── scripts/         # project-specific code only
├── workflows/       # project-local UI exports or snapshots
├── storyboards/     # project-local storyboard exports
├── frames/          # keyframes and extracted endpoints
├── renders/         # generated media and masters
├── bridges/         # generated bridge media
├── edit/            # edit, assembly, and audio-mix plans
├── prompts/         # project-local prompt drafts
├── manifests/       # delivery and provenance manifests
├── audio/           # project-local audio artifacts
├── logs/            # execution logs
└── outputs/         # other generated outputs
```

The repository's root `scripts/`, `skills/`, `schemas/`, and
`workflow-catalog/` directories are shared toolkit code. Project directories
are ignored by default; sanitized fixtures belong under `examples/`.

Copy `_template/` to create a new project workspace, then replace the
placeholder with a unique ID such as `PRJ02`.
