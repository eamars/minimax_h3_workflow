---
name: production-orchestrator
description: Plan and coordinate approval-gated AI video production across specialist skills, MiniMax H3 prompt compilation, ComfyUI workflow jobs, segmented rendering, continuity QC, repair, and final assembly. Use for multi-shot or longer-than-10-second video requests, production-plan routing, deterministic ComfyUI handoffs, approved-tail continuation chains, bridge/cut/match-cut/dissolve decisions, or versioned artifact and approval management.
---

# Production Orchestrator

Coordinate the local AI-video production lifecycle as a thin, stateful router. Preserve each specialist's decision authority, stop at human review by default, and never silently change creative intent to satisfy a downstream workflow.

## Mission

Turn a user brief and seed-asset set into a traceable production plan, then—only after explicit approval—route validated MiniMax H3 and ComfyUI compilation, execution, QC, repair, and assembly stages.

## Ownership boundary

Own lifecycle mode selection, dispatch order, artifact-envelope validation, project state, approval/hash gates, invalidation scope, and dependency scheduling. Delegate narrative, canon, scene, sound, camera, prompt syntax, workflow graph, rendering, QC, repair, and editorial decisions to their named specialist packages.

Read the directly linked [specialist registry](references/specialist-registry.yaml), [routing policy](references/routing-policy.yaml), and [state machine](references/state-machine.yaml) before dispatching. Load every dispatched specialist's `SKILL.md`; never emulate a missing package. Load the [review document contract](references/review-document-contract.yaml), [artifact metadata](references/artifact-metadata.yaml), [approval policy](references/approval-invalidation-policy.yaml), [naming rules](references/naming-conventions.yaml), and [failure taxonomy](references/failure-taxonomy.yaml) when validating or changing artifacts. When the request requires state continuity or says no parallelism, also load the [strict serial continuation profile](references/sequential-continuation-profile.yaml).

## Inputs

- User brief, seed images/audio/video, format/runtime constraints, and requested lifecycle mode.
- Versioned specialist artifacts with provenance and content hashes.
- Human approval bound to the exact authoritative production-plan hash.
- Live ComfyUI capability profile and validated workflow-catalog revision after approval.
- Render reports, QC verdicts, repair plans, and approved media manifests during production.

## Required outputs

- Machine-readable dispatch result with state, owner, inputs, outputs, and failures.
- Reviewed plan pair: `plan/production-plan-vNN.md` and `plan/production-plan-vNN.yaml`.
- After approval, versioned compiled jobs, an acyclic production DAG, execution/QC routing records, or an explicit blocking report.
- An invalidation scope for every change and a new revision for every replaced artifact.

## Processing method

1. Select the requested mode; default to `PLAN_ONLY`.
2. Validate the current project state and all required source revisions.
3. Resolve and load each package through `specialist-registry.yaml`, then dispatch Request Normalizer, Reference/Canon Manager, Plot Architect, Scene/Performance Writer, conditional Sound/Dialogue Planner, Storyboard Director, Animatic/Previs Planner, and an independent Production Preflight Reviewer.
4. Merge outputs without rewriting specialist-owned fields, write the exact review-document pair required by `review-document-contract.yaml`, bind the authoritative YAML to a SHA-256 content hash, and stop for explicit human approval.
5. For an approved plan, probe live ComfyUI capabilities, freeze the capability profile, compile H3 packets and endpoint jobs, validate graphs, and build the dependency DAG before queueing anything.
6. Use the declared execution profile. Independent cuts may run in parallel only when the request permits it; under `strict_serial_continuation`, admit exactly one production job and serialize every boundary as `render -> decode/hash -> extract actual final frame -> full/QC/privacy review -> approve endpoint -> bind successor first frame -> compile successor -> render successor`.
7. Compile bridges only after both endpoint states are approved. Treat dissolves as editorial post-production, not semantic continuity.
8. Route every completed segment to an independent QC pass; send only failed units and their transitive dependents to Repair Director.
9. Assemble only approved media, preserve exact handles and audio continuity, and send the master to final QC.

## Strict serial continuation profile

When the request requires scene state to persist or explicitly forbids parallelism:

- Create a one-way chain; never create circular or mutual scene references.
- Freeze one exact successor mode before plan review. For the current H3 bath profile, use `MiniMaxH3ImageToVideo` / I2VA after the initial R2VA segment.
- Treat the predecessor's actual final decoded frame as the only temporal-state endpoint. Validate the final 12-frame window, but never substitute an earlier frame when frame 191 fails.
- Require matching dimensions, orientation, pixel aspect, and colorspace. Do not normalize an endpoint by crop, pad, stretch, denoise, or creative editing unless a separately hashed derivative is approved.
- Keep each segment at exactly 192 frames, 24 fps, and 8.000 seconds when the profile declares the 64-second eight-segment grid. Retain both sides of a boundary and document the repeated endpoint frame.
- Compile an abstract dependency manifest after approval. Compile only the initial executable job; compile each successor just in time after its predecessor endpoint is approved and hash-bound.
- Make adult-only, non-explicit depiction, chest-deep water, dense mist/steam coverage, and absence of transient revealing frames hard full-segment QC gates.
- Bind video VAE, audio VAE, model, and CLIP to the verified RTX 4090 logical device; fail closed on CPU or alternate-GPU fallback.
- Treat a transition-topology change from `cut` to `continue` as a creative plan delta requiring human approval.

