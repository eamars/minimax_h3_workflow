---
name: comfyui-workflow-compiler
description: Compile an approved real-cinematic AI-video production plan into immutable, typed ComfyUI API-format workflow jobs and an acyclic production DAG while preserving editorial shots, typed camera paths, three time domains, and generation handoff policies. Use after plan approval, live ComfyUI capability probing, MiniMax H3 prompt compilation, and optional endpoint handoff preparation.
---

# ComfyUI Workflow Compiler

## Mission

Compile each approved generation segment and utility operation from the versioned workflow catalog into ComfyUI API-format JSON, typed job manifests, checksums, and a dependency-aware DAG. Stop before execution; the Render Orchestrator alone may queue a compiled job.

## Ownership boundary

Own template selection, typed binding, live capability compatibility, graph validation, deterministic compiled paths, job envelopes, DAG edges, and compile diagnostics. Preserve plan-owned plot, performance, editorial shot/camera setup/motion, duration/segment boundaries, three time domains, editorial boundary semantics, generation handoff policies, reference roles, and acceptance criteria. Treat live `/object_info`, installed model listings, and the frozen catalog revision as authority.

## Inputs

- Approved `production-plan` YAML plus `approval-record`; require exact plan content hash equality and both statuses `approved`.
- H3 prompt-packet manifest, canon/reference asset manifest, and optional approved handoff-frame selection/keyframe report.
- Frozen capability profile containing live `/object_info`, `/models/{folder}`, `/system_stats`, probe timestamp, endpoint, and profile hash.
- Versioned workflow catalog entry, template JSON, mapping YAML, catalog hash, output-path policy, and existing artifact manifest.

## Required outputs

Write only new revisioned files under `compiled/`: `approved-plan-link.yaml`, capability-profile link, prompt-packet link, `workflows/<job-id>.json`, `jobs/<job-id>.yaml`, `production-dag.yaml`, `compile-report.yaml`, and `checksums.yaml`. Every workflow/job records plan ID/version/hash, source hashes, template/mapping/catalog revisions, capability-profile hash, node/model evidence, seed, deterministic paths, stable segment/job IDs, and status. Return `PASS` or `BLOCKED`; when blocked, emit no executable workflow.

## Processing method

1. Validate approval, exact plan hash, provenance, preflight, stable IDs, assets, and immutability.
2. Probe and freeze live `/object_info`, `/models`, and `/system_stats`; never infer capability from a UI export or stale profile.
3. Select a catalog template only when job type, H3 mode, generation relationship/endpoint policy, duration, resolution, audio, node, and model declarations match; editorial cut/dissolve/fade mechanisms stay in post.
4. Expand only declared exact `${name}` placeholders. Reject embedded/unbound/unknown bindings, unsafe paths, and live-schema type/range/enum violations. Expand R2VA autogrow inputs only from live object-info order.
5. For every live `COMFY_DYNAMICCOMBO_V3` input, serialize the selected option as the scalar selector required by the live `/prompt` API (for example `codec: auto`); reject the UI-shaped nested object form. Expand selected nested fields only as the live dotted input names declare, then perform the validator's executor-shape round-trip check.
6. Validate every API node, input, literal, link and output slot against the live schema. Require output nodes and an acyclic graph by topological sort.
7. Validate target/model/effective timing separately. Target/effective are positive and at most 10 seconds. For H3, use 24 fps, the `17k+5` model grid, post-trim effective frames, dimensions divisible by 32, and live audio/resolution limits.
8. Verify every source asset path, hash, role, and plan linkage. Reject existing approved output paths before creating any job.
9. Emit job envelopes for keyframe, video segment, bridge, frame extract, concat, audio mix, upscale, and final export work.
10. Build a DAG with evidenced asset, approval, generation-handoff, and post edges. `independent` jobs have no false dependency; `same_shot_continue` follows its declared endpoint policy; `endpoint_bridge` waits for both endpoints; editorial cuts/dissolves/fades are post-only.
11. Write atomically to new revisioned paths, calculate checksums, and hand off to Render Orchestrator. Never POST `/prompt`.
12. When an environment profile is supplied, validate every prompt-bearing node against the hard projection before writing the executable graph: require the profile ID, positive locked landmarks, boundary/unknown-space language, and negated-only forbidden architecture.

## Invariants

