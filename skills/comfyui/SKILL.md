---
name: comfyui
description: Convert briefs, plots, storyboards, shot lists, and optional media references into ready-to-use ComfyUI workflows; also inspect, validate, automate, and debug image, video, audio, and multimodal graphs. Use for MiniMax H3 multi-shot workflows that must generate and save the final video from one Queue/Start action while preserving the verified local GPU, DynamicVRAM, and offload setup.
---

# ComfyUI workflow design

Use ComfyUI as a typed, executable graph. Treat the prompt, model stack, latent
shape, sampler, decoder, compositor, and output node as one reproducible
artifact. For a requested one-start H3 workflow, interpret the user's source
directly in this skill. Route through storyboard or production-planning skills
only when the user explicitly requests those separate planning artifacts.

## Start with the right operating mode

Choose the smallest graph that satisfies the output contract.

| Need | Graph pattern |
| --- | --- |
| Still image | model/CLIP/VAE loaders -> positive and negative conditioning -> latent -> sampler -> VAE decode -> save |
| Text-to-video | video model and text conditioning -> video latent -> sampler -> video decode -> video save |
| Image-to-video | load or generate a keyframe -> image/video conditioning -> sampler -> decode -> save |
| First/last-frame motion | provide both endpoint images to a model that explicitly supports them; otherwise generate a bridge clip with the model's supported controls |
| Reference-driven video | pass only the references that have a job: identity, style, motion, environment, or audio; bind each reference to the exact tag required by the model |
| Ready-to-click local H3 multi-shot | clone the verified `H3_Seamless_Chain_CORE.json`, inject the complete ordered shot script with the bundled builder, validate the locked runtime, and return one UI-format workflow plus its manifest |
| Formal independently repairable production | generate one shot-sized scene unit per job, export a tail frame and continuity manifest, then assemble reviewed clips |
| Post-production only | load decoded frames or videos, normalize them, trim overlap, concatenate or blend, mux audio, and save; do not invoke a diffusion model merely to edit media |

Prefer built-in nodes. Add a custom-node package only when it supplies a needed
model, control signal, video I/O operation, or deterministic utility. Record the
package name, repository, commit/version, and why it is required.

## Build a workflow

### 1. Freeze the output contract

Write down these values before placing nodes:

- output type, aspect ratio, width, height, FPS, duration, audio sample rate,
  codec/container, and output path;
- model family and task mode (T2V, I2V, first/last frame, reference, or edit);
- fixed style/identity anchors and allowed scene-specific changes;
- seed policy: fixed for diagnosis and comparison, varied only after the graph
  is proven;
- acceptance checks: subject identity, motion, continuity, audio sync, and
  transition behavior.

For generated video, make one clip carry one dominant action and one camera
idea. Split a second action into another shot unless the selected model's
temporal prompt format has been tested for that behavior.

### 2. Inspect the local runtime

Before prescribing node names or widget values, inspect the actual installation.

1. Find the ComfyUI root and read its version, local README, custom-node list,
   model directories, and existing workflows.
2. Start the server on a local port and query `/system_stats`, `/features`, and
   `/object_info`. Use the live node schema as the authority for inputs and
   widget order; exported graphs and custom nodes can change between versions.
3. Prefer the UI's `Workflow -> Browse Workflow Templates` for a known-good
   starting graph. Load a JSON or workflow image, install missing custom nodes
   through Manager when appropriate, and restart after installation.
4. Keep model files and runtime caches outside version control. Version the
   small workflow JSON, scripts, prompts, manifests, and checksums instead.

### 3. Lay out the graph as blocks

Organize the canvas left to right and group nodes by responsibility:

`Inputs -> Model/Conditioning -> Latent -> Sampling -> Decode -> Compose -> Save`

Use clear node titles and notes for model names, dimensions, frame math, and
external dependencies. Keep one source of truth for each control value; connect
width, height, length, FPS, seed, and prompt inputs rather than duplicating
untracked literals. Connect only compatible socket types. A link is part of the
program, not decoration.

For every branch, answer:

- What data enters the branch?
- What changes, and at what representation: image, video frames, latent,
  conditioning, or audio?
- Which node proves the branch ran?
- Where is its output saved so it can become a later scene's input?

### 4. Make the graph reproducible

Pin or record the model filenames, VAE, text encoder, LoRAs, custom-node
versions, sampler, scheduler, steps, CFG/guider settings, resolution, FPS,
frame count, seed, and output prefix. Save both:

