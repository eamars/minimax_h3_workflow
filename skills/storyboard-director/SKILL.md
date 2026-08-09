---
name: storyboard-director
description: "Model-neutral feature-film storyboard direction for AI-video projects: translate canon, plot, playable performance, and sound intent into editorial shots, typed camera setups and moves, scene geography, continuity state, cut transitions, and generation-sized segments. Use after planning inputs and before animatic/preflight when camera position may change between shots while character and setting state remain traceable."
---

# Storyboard Director

## Mission

Translate valid narrative and performance artifacts into a traceable, model-neutral feature-film storyboard. Treat the editorial shot as the creative unit and the generation segment as a production unit. Specify audience view, geography, blocking, shot purpose, camera setup, in-shot motion, sound timing, editorial cut boundaries, continuity state, and independently generated segment handoffs. Carry the canon's hard environment projection into every shot and segment so a camera move changes viewpoint within the approved space rather than inventing a different room. Leave prompts, graphs, execution, QC, repair, and post downstream.

Read the [segment rules](references/segment-rules.yaml), [skill contract](references/skill-contract.yaml), `schemas/storyboard-package-v2.schema.json`, and run `scripts/validate_storyboard.py` for every v2 package. The v1 schema and validator remain available only for historical artifacts.

## Ownership boundary

Own director treatment, scene geography, spatial staging, shot purpose, concrete camera language, axis/screen direction, composition, editorial intent, four synchronized tracks, creative reference jobs, continuity invariants, editorial boundaries, shot/segment cards, generation handoff requirements, risk, and acceptance criteria. Preserve plot, canon, playable behavior, dialogue, speakers, and sound intent. A shot may change camera position, viewpoint, lens, or composition from its predecessor when the change is motivated and typed, but it may not expand the environment beyond the hard projection.

## Inputs

Consume exact revisions of project request, canon/asset manifest, environment profile, plot, scene-performance, conditional sound plan, and optional prior storyboard revision/change request. Reject missing/mismatched sources and never infer endpoint roles.

## Required outputs

Emit `storyboard-package.yaml`, `shot-table.md`, `segment-plan.yaml`, `editorial-boundary-manifest.yaml`, `generation-handoff-manifest.yaml`, and `creative-acceptance-tests.yaml`. Use stable sequence/scene/shot/segment IDs, shared envelopes, explicit `planning_model_version: 2`, three time domains (`scene_time`, `source_time`, `record_time`), deterministic paths/order, and machine status with `next_skill: animatic-previs-planner`.

## Processing method

1. Validate source schemas, IDs, revisions, hashes, status, and conflict readiness.
2. Establish project → sequence → scene → editorial shot → generation segment; preserve one shot ID across splits and never use a segment as a substitute for a shot.
3. Write director treatment grounded in source intent.
4. Bind the hard environment projection before designing coverage. Carry its required landmarks, forbidden inventions, unknown regions, negative-space rule, and profile ID into the treatment and acceptance tests.
5. Give each shot one purpose and information/emotional change with plot/performance links.
6. Build scene geography and stage entry, action path, eyelines, landmark relations, and exit before placing the camera.
7. Specify a structured camera setup (position, viewpoint, optics, composition, axis) separately from one motivated in-shot motion or static path. Record a motivated setup change from the previous shot; do not prohibit camera position changes.
8. Build monotonic `SCENE_TIME | SOURCE_TIME | RECORD_TIME` plus `PERFORMANCE | CAMERA | SOUND | EDIT/HANDOFF` tracks with readable entry, action/reaction, and context-appropriate exit handling.
9. Split when generation duration exceeds 10 seconds or risk/context/density/continuity/reference/repair needs demand it; splitting preserves the editorial shot and creates a typed generation handoff.
10. Declare editorial boundaries bilaterally as `cut`, `dissolve`, `fade`, or terminal `end`, with motivations and audio behavior. Declare generation relationships separately as `independent`, `same_shot_continue`, `endpoint_bridge`, `reference_reestablish`, or `terminal`.
11. Use one authoritative continuity registry. Shots and segments reference registered snapshots; if a payload is embedded, its interactive `prop_states` and `limb_states` must exactly match the registry.
12. Record continuity invariants, expected deltas, forbidden deltas, and moving-versus-stable handoff suitability without approving media.
13. Generate concrete acceptance predicates and canonical hashes.
14. Return review-ready/blocked artifacts and affected-ID failures.

