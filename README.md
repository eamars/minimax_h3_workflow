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
- `.agents/skills/comfyui/` — the direct route from any brief, plot, script,
  storyboard, or shot list to one ready-to-use H3 workflow and its final video.
- `.agents/skills/production-orchestrator/` — the automatic full lifecycle from
  intake and cinematic planning through H3/ComfyUI compilation, rendering,
  continuity QC, repair, assembly, and final QC.
- `.agents/skills/` — 17 project-local skills covering the direct multishot path
  and the complete specialist production workflow.
- `schemas/` and `workflow-catalog/` — shared artifact contracts and typed
  ComfyUI API templates used by the full workflow.
- `.gitignore` — keeps local runtime and production artifacts out of commits.

## AI-agent instruction: create the complete video workflow

When a user asks an AI agent to turn **any** supplied input into a ready H3
video workflow, the default route is `$comfyui`. Input may be a sentence,
brief, plot, script, storyboard, shot list, or optional image/audio/video
references. Do not require a pre-existing project package or a separate review
workflow.

For a direct ready-workflow request, the required deliverable is one ComfyUI UI-format workflow that contains the
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
2. Convert the material into concise, ordered MiniMax H3 action prompts with
   explicit durations. Use 8–12 second generated shots by default. Reserve at
   least two seconds at every later opening for an exact-state airlock and two
   seconds at every ending for a settled landing. Put cuts or camera changes
   inside a shot, after its airlock—not at a generation boundary.
3. Write the builder input in this shape:

   ```json
   {
     "continuity_locks": {
       "style": "fixed style",
       "identity": "fixed subject and wardrobe",
       "environment": "fixed geography and prop layout",
       "lighting": "fixed light sources and exposure"
     },
     "shots": [
       {
         "prompt": "one dominant action and internal camera idea",
         "duration_seconds": 8.0,
         "continuity": {
           "opening_state": "exact opening arrangement",
           "opening_camera": "exact opening camera",
           "opening_audio": "exact opening audio bed",
           "opening_hold_seconds": 0,
           "closing_state": "exact settled closing arrangement",
           "closing_camera": "exact settled closing camera",
           "closing_audio": "exact settled closing audio bed",
           "closing_hold_seconds": 2
         }
       },
       {
         "prompt": "the next dominant action after the airlock",
         "duration_seconds": 8.0,
         "continuity": {
           "opening_state": "copy the previous closing_state verbatim",
           "opening_camera": "copy the previous closing_camera verbatim",
           "opening_audio": "copy the previous closing_audio verbatim",
           "opening_hold_seconds": 2,
           "closing_state": "next settled closing arrangement",
           "closing_camera": "next settled closing camera",
           "closing_audio": "next settled closing audio bed",
           "closing_hold_seconds": 2
         }
       }
     ]
   }
   ```

   The builder rejects phrase-only handoffs, boundary mismatches, missing
   locks, insufficient hold/action budgets, and untimed multi-shot input. A
   workflow is ready only when its manifest reports
   `continuity.status: STRICT_BOUNDARY_VALIDATED`.

4. Build a new workflow from the verified CORE template:

   ```powershell
   python .agents/skills/comfyui/scripts/build_h3_seamless_chain.py `
     --input <shot-specs.json> `
     --output <H3_Seamless_Chain.ui.json> `
     --output-prefix <output-name>
   ```

5. Do not change the machine configuration while creating or repairing the
   workflow. Preserve the intentional RTX 4090/cuda:0 mapping,
   `UnetLoaderGGUFDynamicVRAM`, Q8 FL2VA checkpoint, installed CLIP and VAEs,
   VRAM cap, host-memory offload, 24 fps, resolution, sampler, scheduler, and
   step settings.
6. Before delivery, require strict boundary validation; parse the generated
   JSON; verify every node, link, prompt, duration, exact state/camera/audio
   handoff, repeated lock, protected runtime setting, and output node; confirm
   no placeholder remains; and validate against live ComfyUI `/object_info`
   when the runtime is available. After changes to runtime code or nodes, run a
   minimal two-shot proof before claiming the workflow is ready.
7. Return the workflow path and output prefix. If the user asks the agent to
   execute it, launch ComfyUI with the existing hardware settings, submit the
   workflow once, monitor the queue and logs through completion, and repair
   technical failures directly.

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

## AI-agent instruction: run the full production workflow

Use `$production-orchestrator` when the user asks for the full planning,
generation, QC, repair, editing, and delivery lifecycle. Its default mode is
`FULL_PIPELINE`: it runs every specialist stage automatically and stops only
for a missing creative decision or failed validation that cannot be repaired.
It does not create or require human production gates, sidecar records, or
administrative content fingerprints.

The full route is:

```text
request -> canon -> plot -> performance/sound -> storyboard -> animatic ->
preflight -> H3 packets -> ComfyUI jobs/DAG -> render -> segment/seam QC ->
localized repair -> post edit/audio -> final QC -> delivery
```

Continuous generation handoffs use the MiniMax H3 Multishot design: relay the
predecessor's actual final decoded frame; repeat identity/environment/lighting
descriptions verbatim; hold the exact previous closing arrangement, camera,
and audio for about two seconds at the next opening; finish action/dialogue and
land settled about two seconds before the boundary; never split one spoken line
across shots; and place cuts or reframes inside a shot after the opening hold.
The formal route also verifies state/camera/audio equality and the seam window
before admitting each successor.

## Repository and project layout

This repository is the reusable toolkit, not a container for one production.
Keep shared implementation at the repository root and give every production a
stable project ID with its own private workspace under `projects/`:

```text
.
├── scripts/                    # reusable setup, validation, and toolkit tools
├── .agents/skills/             # 17 project-local Codex skills
├── schemas/                    # full-workflow artifact contracts
├── workflow-catalog/           # typed ComfyUI API templates and mappings
├── tests/                      # direct and full-pipeline tests and fixtures
├── projects/                   # local project workspaces; ignored by Git
│   ├── README.md
│   ├── _template/              # layout guide for a new project
│   └── <project-id>/
│       ├── seeding_material/   # canonical user-supplied seed material
│       ├── inputs/             # source briefs and reference material
│       │   ├── references/
│       │   └── audio/
│       ├── workflows/          # generated UI workflows and manifests
│       ├── renders/            # generated video/audio outputs
│       ├── scripts/             # project-only helpers
│       └── outputs/            # final delivery files
└── ComfyUI/                   # shared local runtime; ignored by Git
```

`<project-id>` must be stable and unique, such as `PRJ01`. Every project
artifact path is relative to that project's directory. Do not put project-specific
plans, seed images, prompts, workflow exports, renders, or run state directly in
the repository root.

Seed images and other user inputs remain the source of truth. Store canonical
seed images under `projects/<project-id>/seeding_material/` and other source
material under `projects/<project-id>/inputs/`. Do not use a shared root
`seeding_material/` directory across projects. A file copied into
`ComfyUI/input/` is only runtime staging; the project copy remains canonical.

Project-only helpers belong in that project's `scripts/` directory. Shared
behavior belongs in root `scripts/`, `.agents/skills/`, `schemas/`, or
`workflow-catalog/`.

To start another project, copy the layout described in `projects/_template/`,
choose a new project ID, place seed inputs under `seeding_material/` and other
source inputs under `inputs/`, and keep all generated artifacts under that
project root.

Codex discovers every project skill directly from `.agents/skills/`. Do not
copy them into a user-global skill directory.

Check that scope with:

```powershell
python scripts\validate_repo_skill_scope.py
```

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
