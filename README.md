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
- `skills/comfyui/` — the default direct route from any brief, plot, script,
  storyboard, or shot list to one ready-to-use H3 workflow and its final video.
- `skills/production-orchestrator/` — the optional approval-gated router for a
  formal planning, compilation, execution, QC, repair, and delivery lifecycle.
- `skills/` — 15 specialist production packages covering request/canon/plot,
  performance/sound/storyboard/previs/preflight, MiniMax H3 and ComfyUI
  compilation, rendering, QC, repair, and post-production.
- `schemas/` and `workflow-catalog/` — shared artifact contracts and typed,
  live-capability-validated ComfyUI API templates.
- `skills/storyboard-director/` — model-neutral feature-film storyboard
  direction, scene geography, typed camera setup/motion, editorial boundaries,
  timelines, continuity, and generation handoffs.
- `.gitignore` — keeps local runtime and production artifacts out of commits.

## AI-agent instruction: create the complete video workflow

When a user asks an AI agent to turn **any** supplied input into a ready H3
video workflow, the default route is `$comfyui`. Input may be a sentence,
brief, plot, script, storyboard, shot list, or optional image/audio/video
references. Do not require a pre-existing project package, approval record,
content hash, production DAG, per-shot API jobs, or manual endpoint approval.
Use `$production-orchestrator` only when the user explicitly requests that
formal lifecycle.

The required deliverable is one ComfyUI UI-format workflow that contains the
whole ordered multi-shot sequence, continues each shot from the previous
shot's final frame, combines the generated video and audio, and saves the final
muxed video. The user must only need to load the workflow and click **Queue
Prompt** once; they must not need to wire nodes, queue individual shots, or
assemble the final video manually.

AI agents must follow this procedure:

1. Read all supplied material and preserve its story, order, characters,
   setting, continuity, and requested runtime. Infer only the production
   details required to make the workflow executable. Ask a question only when
   a missing choice would materially change the user's story.
2. Convert the material into concise, ordered MiniMax H3 prompts with explicit
   durations. Repeat fixed character, wardrobe, environment, lighting, and
   voice anchors in every applicable shot. Start each later shot from the
   exact closing arrangement of its predecessor. Honor supplied timing;
   otherwise choose practical 4–8 second shots and preserve the requested
   total runtime.
3. Write the builder input in this shape:

   ```json
   {
     "shots": [
       {"prompt": "complete H3 shot prompt", "duration_seconds": 6.0}
     ]
   }
   ```

4. Build a new workflow from the verified CORE template:

   ```powershell
   python skills/comfyui/scripts/build_h3_seamless_chain.py `
     --input <shot-specs.json> `
     --output <H3_Seamless_Chain.ui.json> `
     --output-prefix <output-name>
   ```

5. Do not change the machine configuration while creating or repairing the
   workflow. Preserve the intentional RTX 4090/cuda:0 mapping,
   `UnetLoaderGGUFDynamicVRAM`, Q8 FL2VA checkpoint, installed CLIP and VAEs,
   VRAM cap, host-memory offload, 24 fps, resolution, sampler, scheduler, and
   step settings.
6. Before delivery, parse the generated JSON; verify every node, link, prompt,
   duration, protected runtime setting, and output node; confirm no placeholder
   remains; and validate against live ComfyUI `/object_info` when the runtime
   is available. After changes to runtime code or nodes, run a minimal two-shot
   proof before claiming the workflow is ready.
7. Return the workflow path and output prefix. If the user asks the agent to
   execute it, launch ComfyUI with the existing hardware settings, submit the
   workflow once, monitor the queue and logs through completion, and repair
   technical failures directly without adding approval/hash steps.

The generated graph's `SaveVideo` node writes the final muxed MP4 below:

```text
ComfyUI/output/video/<output-prefix>_NNNNN_.mp4
```

The matching audio is retained below:

```text
ComfyUI/output/audio/<output-prefix>_NNNNN.flac
```

ComfyUI assigns the numeric suffix. First-shot previews and recoverable
per-shot clips may also be saved under `ComfyUI/output/video/H3_FIRSTSHOT/`
and `ComfyUI/output/video/H3_SHOTS/`, but those are diagnostics. The MP4 from
the final `SaveVideo` node is the requested finished output and requires no
separate assembly step.

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
`scripts\install_production_skills.ps1`. For the normal one-start workflow,
invoke `$comfyui` and follow the procedure above. `$production-orchestrator`
is an optional formal route: its `PLAN_ONLY` mode writes a Markdown/YAML review
document and stops for approval, while `COMPILE_APPROVED_PLAN` requires the
approved YAML. Do not send a simple ready-workflow request through that formal
route.

The optional formal production-orchestrator architecture enforces independently
generated video segments of at most 10 seconds, but the editorial shot remains
the creative unit. Longer intended
shots retain one shot ID across multiple generation segments. Each join declares
its generation relationship and endpoint policy (`stable_tail`,
`moving_endpoint`, `approved_entry_reference`, or bridge); a stable tail is not
imposed on an editorial cut or on a declared moving endpoint. Editorial cuts,
dissolves, fades, and terminal ends are represented separately in the EDL.

New real-cinematic packages use `planning_model_version: 2` and are validated
with:

```powershell
python scripts\validate_cinematic_package.py --storyboard <storyboard.yaml>
```

The v2 contract requires explicit `scene_time`, `source_time`, and
`record_time`, typed scene geography, structured camera setup/motion, continuity
invariants, bilateral editorial boundaries, and separate generation handoffs.
Historical v1 packages remain readable through the v1 path and are migrated with
an explicit review-blocked report rather than creative fields being invented.

The executed reviewer-corrected development record is [real-cinematic-development-plan-v03.md](examples/cinematic/plan/real-cinematic-development-plan-v03.md); v02 remains the design baseline.

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
