---
name: storyboard-director
description: "Model-neutral feature-film storyboard direction for AI-video projects: translate canon, plot, playable performance, and sound intent into editorial shots, typed camera setups and moves, scene geography, continuity state, cut transitions, and generation-sized segments. Use after planning inputs and before animatic/preflight when camera position may change between shots while character and setting state remain traceable."
---

# Storyboard Director

## Mission

Translate valid narrative and performance artifacts into a traceable, model-neutral feature-film storyboard. Treat the editorial shot as the creative unit and the generation segment as a production unit. Specify audience view, geography, blocking, shot purpose, camera setup, in-shot motion, sound timing, editorial cut boundaries, continuity state, and independently generated segment handoffs. Carry the canon's hard environment projection into every shot and segment so a camera move changes viewpoint within the validated space rather than inventing a different room. Leave prompts, graphs, execution, QC, repair, and post downstream.

Read the [segment rules](references/segment-rules.yaml), [skill contract](references/skill-contract.yaml), `schemas/storyboard-package-v2.schema.json`, and run `scripts/validate_storyboard.py` for every v2 package. When an interactive prop or fixture appears, pass the exact project interaction-target registry with `--interaction-target-registry`; the validator then checks bilateral limb semantics, target existence, prop ownership, and transfer legality. The v1 schema and validator remain available only for historical artifacts.

## Ownership boundary

Own director treatment, scene geography, spatial staging, shot purpose, concrete camera language, axis/screen direction, composition, editorial intent, four synchronized tracks, creative reference jobs, continuity invariants, editorial boundaries, shot/segment cards, generation handoff requirements, risk, and acceptance criteria. Preserve plot, canon, playable behavior, dialogue, speakers, and sound intent. A shot may change camera position, viewpoint, lens, or composition from its predecessor when the change is motivated and typed, but it may not expand the environment beyond the hard projection.

## Inputs

Consume exact revisions of project request, canon/asset manifest, environment profile, plot, scene-performance, conditional sound plan, and optional prior storyboard revision/change request. Reject missing/mismatched sources and never infer endpoint roles.

## Required outputs

Emit `storyboard-package.yaml`, `shot-table.md`, `segment-plan.yaml`, `editorial-boundary-manifest.yaml`, `generation-handoff-manifest.yaml`, and `creative-acceptance-tests.yaml`. Use stable sequence/scene/shot/segment IDs, shared envelopes, explicit `planning_model_version: 2`, three time domains (`scene_time`, `source_time`, `record_time`), deterministic paths/order, and machine status with `next_skill: animatic-previs-planner`.

## Processing method

1. Validate source schemas, IDs, declared revisions, status, and conflict readiness.
2. Establish project → sequence → scene → editorial shot → generation segment; preserve one shot ID across splits and never use a segment as a substitute for a shot.
3. Write director treatment grounded in source intent.
4. Bind the hard environment projection before designing coverage. Carry its required landmarks, forbidden inventions, unknown regions, negative-space rule, and profile ID into the treatment and acceptance tests.
5. Give each shot one purpose and information/emotional change with plot/performance links. If no style source exists, do not lock a named visual style; describe only source-backed medium, world, lighting, texture, and tonal facts so downstream generation remains style-capable.
6. Build scene geography and stage entry, action path, eyelines, landmark relations, and exit before placing the camera.
7. Specify a structured camera setup (position, viewpoint, optics, composition, axis) separately from one motivated in-shot motion or static path. Record a motivated setup change from the previous shot; do not prohibit camera position changes. Expand an intended orbit into a spatial arc or a directional truck-plus-counter-pan pair instead of leaving the camera instruction as an opaque “orbit.”
8. Build monotonic `SCENE_TIME | SOURCE_TIME | RECORD_TIME` plus `PERFORMANCE | CAMERA | SOUND | EDIT/HANDOFF` tracks with readable entry, action/reaction, and context-appropriate exit handling. For every editorial shot, make the downstream projection recoverable as `shot size + visible content + camera + action + dialogue/speaker state + sound`.
9. Fit dialogue to the available shot time. Declare the actual speaker, on-screen/off-screen transition, and J-cut or L-cut span when speech begins before or continues after a picture cut.
10. Split when generation duration exceeds 10 seconds or risk/context/density/continuity/reference/repair needs demand it; splitting preserves the editorial shot and creates a typed generation handoff.
11. Declare editorial boundaries bilaterally as `cut`, `dissolve`, `fade`, or terminal `end`, with motivations and audio behavior. Declare generation relationships separately as `independent`, `same_shot_continue`, `endpoint_bridge`, `reference_reestablish`, or `terminal`. Never rely on H3 to invent a default cut. When a generated chain must realize a scene/shot transition, assign it to the protected middle of one transition-bearing segment; the next segment opens only after the destination context is established.
12. Treat an exact first-plus-last-frame segment as continuous interpolation by default. Do not place an editorial cut merely because two endpoint images exist; any internal transition must be explicitly planned and timed.
13. Use one authoritative continuity registry plus an exact interaction-target registry. Shots and segments reference registered snapshots; if a payload is embedded, its interactive `prop_states` and `limb_states` must exactly match the registry. A contact target may be a declared prop, fixture/surface, landmark, or subject body zone; it may never be an invented ID.
14. At every split interaction, hand off the action phase, subject pose/gaze, left/right limb state, prop ownership/contact, camera pose and motion vector, focus plane, lighting, active speaker/dialogue span, ambience, and the next allowed delta. The successor continues that delta without replaying completed motion.
15. Record continuity invariants, expected deltas, forbidden deltas, and moving-versus-stable handoff suitability without approving media.
16. Generate concrete acceptance predicates and revision references.
17. Return review-ready/blocked artifacts and affected-ID failures.