- Exact approved plan hash and live capability evidence are mandatory.
- Effective duration never exceeds 10 seconds and approved segment boundaries never change here.
- Positional widget indices, unknown nodes/models, stale object-info, unresolved placeholders, dangling links, cycles, and false dependencies are forbidden.
- Generation handoffs require their declared endpoint policy; stable-tail and bridge policies gate endpoints, while moving-endpoint and approved-entry-reference policies preserve their evidence without fabricating a stable tail.
- Approved artifacts are immutable; replacement uses a new revision and `supersedes`.
- No queue, render, download/install, plan mutation, or overwrite side effect.
- Environment profile ID and prompt projection are immutable compilation inputs; missing or positive forbidden-feature language blocks the executable graph.

## Non-responsibilities

Do not author prompts creatively, choose H3 modes, redesign references, change story/camera/performance, split editorial shots or segments, alter boundaries/handoff policies, approve plans, judge quality, select repairs, execute jobs, or assemble media. Report unsupported capability instead of substituting a template or model.

## Failure conditions

Return `BLOCKED` with stable IDs, evidence, owner, and invalidation scope using only: `PLAN_APPROVAL_REQUIRED`, `PLAN_HASH_MISMATCH`, `PREFLIGHT_BLOCKED`, `CAPABILITY_PROBE_MISSING`, `ENVIRONMENT_PROJECTION_INVALID`, `WORKFLOW_TEMPLATE_MISSING`, `WORKFLOW_MAPPING_INVALID`, `WORKFLOW_NODE_UNAVAILABLE`, `WORKFLOW_INPUT_UNSUPPORTED`, `WORKFLOW_LINK_INVALID`, `WORKFLOW_CYCLE`, `REQUIRED_MODEL_MISSING`, `REQUIRED_ASSET_MISSING`, `SEGMENT_TOO_LONG`, `INVALID_FRAME_GRID`, `RESOLUTION_UNSUPPORTED`, `AUDIO_SPEC_UNSUPPORTED`, `HANDOFF_TAIL_UNAPPROVED`, `DAG_INVALID`, `APPROVED_ARTIFACT_OVERWRITE_FORBIDDEN`, or `OUTPUT_PATH_UNSAFE`.

## Validation rules

Validate the local contract and every consumed schema. Hash canonical UTF-8 sorted-key YAML/JSON without timestamps. Compare every template class/input to live object-info; validate literals, links, outputs, model/assets, duration/grid/resolution, paths, DAG acyclicity, editorial-boundary versus generation-handoff separation, camera/time traceability, plan/job traceability, and immutability. For dynamic-combo inputs, test both the accepted scalar selector and the rejected UI-shaped object against the live schema, and require a final pre-submit validator pass over every compiled graph. Run `scripts/probe_comfyui.py`, the approval-gated `scripts/compile_workflow.py`, `scripts/validate_live_graph.py`, and contract tests before handoff; validation must never POST `/prompt`.

## Minimal example

For an approved T2VA segment at 8 seconds, 1344×768, 24 fps, compile 209 model frames and 192 post-trim effective frames into `JOB_SEQ01_SC01_SH01_SEG01_R01`. Emit a validated workflow and one DAG job with only asset and approval edges; do not queue it.

## Adversarial example

If a template supplies `quality` to `CreateVideo` or `SaveVideo` while live object-info exposes `bit_depth` and `codec`, return `WORKFLOW_INPUT_UNSUPPORTED`. If live object-info exposes a `COMFY_DYNAMICCOMBO_V3` selector such as `codec` and a graph emits `{codec: {codec: auto}}` instead of `codec: auto`, return `WORKFLOW_INPUT_UNSUPPORTED` before writing the executable workflow. Also block an 11-second segment, unapproved continuation tail, absent GGUF model, graph cycle, stale plan hash, unresolved placeholder, or existing approved output; never silently repair it.

## Acceptance tests

- Missing approval/hash/live capability blocks before writes.
- Missing node/model/asset, bad binding, stale input, wrong type/range/enum, dangling or mismatched link, output-slot error, and cycle fail deterministically.
- Zero or over-cap target/effective duration and invalid H3 grid/resolution/audio fail; grid-aligned model duration may exceed 10 only with a recorded effective trim at or below 10.
- Independent cuts have no false edges; continuation and bridge dependencies are serialized correctly; dissolve stays post-only.
- Outputs trace to plan hash, segment and acceptance IDs with deterministic checksums and immutable revisions.
- Tests assert zero `/prompt`, download, render, plan mutation, and overwrite calls.
