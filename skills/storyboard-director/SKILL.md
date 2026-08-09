---
name: storyboard-director
description: "Model-neutral creative direction for AI-video storyboards: translate canon, plot, playable performance, and optional sound intent into director treatment, blocking, shot purpose, camera/edit language, four-track timelines, continuity, handoffs, and generation-sized segments. Use after planning inputs and before animatic/preflight; use for multi-shot or continuous-shot plans and cut/continue/bridge/match_cut/dissolve decisions."
---

# Storyboard Director

## Mission

Translate valid narrative and performance artifacts into a traceable, model-neutral storyboard. Specify audience view, blocking, shot purpose, camera/edit behavior, sound timing, and independently generated segment boundaries. Leave prompts, graphs, execution, QC, repair, and post downstream.

Read the [segment rules](references/segment-rules.yaml), [skill contract](references/skill-contract.yaml), and `schemas/storyboard-package.schema.json`.

## Ownership boundary

Own director treatment, geography, blocking, shot purpose, concrete camera language, axis/screen direction, composition, editorial intent, four synchronized tracks, creative reference jobs, continuity, shot/segment cards, transition semantics, handoff requirements, risk, and acceptance criteria. Preserve plot, canon, playable behavior, dialogue, speakers, and sound intent.

## Inputs

Consume exact revisions of project request, canon/asset manifest, plot, scene-performance, conditional sound plan, and optional prior storyboard revision/change request. Reject missing/mismatched sources and never infer endpoint roles.

## Required outputs

Emit `storyboard-package.yaml`, `shot-table.md`, `segment-plan.yaml`, `handoff-manifest.yaml`, and `creative-acceptance-tests.yaml`. Use stable sequence/scene/shot/segment IDs, shared envelopes, deterministic paths/order, and machine status with `next_skill: animatic-previs-planner`.

## Processing method

1. Validate source schemas, IDs, revisions, hashes, status, and conflict readiness.
2. Establish project → sequence → scene → intended shot → generation segment; preserve one shot ID across splits.
3. Write director treatment grounded in source intent.
4. Give each shot one purpose and information/emotional change with plot/performance links.
5. Block entry pose/gaze/hands/props/path/reaction/exit before placing camera.
6. Specify size, angle, height, lens feel, position, depth, axis, horizon, and one motivated dominant move or static.
7. Build monotonic `TIME | PERFORMANCE | CAMERA | SOUND | EDIT/HANDOFF` tracks with readable entry, action/reaction, settle, and stable exit.
8. Split when duration exceeds 10 seconds or risk/context/density/continuity/reference/repair needs demand it.
9. Declare exactly one transition: cut, continue, bridge, match_cut, dissolve, or terminal end.
10. Record continuity and handoff requirements without approving media.
11. Generate concrete acceptance predicates and canonical hashes.
12. Return review-ready/blocked artifacts and affected-ID failures.

## Invariants

- Trace every shot to plot and every segment to plot, performance, canon, shot, neighbors, and acceptance tests.
- Require `0 < duration_seconds <= 10` without rounding before comparison.
- Use one primary performance arc and one dominant camera move/static per segment.
- Establish entry before action; finish important action/reaction before a stable exit handle.
- Reject blurred, occluded, unfinished, uncontrolled, fast-pan, or impossible-reflection exits.
- Preserve exact transition semantics and source decisions.
- Emit no H3, node, workflow, queue, render, QC, repair, or post settings.

## Non-responsibilities

Do not normalize intake, reinterpret canon, change plot, write dialogue/sound, select models/modes, compile prompts/workflows, probe capability, render/extract/approve media, judge QC, repair, assemble, mix, or deliver.

## Failure conditions

Return declared storyboard codes for invalid sources/provenance, purposeless shots, ambiguous blocking, nonpositive/overlong/overloaded segments, missing entry/unstable exit, unspecified/invalid handoffs, nonmonotonic timelines, unmotivated camera, missing traceability, or technical leakage. Pass upstream failures unchanged.

## Validation rules

- Validate schema, envelope/hash, stable IDs, traceability, duration, four-track timing, transitions/handoffs, and technical separation—in that order.
- Require exact transition matrix: cut independent; continue exact predecessor exit; bridge both endpoints; match cut bilateral motif; dissolve post-only.
- Require one move/arc per segment and resolvable source links.
- Report failures; never auto-repair creative content.

## Minimal example

For a 5.5-second reveal, use one purposeful shot, readable entry, one observable notice/reaction arc, a static or single motivated move, timed sound, settled visible exit, and an independent cut. Attach source and acceptance IDs.

## Adversarial example

Block one “seamless cinematic” 11-second clip containing multiple unrelated arcs, a 180-degree spin, new confession, and mid-pan exit. Return overlength/overload/unstable-handoff failures instead of shortening silently or inventing a workflow.

## Acceptance tests

- Split a 24-second continuous intended shot into at least three <=10-second segments with one shot ID and continuation handoffs.
- Accept 10.000 seconds; reject 10.0001 and 11.
- Reject nonpositive, overloaded, unstable, untraceable, vague, or technically contaminated segments.
- Validate all transition semantics and four-track order.
- Produce deterministic outputs and preserve immutable source revisions.