## Invariants

- Trace every shot to plot and every segment to plot, performance, canon, shot, neighbors, and acceptance tests.
- Require `0 < duration_seconds <= 10` without rounding before comparison.
- Use one primary performance arc and one typed dominant in-shot camera move/static per generation segment; camera setup may change between editorial shots.
- Do not introduce a named style family when the request, canon, and references leave style unspecified.
- Require every editorial shot to project unambiguously to shot size, visible content, camera, action, dialogue/speaker state, and sound.
- Establish entry before action; finish important action/reaction before a stable exit handle.
- Reject blurred, occluded, unfinished, uncontrolled, fast-pan, or impossible-reflection exits only when that segment is declared a continuation or endpoint handoff; a motivated editorial cut may leave on active motion.
- Preserve exact editorial boundary semantics separately from generation handoff semantics.
- Forbid scene, shot, lens/setup, and visual-context resets at generation frame
  zero. A transition-bearing segment must retain the source context through its
  opening airlock, execute the declared transition in the 40–60% middle window,
  and settle in the destination context before its successor begins.
- Require identity, wardrobe, prop, wetness, environment, and sound invariants to be explicit even when framing changes.
- Require the environment projection to survive every framing change: a new position may reveal validated landmarks or unknown negative space, but may not turn a partial counter edge into a vanity, add a tub, mirror, corridor, window, basket, or second person.
- Require `limb_states` and prop states at every interactive entry, contact, transfer, release, and exit handoff. Preserve the same left/right allocation across independent cuts unless the performance state explicitly changes it.
- Distinguish endpoint snapshots from micro-actions inside one generation segment: an in-shot contact may be documented in scene-performance and the target registry without inventing an extra segment, but every visible handoff must still have a legal state, target, and release/ownership path.
- Treat the continuity registry as the only authority; duplicate snapshot IDs with divergent interactive payloads are invalid.
- If geography is unknown, mark the axis/region unknown and require an explicit coverage or axis-reset motivation; never invent coordinates.
- Emit no H3, node, workflow, queue, render, QC, repair, or post settings.

## Non-responsibilities

Do not normalize intake, reinterpret canon, change plot, write dialogue/sound, select models/modes, compile prompts/workflows, probe capability, render/extract/validate media, judge QC, repair, assemble, mix, or deliver.

## Failure conditions

Return declared storyboard codes for invalid sources/provenance, missing or violated environment locks, purposeless or thin coverage, ambiguous geography/staging, opaque camera plans, nonpositive/overlong/overloaded segments, missing entry/continuity/limb state, divergent duplicate snapshots, inappropriate unstable exits, conflated editorial/generation boundaries, unspecified/invalid handoffs, nonmonotonic time domains, unmotivated camera setup/motion, missing traceability, or technical leakage. Pass upstream failures unchanged.

## Validation rules

- Validate schema, envelope/revision, stable IDs, traceability, hard environment projection, typed geography/staging, three time domains, camera setup/position/viewpoint/optics/look-at/motion/risk, one authoritative continuity registry with limb/prop payload equality, declared interaction targets, legal limb semantics, no double-held props, and adjacent-state deltas, four-track timing, bilateral editorial boundaries with structured J/L audio edits, generation handoffs, and technical separation—in that order.
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
- Reject an undeclared model-invented cut, a two-endpoint segment treated as an automatic montage, or a split interaction whose successor replays the predecessor's completed action.
- Produce deterministic outputs and preserve immutable source revisions.