## Invariants

- Trace every shot to plot and every segment to plot, performance, canon, shot, neighbors, and acceptance tests.
- Require `0 < duration_seconds <= 10` without rounding before comparison.
- Use one primary performance arc and one typed dominant in-shot camera move/static per generation segment; camera setup may change between editorial shots.
- Establish entry before action; finish important action/reaction before a stable exit handle.
- Reject blurred, occluded, unfinished, uncontrolled, fast-pan, or impossible-reflection exits only when that segment is declared a continuation or endpoint handoff; a motivated editorial cut may leave on active motion.
- Preserve exact editorial boundary semantics separately from generation handoff semantics.
- Require identity, wardrobe, prop, wetness, environment, and sound invariants to be explicit even when framing changes.
- Require the environment projection to survive every framing change: a new position may reveal approved landmarks or unknown negative space, but may not turn a partial counter edge into a vanity, add a tub, mirror, corridor, window, basket, or second person.
- Require `limb_states` and prop states at every interactive entry, contact, transfer, release, and exit handoff. Preserve the same left/right allocation across independent cuts unless the performance state explicitly changes it.
- Treat the continuity registry as the only authority; duplicate snapshot IDs with divergent interactive payloads are invalid.
- If geography is unknown, mark the axis/region unknown and require an explicit coverage or axis-reset motivation; never invent coordinates.
- Emit no H3, node, workflow, queue, render, QC, repair, or post settings.

## Non-responsibilities

Do not normalize intake, reinterpret canon, change plot, write dialogue/sound, select models/modes, compile prompts/workflows, probe capability, render/extract/approve media, judge QC, repair, assemble, mix, or deliver.

## Failure conditions

Return declared storyboard codes for invalid sources/provenance, missing or violated environment locks, purposeless or thin coverage, ambiguous geography/staging, opaque camera plans, nonpositive/overlong/overloaded segments, missing entry/continuity/limb state, divergent duplicate snapshots, inappropriate unstable exits, conflated editorial/generation boundaries, unspecified/invalid handoffs, nonmonotonic time domains, unmotivated camera setup/motion, missing traceability, or technical leakage. Pass upstream failures unchanged.

## Validation rules

- Validate schema, envelope/hash, stable IDs, traceability, hard environment projection, typed geography/staging, three time domains, camera setup/position/viewpoint/optics/look-at/motion/risk, one authoritative continuity registry with limb/prop payload equality and adjacent-state deltas, four-track timing, bilateral editorial boundaries with structured J/L audio edits, generation handoffs, and technical separation—in that order.
- Require editorial mechanisms `cut`, `dissolve`, `fade`, or `end`; keep generation relationships independent from those mechanisms.
- Require one move/arc per generation segment, resolvable source links, and a moving endpoint policy when a same-shot split cannot provide a stable tail.
- Report failures; never auto-repair creative content.

## Minimal example

For a 5.5-second reveal, use one purposeful editorial shot with a declared camera setup and motivated dolly or static path, timed scene/source/record ranges, stable character/environment state, a typed `cut` boundary, and an `independent` generation handoff. Attach source and acceptance IDs.

## Adversarial example

Reject a v1-style package that calls an opaque camera string a storyboard, puts `transition_to_next: continue` on every segment, supplies no geography, and represents an entire scene as one 11-second clip. Return camera/boundary/time/coverage failures; do not silently rewrite it into a short video.

## Acceptance tests

- Split a 24-second continuous intended shot into at least three <=10-second segments with one shot ID, explicit source/record times, and same-shot generation handoffs.
- Accept 10.000 seconds; reject 10.0001 and 11.
- Reject nonpositive, overloaded, inappropriate unstable, untraceable, vague, opaque-camera, unknown-geometry, or technically contaminated segments.
- Reject a shot that introduces architecture forbidden by the environment profile or an interactive action without explicit left/right limb continuity.
- Validate bilateral editorial boundaries, separate generation handoffs, all three time domains, camera setup/motion structure, and four-track order.
- Produce deterministic outputs and preserve immutable source revisions.
