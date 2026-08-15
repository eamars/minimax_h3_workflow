---
name: comfyui-workflow-compiler
description: Compile a ready real-cinematic production-plan revision into typed ComfyUI API workflows and an acyclic production DAG. Use after automated preflight, live ComfyUI capability probing, MiniMax H3 packet compilation, and optional endpoint preparation; no human production gate or plan fingerprint is required.
---

# ComfyUI Workflow Compiler

## Mission

Compile each planned generation segment and utility operation from the workflow catalog into executable API-format JSON, typed job manifests, and a dependency-aware DAG. Stop before execution.

## Ownership boundary

Own template selection, typed bindings, live capability compatibility, graph validation, safe output paths, job envelopes, DAG edges, and compile diagnostics. Preserve story, camera, timing, editorial boundaries, generation handoffs, references, and acceptance criteria.

## Inputs

- Current production-plan artifact and revision IDs.
- H3 prompt packets, reference assets, and optional validated endpoint selections.
- Live `/object_info`, installed-model, and `/system_stats` evidence.
- Workflow catalog, template, mapping, bindings, and output-path policy.

## Required outputs

Write new `compiled/workflows`, `compiled/jobs`, `production-dag.yaml`, and `compile-report.yaml` revisions. Record plan revision, stable IDs, capability evidence, template/mapping revisions, model/node selections, seed, paths, timing, and diagnostic checksums.

## Processing method

1. Validate the plan revision, automated preflight, IDs, assets, and paths.
2. Probe live ComfyUI and treat the live schema as authority.
3. Select only a catalog template matching job type, H3 mode, endpoint policy, timing, audio, nodes, and models.
4. Expand exact placeholders and reject missing, embedded, or unknown bindings.
5. Serialize dynamic-combo selectors in the scalar API shape exposed by live `/object_info`.
6. Validate every node, literal, link, output slot, model, and acyclic graph.
7. Validate target/model/effective timing, the `17k+5` H3 grid, 24 fps, post-trim duration at most 10 seconds, and dimensions divisible by 32.
8. Verify source paths, roles, and optional raw-file integrity checksums.
9. Build jobs for generation, endpoint, extraction, concat, mix, upscale, and export operations.
10. Build only real asset/handoff/post dependencies. Keep editorial mechanisms outside generation topology.
11. Write new revisions atomically and hand off to Render Orchestrator. Never submit `/prompt`.

## Invariants

- Require a current plan revision and live capability evidence, never a human gate or plan fingerprint.
- Preserve planned segment boundaries and creative fields.
- Keep target/effective duration positive and at most 10 seconds.
- Reject unresolved placeholders, unavailable nodes/models, invalid links, cycles, stale schemas, false dependencies, and unsafe paths.
- Use technical checksums only for reproducibility and file integrity.
- Never queue, render, install models, mutate the plan, or overwrite an existing artifact.

## Non-responsibilities

Do not invent prompts, choose creative modes, reinterpret references, change story/camera/timing, prepare endpoints, judge media, repair content, execute jobs, or assemble the master.

## Failure conditions

Return `BLOCKED` with stable IDs and evidence for `PLAN_REVISION_INVALID`, `PREFLIGHT_BLOCKED`, `CAPABILITY_PROBE_MISSING`, `ENVIRONMENT_PROJECTION_INVALID`, `WORKFLOW_TEMPLATE_MISSING`, `WORKFLOW_MAPPING_INVALID`, `WORKFLOW_NODE_UNAVAILABLE`, `WORKFLOW_INPUT_UNSUPPORTED`, `WORKFLOW_LINK_INVALID`, `WORKFLOW_CYCLE`, `REQUIRED_MODEL_MISSING`, `REQUIRED_ASSET_MISSING`, `SEGMENT_TOO_LONG`, `INVALID_FRAME_GRID`, `RESOLUTION_UNSUPPORTED`, `AUDIO_SPEC_UNSUPPORTED`, `HANDOFF_TAIL_INVALID`, `DAG_INVALID`, `ARTIFACT_OVERWRITE_FORBIDDEN`, or `OUTPUT_PATH_UNSAFE`.

## Validation rules

Validate schemas, plan/job revision linkage, live graph shape, model/assets, timing/grid/resolution, safe paths, DAG acyclicity, camera/time traceability, and boundary/handoff separation. Run the bundled probe, compiler, live-graph validator, and contract tests. Validation must never submit `/prompt`.

## Minimal example

For a ready T2VA segment at 8 seconds, compile aligned model frames and an exact 192-frame effective clip into one validated workflow/job with asset dependencies, then stop before queueing.

## Adversarial example

Reject an 11-second segment, unavailable model, dynamic-combo object value, unresolved placeholder, graph cycle, invalid endpoint, stale plan revision, or existing output path. Do not silently substitute values or request human sign-off.

## Acceptance tests

- A current plan revision and live capability profile compile without a sidecar gate.
- Missing node/model/asset, bad binding/link/type/range, invalid timing/grid, unsafe path, and graph cycle fail deterministically.
- Independent jobs have no false edge; continuation and bridge jobs serialize correctly.
- Outputs trace to plan/segment/acceptance revision IDs.
- Compilation performs no queue, download, render, plan mutation, or overwrite calls.

