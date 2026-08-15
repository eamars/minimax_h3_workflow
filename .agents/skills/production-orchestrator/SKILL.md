---
name: production-orchestrator
description: Run the complete real-cinematic AI-video lifecycle automatically across planning, MiniMax H3 prompt compilation, ComfyUI workflow compilation, rendering, continuity QC, repair, assembly, and final QC. Use for full multi-stage production without human production gates; use the comfyui skill directly when one ready-to-queue multishot graph is the only requested deliverable.
---

# Production Orchestrator

## Mission

Turn a brief and optional seed media into a validated final video by routing every stage automatically. Preserve specialist ownership and stop only for a genuine missing creative decision or failed technical/quality validation. Never require a human production gate or content fingerprint for stage admission.

## Ownership boundary

Own lifecycle mode, dispatch order, revision tracking, dependency scheduling, and failure routing. Keep editorial shots, generated segments, editorial boundaries, and generation handoffs distinct. Delegate story, canon, performance, sound, camera, H3 syntax, graph compilation, rendering, QC, repair, and editing to their named skills.

Read the [specialist registry](references/specialist-registry.yaml), [routing policy](references/routing-policy.yaml), [state machine](references/state-machine.yaml), [artifact metadata](references/artifact-metadata.yaml), [naming rules](references/naming-conventions.yaml), and [failure taxonomy](references/failure-taxonomy.yaml). Read the [serial continuation profile](references/sequential-continuation-profile.yaml) for continuous scenes.

## Inputs

- User brief, requested runtime/delivery, and optional image/audio/video references.
- Existing project revisions when resuming or repairing.
- Live ComfyUI capability evidence and the workflow catalog before compilation.
- Render reports, QC evidence, repair plans, and QC-passed media during production.

## Required outputs

- Versioned planning artifacts and a preflight verdict.
- H3 prompt packets, ComfyUI jobs/workflows, and an acyclic dependency DAG.
- Render reports, QC evidence, localized repairs, final EDL/audio plan, assembled master, and final QC result.
- A machine-readable lifecycle state and failures after every stage.

## Processing method

1. Default to `FULL_PIPELINE`; honor `PLAN_ONLY`, `COMPILE_PLAN`, path-test, repair, or assembly modes only when explicitly requested.
2. Dispatch Request Normalizer, Reference/Canon Manager, Plot Architect, Scene/Performance Writer, conditional Sound/Dialogue Planner, Storyboard Director, Animatic/Previs Planner, and Production Preflight Reviewer.
3. If preflight fails, route the smallest revision request to its owning skill and rerun affected planning stages. Continue automatically once preflight passes.
4. Probe live ComfyUI, compile H3 prompt packets, prepare required endpoint media, compile API workflows, validate graphs, and build the production DAG.
5. Render dependency-ready jobs. Run independent branches concurrently only when policy permits; serialize continuous handoffs.
6. Route every generated segment through Continuity and QC Supervisor. Send failures to Repair Director and rerun only the affected dependency closure.
7. Assemble QC-passed media through Post Editor and run final QC. Enter `DELIVERED` only after the master passes final QC.
8. Create new revisions instead of overwriting prior artifacts. Revision identity controls freshness.

For a direct one-start workflow, route to `$comfyui`. That path builds one UI graph and uses the Joey Gambino H3 multishot continuity rules without creating the formal per-segment DAG.

## Invariants

- Require no human validation or validation sidecar at any stage.
- Keep plan/artifact revision IDs for freshness and raw-media/model checksums only for technical integrity.
- Preserve actual source media, completed renders, and QC evidence; never silently overwrite them.
- Keep generated segments positive and at most 10 seconds in the formal pipeline.
- For a continuous chain, relay the predecessor's actual final decoded frame, hold the exact closing state/camera/audio at the next opening for about two seconds, add only micro-motion in that airlock, and settle action/dialogue about two seconds before the next boundary.
- Repeat identity, wardrobe, environment, lighting, and voice anchors verbatim across connected shots.
- Never split one spoken line across generated shots. Put cuts, reframes, and new action after the opening airlock, inside a shot.
- Never place a scene/shot transition at a generation boundary. Put it in the
  protected middle 40–60% of one transition-bearing segment, leave enough time
  to establish the destination scene before the landing, and make the next
  segment a pure continuation of that established closing context.
- Compile and admit a continuation only after its predecessor passes QC and its endpoint validates. Do not substitute an earlier “better” frame for the actual final frame.
- Restart a chain at true scene cuts and monitor long chains for accumulated visual/audio drift.
- Keep live `/object_info` and installed model/node evidence authoritative.

## Non-responsibilities

Do not invent specialist-owned creative decisions, judge media without QC evidence, conceal failed continuity with an undocumented transition, or weaken the verified GPU/offload configuration to force a run.

## Failure conditions

Stop only the affected scope for missing requirements/assets, unresolved canon, invalid planning contracts, failed preflight, unsupported H3 modes, unavailable nodes/models, invalid graph/DAG, failed render, failed continuity or endpoint validation, unrepairable media, or failed final QC. Ask the user only when the missing choice materially changes their story or requested output.

## Validation rules

- Validate skill packages with `python scripts/validate_production_system.py`.
- Validate schemas, stable IDs, revisions, paths, DAG acyclicity, timing, continuity state, camera mappings, generation relationships, environment projection, and limb/prop targets.
- Validate every graph against live `/object_info` immediately before submission.
- Validate decoded frame/audio counts, seam evidence, and final delivery specs.
- Reject any workflow path that requests a human production gate or an administrative content fingerprint.

## Minimal example

For a 24-second continuous scene, plan three generated segments of at most 10 seconds, pass the actual final frame and matching state/camera/audio into each successor, QC each segment and seam, repair only failures, assemble the result, and run final QC automatically.

## Adversarial example

If a continuation endpoint fails QC, do not ask for production validation, use an earlier tail, or hide the seam with a dissolve. Repair the failing segment or revise its declared generation relationship, then recompile and rerun the affected successor closure.

## Acceptance tests

- Full pipeline progresses from brief to final QC without a validation sidecar or content-fingerprint gate.
- Preflight revisions loop automatically to the owning planning skill.
- Independent branches may run concurrently; continuous successors remain serial.
- Every continuation uses the actual validated final frame and exact boundary state/camera/audio.
- A localized failure preserves unaffected media and reruns only dependent work.
- Direct one-start requests route to `$comfyui`; formal production requests retain every specialist stage.
- Final delivery requires QC PASS, not human validation.