- the UI-format workflow for a human to reopen and edit;
- the API-format workflow for automation, generated by ComfyUI's `Save (API
  Format)` command or a version-aware converter.

Do not hand-edit API widget positions based on guesswork. Resolve live inputs
from `/object_info`, then submit the prompt graph. A scalar accidentally placed
in an `IMAGE`, `VIDEO`, `LATENT`, or `AUDIO` input is a common cause of opaque
runtime errors.

When a script derives a workflow from a template, keep the template as the
source of truth: load it, mutate named nodes and connections, recalculate node
and link identifiers, and write the UI workflow, API workflow, and manifest
together. Validate that every link endpoint and required node type still
exists. Stage reference assets idempotently and refuse to overwrite an existing
asset whose contents differ from the requested source.

## Build a one-start local H3 multi-shot workflow

Use this as the default route whenever the user asks for a ready workflow or a
final multi-shot video. Accept any useful source: a sentence, brief, plot,
script, storyboard, shot list, or optional image/audio/video references. Do not
require a pre-existing project package.

This route has no planning approval, approval hash, production DAG, per-shot API
job bundle, QC bureaucracy, or manual endpoint gate. Do not invoke those systems
unless the user explicitly asks for that production lifecycle. The normal
deliverable is one UI-format workflow that runs every shot sequentially and
saves the final muxed video after one Queue Prompt action.

1. Read every supplied input. Infer only missing production details needed to
   make it executable: ordered shots, duration, camera, action, sound, opening
   and closing state, and continuity. Ask the user only when a missing choice
   would materially change their story.
2. Compile a concise H3 prompt for every generated shot. Repeat fixed identity,
   wardrobe, environment, lighting, and voice anchors verbatim. Begin each shot
   from its predecessor's exact closing arrangement and end it in a usable
   handoff state.
3. Assign every shot an explicit duration. Honor supplied timing. Otherwise
   choose practical 4–8 second shots and preserve the requested total runtime.
   Split any generated shot whose aligned H3 length would exceed the verified
   362-frame maximum.
4. Write one temporary authoring input in this exact shape:

   ```json
   {
     "shots": [
       {"prompt": "complete H3 shot prompt", "duration_seconds": 6.0}
     ]
   }
   ```

5. Build from the verified local template only:

   ```powershell
   python skills/comfyui/scripts/build_h3_seamless_chain.py `
     --input <shot-specs.json> `
     --output <H3_Seamless_Chain.ui.json> `
     --output-prefix <output-name>
   ```

   The builder embeds the script and exact timing into one
   `H3MultishotSampler`. The node generates each shot on the H3 `17k+5` model
   grid, trims decoded video/audio to its declared duration, relays the final
   frame into the next shot, removes the duplicated boundary frame, and returns
   one exact-length master to `SaveVideo`.
6. Preserve the local runtime without negotiation: RTX 4090, cuda:0 mapping,
   `UnetLoaderGGUFDynamicVRAM`, Q8 FL2VA checkpoint, installed CLIP and VAEs,
   VRAM cap, host-memory offload, 24 fps, resolution, sampler, scheduler, and
   step settings. Never solve a workflow error by changing this hardware or
   memory configuration.
7. Keep `shot_count: 0`, per-shot seeds, first-shot preview, and per-shot saves.
   Use `chain_gain_control: flatten` for chains longer than five shots. Patch
   both `widgets_values` and `properties.h3_widget_values` so the UI cannot
   restore stale values over the generated script.
8. Validate before delivery: parse the UI JSON, verify every node/link and
   output node, confirm no placeholder remains, confirm prompt count and summed
   duration, confirm the protected runtime fingerprint, load against live
   `/object_info`, and run a minimal two-shot proof after runtime changes.

Return the workflow path and the final output prefix. The user should only need
to load the workflow and click Queue Prompt. If execution is requested, monitor
the queue and logs, use the first-shot preview to catch a bad route early, and
repair technical failures directly without asking the user to operate nodes or
repeat approval steps.

### 5. Run a small proof first

Queue a low-resolution, short-duration, low-step render with a fixed seed. Check
the console and node error state before spending GPU hours. Then increase one
variable at a time. Record the successful settings beside the workflow.

Use the UI for exploration: Queue/Run, History, node previews, and workflow
save. Use the local API for repeatable batches: `POST /prompt`, capture the
returned `prompt_id`, monitor `/ws` or poll `/history/{prompt_id}`, and collect
the output filenames. See [api-and-debugging.md](references/api-and-debugging.md)
for the request contract and failure checks.

## MiniMax H3 adaptation

When H3 nodes are available, use the installed node schema, model files, and
workflow templates as the version-specific authority. Common patterns may
include:

- `MiniMaxH3ImageToVideo`: prompt plus optional `first_frame` and `last_frame`
  keyframes, returning conditioning and a packed video+audio latent;
- `MiniMaxH3ReferenceToVideo`: reference images, videos, and audio with prompt
  tags such as `<Picture 1>`, `<Video 1>`, and `<Audio 1>` in connection order;
- `MiniMaxH3SigmaShift`: model patch for the video/audio flow shifts;
- `VAEDecode` plus `VAEDecodeAudio`, followed by `CreateVideo` for synchronized
  video and native audio output.

Keep the H3 graph internally consistent:

- Use the same task family and matching model weights. Do not substitute
  reference-to-video weights into a first/last-frame graph without checking the
  model card and node implementation.
