---
name: production-orchestrator
description: Plan and coordinate approval-gated real-cinematic AI video production across specialist skills, MiniMax H3 prompt compilation, ComfyUI API jobs, editorial shots, generated segments, continuity QC, repair, and final assembly. Use only when the user explicitly requests review approvals, independent jobs, formal QC/repair, or delivery provenance. Do not use for a request to convert any brief, plot, storyboard, or shot list into one ready-to-use ComfyUI workflow and final one-start render; route that directly to the comfyui skill.
---

# Production Orchestrator

Coordinate the local AI-video production lifecycle as a thin, stateful router. Preserve each specialist's decision authority, stop at human review by default, and never silently change creative intent to satisfy a downstream workflow.

## Mission

Turn a user brief and seed-asset set into a traceable production plan, then—only after explicit approval—route validated MiniMax H3 and ComfyUI compilation, execution, QC, repair, and assembly stages.

## Direct UI-workflow boundary

If the user asks for one local UI-format workflow that can be loaded and queued
once from any input, route directly to the `comfyui` skill's one-start H3
seamless-chain path. Do not create a project plan, request approval, calculate
an approval hash, build a production DAG, or emit per-segment API jobs. Do not
claim this orchestrator's `COMPILED` state is a ready-to-click ComfyUI canvas:
its compiler outputs API-format jobs for Render Orchestrator, not one UI graph.

Use this orchestrator instead when exact unequal shot timecodes, independently
repairable segments, human approval, endpoint QC, or delivery status is part of
the requested contract. A source `plot.md` alone is not an approved production
plan and cannot enter compilation or rendering through this lifecycle.

## Ownership boundary

Own lifecycle mode selection, dispatch order, artifact-envelope validation, project state, approval/hash gates, invalidation scope, and dependency scheduling. Enforce the separation between editorial shots, generated segments, editorial boundaries, and generation handoffs. Delegate narrative, canon, scene, sound, camera, prompt syntax, workflow graph, rendering, QC, repair, and editorial decisions to their named specialist packages.

Read the directly linked [specialist registry](references/specialist-registry.yaml), [routing policy](references/routing-policy.yaml), and [state machine](references/state-machine.yaml) before dispatching. Load every dispatched specialist's `SKILL.md`; never emulate a missing package. Load the [review document contract](references/review-document-contract.yaml), [artifact metadata](references/artifact-metadata.yaml), [approval policy](references/approval-invalidation-policy.yaml), [naming rules](references/naming-conventions.yaml), and [failure taxonomy](references/failure-taxonomy.yaml) when validating or changing artifacts. When the request requires state continuity or says no parallelism, also load the [strict serial continuation profile](references/sequential-continuation-profile.yaml).

## Inputs

- User brief, seed images/audio/video, format/runtime constraints, and requested lifecycle mode.
- Explicit execution lifecycle: `PATH_TEST` for technical route validation with visual quality skipped, or `PRODUCTION` for the approval-gated render/QC/delivery route. A path test is never a delivery state.
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
3. Resolve and load each package through `specialist-registry.yaml`, then dispatch Request Normalizer, Reference/Canon Manager, Plot Architect, Scene/Performance Writer, conditional Sound/Dialogue Planner for pre-storyboard sound intent, Storyboard Director, Animatic/Previs Planner for the record-time and post-storyboard sound-boundary pass, and an independent Production Preflight Reviewer.
4. Merge outputs without rewriting specialist-owned fields, write the exact review-document pair required by `review-document-contract.yaml`, bind the authoritative YAML to a SHA-256 content hash, and stop for explicit human approval.
5. For an approved plan, probe live ComfyUI capabilities, freeze the capability profile, compile H3 packets and endpoint jobs, validate graphs, and build the dependency DAG before queueing anything.
6. Use the declared execution profile. Independent generation relationships may run in parallel only when the request permits it; under `strict_serial_continuation`, admit exactly one production job and serialize only the typed same-shot handoff as `render -> decode/hash -> extract actual final frame -> full/QC/privacy review -> approve endpoint -> bind successor first frame -> compile successor -> render successor`.
7. Compile endpoint bridges only after both endpoint states are approved. Apply cuts, dissolves, and fades only in editorial post-production; never infer a generation dependency from an editorial mechanism.
8. Route every completed segment to an independent QC pass; send only failed units and their transitive dependents to Repair Director.
9. Assemble only approved media, preserve exact handles and audio continuity, and send the master to final QC.

## Technical path-test mode

Use `PATH_TEST` only when the user explicitly prioritizes proving the workflow path over visual evaluation. It may render every admitted job, write technical-intake manifests, and create a clearly labeled straight-cut draft for decode/A/V/provenance validation. It must set `quality_evaluation: not_performed_by_user_instruction`, keep the lifecycle status outside `DELIVERED`, disclose every planned editorial transition that was not realized, and stop before continuity QC, repair approval, final QC, or delivery. Use the bundled `scripts/validate_path_test.py` as the independent acceptance gate.

Use `PRODUCTION` for any cinematic or deliverable claim. Every required segment must pass independent continuity QC; every declared cut/dissolve/fade must be realized by the post-editor; the assembled master must pass independent final QC; only then may the lifecycle enter `DELIVERED`. A technical draft, playable MP4, or successful ComfyUI history item never satisfies these gates by itself.

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
- Treat a change to camera setup/motion, editorial boundary mechanism/motivation, generation relationship, or editorial shot boundary as a creative plan delta requiring human approval. A technical generation-segment resplit is allowed without creative reapproval only when the approved shot boundary, camera interval map, continuity contract, record edit points, generation relationship/policy, and prompt intent remain byte-identical and the superseding revision records the old-to-new segment map.