## Invariants

- Keep every accepted generation segment's target and effective duration greater than zero and at most 10 seconds. A longer intended shot is a chain of independently generated segments, not one oversized job.
- Record target duration, model-aligned frame count/duration, and effective post-trim frame count/duration separately. Extract handoff frames only from the effective clip.
- Require an approved, stable predecessor tail before a continuation successor can compile or render. Never use an unapproved or motion-blurred tail merely to keep a queue moving.
- In a strict serial chain, require the predecessor's actual final decoded frame and its endpoint hash; validate the final stability window without selecting a substitute frame.
- Keep continuation successor jobs endpoint-pending until the predecessor has passed segment QC and endpoint approval. Never pre-submit a successor prompt.
- Keep `cut`, `continue`, `bridge`, `match_cut`, and `dissolve` as distinct declared transition semantics.
- Require live `/object_info` and installed model/node evidence before ComfyUI compilation; do not trust stale positional widget fallbacks or legacy UUID workflows.
- Bind every compiled job to the approved plan revision/hash, prompt/workflow/template revisions, model/node versions, seed, paths, and source assets.
- Record logical-to-physical GPU identity, model/CLIP/VAE placement, runtime flags, and fallback policy in the capability and run provenance.
- Treat seeds as reproducibility inputs, not a guarantee of identical pixels across runtimes; preserve every attempt and its hashes.
- Preserve approved artifacts and media immutably. Create a new revision and record `supersedes` instead of overwriting.
- Never approve the orchestrator's own plan or output.

## Non-responsibilities

- Do not invent plot beats, dialogue, canon, blocking, camera language, H3 field syntax, or ComfyUI node graphs.
- Do not reinterpret seed-image roles, shorten or merge approved segments, or turn a failed continuation into a cut without plan/change approval.
- Do not judge visual quality, author a repair, or conceal a failure with an undocumented crossfade or edit.
- Do not execute a stage whose specialist package or capability contract is unavailable; return the owning failure code and stop that branch.

## Failure conditions

Return one or more codes from [failure-taxonomy.yaml](references/failure-taxonomy.yaml), affected stable IDs, evidence, blocking scope, and the responsible owner. Stop on missing requirements/assets, ambiguous canon, invalid state transitions, approval/hash mismatch, duration over 10 seconds, unstable endpoints, dependency cycles, unavailable ComfyUI nodes/models, unsupported H3 mode combinations, failed QC handoffs, or attempted approved-output overwrite.

## Validation rules

- Validate package metadata against [skill-package-contract.yaml](references/skill-package-contract.yaml) and the instance contract at [skill-contract.yaml](references/skill-contract.yaml).
- Validate artifact provenance, immutable revision, content hash, lifecycle status, and approved-plan linkage.
- Validate stable IDs and deterministic paths using [naming-conventions.yaml](references/naming-conventions.yaml); filenames never replace artifact identity.
- Validate DAG acyclicity and relation-specific dependencies: continuation waits for an approved tail, bridge waits for approved head and tail, and independent cuts have no false dependency.
- Validate strict serial profiles for one in-flight production job, one-way predecessor edges, exact endpoint frame binding, endpoint hash lineage, and no successor-ready state before approval.
- Validate normalized resolution, FPS, frame order, color, codec, audio sample rate/channels, duplicate endpoint trimming, and final seam evidence before assembly.
- Validate safety/privacy criteria over the entire segment and endpoint window, not only at a chosen handoff frame. Validate segment QC before endpoint approval, assembly before final-master QC, and final-master QC before delivery.
- Run `python scripts/validate_package.py` after editing the package.

## Minimal example

For a 24-second continuous camera shot, keep one intended shot ID but create at least three generation segments at or below 10 seconds. Render and QC the first, approve its stable effective tail, bind that exact image as the second segment's first frame in ComfyUI, and repeat before assembly.

## Adversarial example

If a caller asks to queue an 11-second continuation from an unapproved render, return `SEGMENT_TOO_LONG` and `HANDOFF_TAIL_UNAPPROVED`. Do not silently shorten it, use the raw tail, switch to a cut, or queue the job.

## Acceptance tests

- Default `PLAN_ONLY` stops at `PLAN_REVIEW_READY`.
- Compilation is rejected unless approval status and plan content hash match.
- A segment over 10 seconds is rejected before DAG creation or `/prompt` submission.
- Continuation jobs serialize behind QC and approved-tail selection; intentional cuts can run in parallel.
- A strict serial continuation chain admits one job at a time, compiles successors just in time, and blocks all descendants after an ancestor or endpoint failure.
- A strict serial eight-segment grid retains exactly 192 frames per segment and records the repeated boundary-frame policy.
- A failed middle segment leaves approved neighboring segments immutable.
- Missing ComfyUI capability fails before queueing and names the affected jobs.
- Creative repair changes return to plan review and require a new approval.
- Approved output write attempts create a new revision rather than overwrite.