- Derive the valid frame grid, FPS, spatial multiples, aspect-ratio limits, and
  native resolution policy from the live node schema or model documentation.
  Never assume that a duration in seconds maps to the exact requested frame
  count. Record both the model-aligned generation length and the effective
  output length.
- When exact output timing is required, calculate the target video frame count
  from the authoritative FPS, generate an aligned length that is accepted by
  the model, then trim decoded video frames and audio separately before the
  final video/audio mux. Validate the resulting frame count, duration, and
  audio sample rate rather than trusting the nominal duration widget.
- Keep video and audio VAEs paired with the H3 model. Treat a requested duration
  as approximate until the valid frame count is calculated.
- For references, use exact ordinals and describe which reference controls which
  attribute. Do not attach a reference just because the node has an empty slot.
- Discover available compute devices from the runtime and live selector options.
  Route model, text encoder, and VAE components only through supported device
  controls; do not assume a particular GPU ordinal. If an explicit device
  route can silently fall back to another device, add a tested fail-closed
  check or surface the fallback in validation output. Record the device mapping
  used for the render and the launcher/environment assumptions that created it.
- Treat reference staging, device routing, temporal alignment, trimming, and
  muxing as part of the workflow contract. Preserve those steps in the graph or
  builder and document their acceptance checks; do not hide them in an
  undocumented manual workaround.

The repository's `scripts/comfy_api_runner.py` can be used as a local runner
when its assumptions match the installed node schema. Inspect or adapt it rather
than silently bypassing live `/object_info` validation.

## Join storyboard scenes without a visible seam

Do not begin with a blind file concatenation. Start with the desired transition
semantics, then choose one of the patterns in
[video-stitching.md](references/video-stitching.md).

The default chain is:

`approved tail frame of S01 -> first-frame continuation for S02 -> approve S02 -> repeat`

For a substantive transition, generate a short bridge clip whose first frame is
the final stable frame of the prior scene and whose last frame is the planned
entry keyframe of the next scene. Trim duplicate endpoint frames before joining.
If the model cannot constrain both endpoints, use an image-to-video continuation
from the prior tail and apply an editorial cut, dissolve, or optical-flow/frame
interpolation only when it matches the story. A crossfade hides a hard cut but
does not repair identity, geometry, lighting, or motion discontinuity.

For every handoff, keep:

- source scene ID and exact tail-frame filename/index;
- next scene ID and first-frame filename/index;
- target endpoint, if any;
- overlap/bridge frame count, FPS, resolution, and color/audio settings;
- continuity state: character pose, gaze, screen direction, camera vector,
  prop state, lighting, environment, and audio beat;
- whether the seam is `continue`, `bridge`, `cut`, `dissolve`, or `match_cut`.

Normalize every clip before assembly. Match dimensions, FPS, frame order,
pixel format, color treatment, and audio sample rate. Use `ImageFromBatch` or a
video loader to select tail/head windows, `ImageBatch`/`Batch Images` to stack
frames, `CreateVideo` or `VHS_VideoCombine` to encode, and `SaveVideo` to write
the final artifact. Keep the original scene clips and bridge clips so the edit
can be revised without regenerating everything.

## Validate and troubleshoot

Run these checks in order:

1. **Graph validity:** no red/missing nodes; all links have compatible types;
   all required model files appear in the live dropdown or `/object_info`.
2. **Runtime validity:** `/prompt` returns a `prompt_id`; node errors are empty;
   `/history/{prompt_id}` reaches success; output files exist and are readable.
3. **Media validity:** dimensions, FPS, frame count, duration, audio channels,
   sample rate, and codec match the contract.
4. **Continuity validity:** compare each scene's tail against the next head;
   inspect a few frames before and after every seam; verify screen direction,
   subject state, lighting, and audio beat.
5. **Provenance validity:** save the exact prompt, workflow JSON, seed, model
   names, custom-node versions, and output paths.

Use this failure map:

- Missing red node: update ComfyUI or install the named custom-node package,
  then restart and reload the graph.
- Missing model: fix the model directory or filename; do not substitute a
  similarly named checkpoint without checking architecture and VAE compatibility.
- Out of memory: reduce resolution, frame count, batch size, or quantization
  first; then use the runtime's supported offload/low-VRAM options.
- Invalid frame length: calculate the model's temporal grid instead of rounding
  a requested seconds value by intuition.
- API `int`/`float` in a tensor slot: regenerate API format from the live UI or
  schema and re-run the converter; never shift widgets by hand.
- Hiccup at a seam: remove duplicate endpoint frames, confirm equal FPS, then
  try a generated bridge or shorter overlap. Do not add interpolation before
  checking the actual frame sequence.
- Audio drift: use one authoritative FPS and sample rate, trim audio explicitly,
  and mux only after the video frame count is final.

## Handoff checklist

Return a compact package containing the chosen graph pattern, assumptions,
required models/nodes, UI/API workflow paths, prompt/control fields, run command,
small-proof result, output location, and known limitations. For a storyboard
project, include the scene ID and the exported tail frame/manifest needed by the
next scene.