## Invariants

- Keep every accepted generation segment's target and effective duration greater than zero and at most 10 seconds. A longer intended shot is a chain of independently generated segments, not one oversized job.
- Record target duration, model-aligned frame count/duration, and effective post-trim frame count/duration separately. Extract handoff frames only from the effective clip.
- Require the endpoint policy declared by the generation handoff. A stable predecessor tail is mandatory for `stable_tail`, but a moving endpoint or approved entry reference is valid when the plan declares it and QC can assess it.
- In a strict serial chain, require the predecessor's actual final decoded frame and its endpoint hash; validate the final stability window without selecting a substitute frame.
- Keep continuation successor jobs endpoint-pending until the predecessor has passed segment QC and endpoint approval. Never pre-submit a successor prompt.
- Keep editorial mechanisms (`cut`, `dissolve`, `fade`, `end`) distinct from generation relationships (`independent`, `same_shot_continue`, `endpoint_bridge`, `reference_reestablish`, `terminal`).
- Carry a hard environment projection and a typed interaction-target registry into compilation and render admission. Camera position/viewpoint may change only inside that projection; unknown limb targets, prop ownership, or environment features fail closed.
- Require live `/object_info` and installed model/node evidence before ComfyUI compilation; do not trust stale positional widget fallbacks or legacy UUID workflows.
- Bind every compiled job to the approved plan revision/hash, prompt/workflow/template revisions, model/node versions, seed, paths, and source assets.
- Record logical-to-physical GPU identity, model/CLIP/VAE placement, runtime flags, and fallback policy in the capability and run provenance.
- Treat seeds as reproducibility inputs, not a guarantee of identical pixels across runtimes; preserve every attempt and its hashes.
- Preserve approved artifacts and media immutably. Create a new revision and record `supersedes` instead of overwriting.
- Never approve the orchestrator's own plan or output.

## Non-responsibilities

- Do not invent plot beats, dialogue, canon, blocking, camera language, H3 field syntax, or ComfyUI node graphs.
- Do not reinterpret seed-image roles, shorten or merge approved segments, or turn a failed generation handoff into a different relationship or editorial cut without plan/change approval.
- Do not judge visual quality, author a repair, or conceal a failure with an undocumented crossfade or edit.
- Do not execute a stage whose specialist package or capability contract is unavailable; return the owning failure code and stop that branch.

## Failure conditions

Return one or more codes from [failure-taxonomy.yaml](references/failure-taxonomy.yaml), affected stable IDs, evidence, blocking scope, and the responsible owner. Stop on missing requirements/assets, ambiguous canon, invalid state transitions, approval/hash mismatch, duration over 10 seconds, unstable endpoints, dependency cycles, unavailable ComfyUI nodes/models, unsupported H3 mode combinations, failed QC handoffs, or attempted approved-output overwrite.

## Validation rules

- Validate package metadata against [skill-package-contract.yaml](references/skill-package-contract.yaml) and the instance contract at [skill-contract.yaml](references/skill-contract.yaml).
- Validate artifact provenance, immutable revision, content hash, lifecycle status, and approved-plan linkage.
- Validate stable IDs and deterministic paths using [naming-conventions.yaml](references/naming-conventions.yaml); filenames never replace artifact identity.
- Validate DAG acyclicity and generation-relation-specific dependencies: `same_shot_continue` waits for the declared endpoint policy, `endpoint_bridge` waits for approved head and tail, and `independent` relationships have no false dependency. Validate editorial boundaries separately in the EDL.
- Validate strict serial profiles for one in-flight production job, one-way predecessor edges, exact endpoint frame binding, endpoint hash lineage, and no successor-ready state before approval.
- Validate lifecycle mode and truthful status: `PATH_TEST` cannot emit QC-PASS or delivery artifacts, while `PRODUCTION` cannot bypass segment or final QC. Validate resume against the original admitted job set, plan/DAG/capability/environment hashes, and complete media provenance.
- Validate the environment prompt projection immediately before queueing: required landmarks, boundary/unknown-space language, profile ID, and negated-only forbidden-feature references. Validate bilateral limb semantics, declared interaction targets, and no double-held prop.
- Validate normalized resolution, FPS, frame order, color, codec, audio sample rate/channels, duplicate endpoint trimming, and final seam evidence before assembly.
- Validate safety/privacy criteria over the entire segment and endpoint window, not only at a chosen handoff frame. Validate segment QC before endpoint approval, assembly before final-master QC, and final-master QC before delivery.
- Run `python scripts/validate_package.py` after editing the package.
- Run `python scripts/validate_path_test.py` for technical path mode; do not substitute it for continuity or final QC.

## Minimal example

For a 24-second continuous camera shot, keep one editorial shot ID but create at least three generation segments at or below 10 seconds. Declare whether each join uses a stable tail or moving endpoint, then render/QC/approve only the required endpoint before binding the successor. Keep the final editorial cut plan separate.

## Adversarial example

If a caller asks to queue an 11-second same-shot successor from an unapproved render, return `SEGMENT_TOO_LONG` and the applicable handoff-approval failure. Do not silently shorten it, use the raw tail, change the camera/coverage, switch the editorial cut, or queue the job.

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
- Path-test mode emits a truthful non-deliverable status and independently verifies every job report, QC-intake record, source/output hash, exact video frame count, and exact audio sample count.
- A positive forbidden environment feature, undeclared limb target, missing prompt projection, stale resume selection, mismatched ComfyUI prompt ID, or unsupported editorial transition blocks before queue/assembly.
