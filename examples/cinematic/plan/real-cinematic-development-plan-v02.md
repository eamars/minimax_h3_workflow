# Real-Cinematic Production Skills Development Plan

Status: revised_after_independent_review
Version: v02
Supersedes: `real-cinematic-development-plan-v01.md`
Scope: shared storyboard, planning, validation, compilation, QC, orchestration, and post-production contracts
Reference failure case: `projects/PRJ01`
Implementation status: planning only; no production artifacts or approved plans are changed by this document

Review result: the independent SOL review found the v01 direction correct but returned **revise before implementation**. This revision incorporates its required amendments.

## 1. Goal

Make the production system capable of planning and preserving a genuinely cinematic scene: deliberate coverage, motivated camera setups and movement, readable geography, editorial rhythm, continuity, sound picture relationships, and long takes where appropriate.

The system must design the movie first and divide it into model-sized generation work second. A ten-second generation limit is a technical constraint; it must not become the scene's shot grammar.

“Real cinematic” means the plan can express, validate, and preserve independently:

- editorial shots and dramatic purposes;
- offscreen camera setups and visible in-shot camera movement;
- camera position/path, viewpoint/orientation, lens, focus, and composition;
- subject blocking and performance state;
- scene geography, action axes, eyelines, and visible spatial relationships;
- editorial boundaries, transition mechanisms, motivations, and audio overlap;
- technical generation segmentation and endpoint dependencies;
- character, environment, prop, wardrobe, lighting, wetness, gaze, and screen-direction continuity.

This is not a requirement for a generic “Hollywood” formula. Static observation, a long take, sparse coverage, a jump cut, or an axis crossing remains valid when explicitly motivated, geometrically legible, and traceable.

## 2. Current failure baseline

The current system has the intended hierarchy `project → sequence → scene → shot → generation segment`, but camera and transition semantics are mostly opaque strings.

- `storyboard-director` requires camera size, angle, height, lens feel, position, depth, axis, horizon, and one dominant move or static camera, but the schema does not model those properties.
- `generationSegment.dominant_camera_move` is only a non-empty string; timeline camera entries are also unstructured.
- `transition_to_next` mixes editorial meaning (`cut`, `match_cut`, `dissolve`) with technical generation relationships (`continue`, `bridge`).
- PRJ01 turns eight plot beats into eight equal 8-second segments and eight independent cuts. Its director treatment limits the camera to static or slow push-in/pull-back behavior and globally repeats a fixed axis.
- PRJ01 does not identify camera setups, camera paths, shot coverage, edit motivation, time overlap, or the difference between an editorial boundary and a generation boundary.
- The separate 10-second storyboard prompt asks for a close-up and then a medium mirror composition while forbidding cuts, orbit, lens change, and meaningful camera relocation.
- Existing validators emphasize required files, shallow fields, duration caps, transition presence, and endpoint stability. They do not validate scene geography, camera geometry, coverage, editorial motivation, time domains, or shot/segment separation.

PRJ01 must remain available as an immutable negative fixture. It must not be silently rewritten as part of this plan.

## 3. Target architecture

```text
Canon and scene state
  → typed scene geography and action axes
  → performance phases and spatial staging
  → feature-film shot and coverage plan
  → editorial boundaries and sound map
  → ≤10-second generation segmentation
  → generation-handoff dependency graph
  → H3 compilation
  → render and seam/shot/edit QC
  → post conform and final QC
```

### 3.1 Editorial shot versus generation segment

An editorial shot owns the audience-facing cinematic decision. It has a purpose, coverage role, scene-time range, camera setup, visible in-shot motion, blocking relationship, intended record duration, edit-in cue, edit-out cue, and bilateral editorial boundary records.

A generation segment is a technical slice of one editorial shot. It has a maximum effective duration of 10 seconds, a source-time interval, an entry/exit state, a bounded performance/camera interval, and a generation handoff.

The same editorial shot ID must survive technical splitting. A same-shot continuation is not an editorial cut.

### 3.2 Three time domains

Every shot and boundary must distinguish:

1. `scene_time`: performance/action time in the fictional scene. Multiple coverage shots may overlap the same scene-time range.
2. `source_time`: time inside generated source media and its generation segments.
3. `record_time`: final editorial timeline time after shot ordering, handles, audio overlaps, dissolves, and duplicate-endpoint removal.

Each shot/segment and EDL entry must carry the relevant scene-time phase IDs, source in/out, and record in/out. This prevents a master, insert, and reaction from being misread as three consecutive story events and supports genuine cuts on action.

### 3.3 Typed scene geography and action axes

Create a model-neutral scene-space contract before camera validation:

```yaml
scene_geography:
  world_id: SC01_WORLD
  zones:
    - {zone_id: doorway_interior, semantic: entrance, adjacency: [counter_area]}
    - {zone_id: tub_side, semantic: bathing_area, adjacency: [counter_area, mirror_wall]}
  anchors: [door, tub, mirror, counter]
  visibility:
    - {from_zone: doorway_interior, reveals: [door, counter_area]}
    - {from_zone: tub_side, reveals: [tub, mirror_wall]}
  geometry_provenance: declared_and_reference_observed
  unknown_regions: []
  action_axes:
    - {axis_id: AXIS_SC01_SUBJECT_SPACE, subject: protagonist, object: tub, active_scene_time: [0, 64]}
  reference_views:
    - {asset_id: ASSET_BATHROOM_01, reveals: [mirror_wall, tub_side], scope: environment_style}
```

The initial implementation should use symbolic zones and typed relationships rather than false metric precision. Geometry must record whether it is observed, user-declared, inferred, or unknown.

If a new viewpoint exposes an unseen side of the environment, the plan must declare an uncovered-geometry risk or request an approved additional reference view. It must not invent hidden architecture.

### 3.4 Structured camera setup and in-shot motion

Separate an offscreen setup change from visible camera motion:

```yaml
camera_plan:
  setup_id: CAM_SETUP_03
  coordinate_space: SC01_WORLD
  setup:
    position_zone: tub_side
    orientation: {angle: controls_three_quarter, height: low_eye_level, pitch: level, roll: 0}
    optics: {lens_class: short_telephoto, focal_length_equivalent_mm: 65, zoom: none}
    composition: {size: insert, headroom: minimal, lead_room: hand_action}
  in_shot_motion:
    type: static
    timing: [0.0, 3.0]
  axis:
    axis_id: AXIS_SC01_SUBJECT_SPACE
    camera_side: side_a
    crossing: none
```

For a visible moving shot:

```yaml
camera_plan:
  setup_id: CAM_SETUP_04
  coordinate_space: SC01_WORLD
  setup:
    position_zone: counter_area
    orientation: {angle: three_quarter_right, height: eye_level, pitch: level, roll: 0}
    optics: {lens_class: normal, focal_length_equivalent_mm: 40, zoom: none}
    composition: {start_size: medium_wide, end_size: medium, lead_room: movement_direction}
  in_shot_motion:
    type: dolly_arc
    keyframes:
      - {source_time: 0.0, position_zone: counter_area, look_at: subject_upper_body}
      - {source_time: 7.0, position_zone: tub_side, look_at: subject_face}
    direction: forward_left
    distance_class: moderate
    rig_character: smooth_observational_track
    motivation: follow_subject_into_space
    orientation_tracking: preserve_eyeline_and_lead_room
```

The model must distinguish:

- `setup`: where the camera is placed after an editorial cut, with no implied physical path;
- `in_shot_motion`: visible translation and/or orientation change within a shot;
- `orientation`: pan, tilt, roll, angle, height, and look-at target;
- `optics`: lens, zoom, focus, depth, and focus transition;
- `composition`: shot size, framing, headroom, lead room, and foreground elements;
- `subject_blocking`: performer/prop movement, staged separately from camera motion;
- `axis`: action line, camera side, and explicit crossing/reset strategy.

A coordinated dolly-and-pan is one motivated camera operation. A new camera position after a cut requires a setup and editorial reason, but no interpolated path.

The 180-degree rule is contextual rather than a global fixed-camera rule. Camera relocation is allowed while remaining on the established side of the active action axis. Crossing requires an explicit visible crossing, neutral/on-axis reset, re-establishing shot, cutaway reset, or declared disorientation. The 30-degree rule is an anti-jump-cut heuristic with motivated exceptions.

### 3.5 Blocking and continuity state

Scene Performance owns what the performer does, why, action order, dialogue, prop/hand state, and physical state changes. Storyboard owns spatial staging of that approved performance: marks/zones, facing, screen path, eyeline target, foreground/background relation, entrances/exits, and timing relative to the camera.

Use a structured staging track with stable entity IDs, performance-beat IDs, prop IDs, zone IDs, and scene/source-time references.

Continuity must represent invariants and expected change rather than blanket locks:

```yaml
continuity_state:
  invariants: [character_identity, room_architecture, lighting_direction]
  entry_snapshot: {wardrobe: clothed, wetness: dry, prop_state: basket_carried}
  expected_deltas: [wetness_progression, wardrobe_transition, prop_release]
  exit_snapshot: {wardrobe: towel_wrap, wetness: towel_dried}
  forbidden_deltas: [identity_redesign, room_relayout, unexplained_screen_direction_flip]
```

Reference binding must support property-level scope, timeline scope, and strength. An environment reference must not silently become a fixed camera reference. A camera-composition reference is hard only when explicitly declared hard.

### 3.6 Bilateral editorial boundaries and generation handoffs

Editorial boundaries are first-class records between two shots:

```yaml
editorial_boundary:
  boundary_id: EB_SC01_04
  from_shot_id: SH04
  to_shot_id: SH05
  mechanism: cut
  motivations: [reaction, eyeline]
  action_match:
    outgoing_phase: hand_reaches_control
    incoming_phase: hand_contacts_control
  visual_match: null
  audio_transition: {type: l_cut, overlap_frames: 18}
```

Keep mechanisms limited to `cut`, `dissolve`, and `fade`. Treat action, reaction, eyeline, match, and similar values as motivations or constraints; they may coexist. `end` is a timeline terminator, not a transition between two shots.

Generation handoffs are separate:

- `independent`: no pixel dependency;
- `same_shot_continue`: approved predecessor endpoint becomes the successor entry;
- `endpoint_bridge`: downstream-generated interpolation between approved endpoints;
- `reference_reestablish`: continuity/reference state reused without predecessor pixels;
- `terminal`: no successor.

Continuation suitability must support moving endpoints. Replace a universal stable-tail requirement with a mode-specific contract:

- identity and geometry coherent;
- exposure and composition usable;
- intended action and camera-motion phase known;
- camera path direction/tangent recorded where applicable;
- no accidental blur or occlusion;
- controlled intentional motion permitted;
- successor entry reproduces the approved motion phase;
- no visible settle unless creatively planned.

Keyframe Handoff Builder and QC must jointly support moving continuation endpoints. If the installed capability cannot continue controlled motion reliably, preflight must report that limitation and block or request a creative revision; it must not force a pause into the shot.

## 4. Implementation work packages

Each work package ships its schemas, validators, fixtures, and contract tests together. Downstream work starts only after its input contract is frozen.

### WP0A — Vocabulary, versions, boundaries, and time domains

Owners: `storyboard-director`, `production-orchestrator`
Priority: P0
Depends on: none

Steps:

1. Add explicit v1/v2 schema and artifact versions.
2. Add shared definitions for scene-time, source-time, record-time, editorial shots, editorial boundaries, generation segments, and generation handoffs.
3. Replace segment-level transition ambiguity with bilateral editorial and generation boundary records.
4. Make `end` consistent as a terminator across storyboard, orchestrator, compiler, post, and validators.
5. Reject mixed legacy opaque and structured fields in v2 artifacts.

Acceptance:

- A 24-second uninterrupted shot becomes three or more segments with one shot ID and no editorial cut.
- Three independent 4-second shots remain three editorial shots even when each uses one generation job.
- Overlapping scene-time coverage does not duplicate or skip the underlying performance event.
- A cut during controlled motion is valid without a continuation tail.
- Continuation without a suitable approved endpoint fails.
- A bridge without both approved endpoints fails.

### WP0B — Scene geography, continuity state, and staging ownership

Owners: `reference-canon-manager`, `scene-performance-writer`, `storyboard-director`
Priority: P0
Depends on: WP0A

Steps:

1. Add typed scene geography: zones, anchors, adjacency, visibility, entrances, exits, obstacles, mirrors, reference views, provenance, unknown regions, and active axes.
2. Add structured storyboard staging linked to Scene Performance beat IDs rather than adding camera fields to Scene Performance.
3. Add continuity invariants, entry/exit snapshots, expected deltas, and forbidden deltas.
4. Add property-level, timeline-scoped, strength-scoped reference bindings.
5. Add uncovered-geometry risk and approved extra-reference routing.

Acceptance:

- A camera setup referring to an unknown zone fails or requests an explicit reference-view decision.
- Identity, room architecture, lighting, props, and state changes are independently traceable.
- Wetness and wardrobe progression can change according to approved beats without being misclassified as drift.
- Storyboard can stage an approved performance without rewriting its action or outcome.
- Multiple camera positions can reuse the same character and environment references.

### WP0C — Camera setup, visible motion, optics, blocking, and axes

Owner: `storyboard-director`
Priority: P0
Depends on: WP0B

Steps:

1. Add `camera_plan` schema with setup, in-shot motion, orientation, optics, composition, axis, motivation, and risk.
2. Require paths only for visible in-shot motion; do not invent paths for offscreen setup changes after cuts.
3. Add camera keyframes, look-at targets, timing, movement character, focus/depth intent, and segment interval references.
4. Allow camera relocation and coupled movement while retaining a one-dominant-operation generation-risk rule.
5. Add explicit axis crossing/reset strategy and viewpoint-geometry coverage checks.

Acceptance:

- Doorway-to-tub relocation passes as a new setup after a cut.
- A continuous doorway-to-tub dolly arc passes with position/orientation keyframes.
- Dolly-plus-pan passes as one motivated camera operation.
- Dolly, pan/tilt, orbit/arc, zoom, and reframing remain distinguishable.
- An unexplained axis flip fails; a declared motivated crossing passes.
- Fixed-camera/no-lens-change text cannot claim an unexplained close-up-to-medium change.

### WP1A — Feature-film coverage and visual grammar

Owner: `storyboard-director`
Priority: P1
Depends on: WP0C

Steps:

1. Draft scene geography, action axes, entrances, exits, eyelines, and audience information changes.
2. Add scene-level visual strategy: dramatic viewpoint, lens palette, movement doctrine, depth strategy, coverage map, shot progression, and pacing intent.
3. Design coverage before generation segmentation: establishing/master, moving master, singles, over-the-shoulders, inserts, reactions, eyeline shots, and cutaways when justified.
4. Give each shot one dramatic/editorial purpose and bilateral edit-in/edit-out reasons.
5. Permit variable shot duration, overlapping scene-time coverage, long takes, sparse coverage, and deliberate stylistic exceptions.
6. Split only after shot order and camera intent are approved. Preserve the camera interval and motion phase through same-shot splits.

Acceptance:

- Mechanically uniform one-beat/equal-duration coverage fails unless explicitly marked as intentional observational style.
- Every visible camera relocation or major in-shot move has motivation, path/keyframes where applicable, and risk.
- A moving master can span multiple plot/performance phases.
- A long shot can split without introducing an editorial cut or artificial settle.
- Static observation remains valid when its purpose and style are declared.

### WP1B — Editorial EDL, animatic, sound map, and preflight

Owners: `animatic-previs-planner`, `production-preflight-reviewer`, `sound-dialogue-planner`
Priority: P1
Depends on: WP1A

Steps:

1. Add an editorial-intent EDL and retain a separate generation-segment assembly map.
2. Record scene-time phases, source in/out, record in/out, handles, boundary mechanisms, motivations, and overlap runtime math.
3. Keep the pre-storyboard Sound Planner artifact focused on dialogue, effects, ambience, motifs, and music intent.
4. Add a post-storyboard editorial sound map for boundary carry, J-cuts, L-cuts, overlaps, room tone, pre-roll, post-roll, and synchronization. Animatic owns timing checks; Post Editor conforms approved intent to actual media.
5. Add preflight checks for coverage, camera geometry, motivated movement, impossible reframing, axis crossing, edit motivation, time-domain consistency, and shot/segment separation.

Acceptance:

- The paper edit shows the intended film sequence independently of generation job count.
- Segment timing remains <=10 seconds while editorial shot timing may be longer.
- Master, insert, and reaction shots can overlap scene-time without duplicating story events.
- J-cuts and L-cuts validate picture and audio boundaries independently.
- Coverage gaps and unexplained camera jumps are reported before human plan review.
- Preflight never rewrites shots, camera intent, sound intent, or approval state.

### WP2 — Segmentation, moving handoffs, compilation, DAG, and execution

Owners: `keyframe-handoff-builder`, `minimax-h3-adapter`, `comfyui-workflow-compiler`, `render-orchestrator`, `production-orchestrator`
Priority: P2
Depends on: WP1B and frozen camera/boundary schemas

Steps:

1. Compile only the approved camera-path interval and state snapshot for each generation segment.
2. Preserve source-field traceability for camera setup, motion keyframes, orientation, optics, composition, blocking, and handoff suitability.
3. Support moving continuation endpoints when the frozen capability profile proves support; otherwise block before compilation or request a creative revision.
4. Maintain separate editorial timeline and generation dependency DAGs.
5. Keep independent cuts parallelizable, continuation serialized, endpoint bridges dependent on both endpoints, and reference re-establish branches pixel-independent.
6. Preserve approval/hash gates and exact endpoint lineage.

Acceptance:

- H3 cannot silently change lens, path, angle, shot boundary, or transition.
- H3 receives the segment camera interval rather than the entire shot as ambiguous prose.
- Adjacent same-shot intervals reconstruct the approved camera path without a pause or jump.
- A controlled moving endpoint passes continuation suitability; accidental blur or geometry drift fails.
- Unsupported compound motion blocks at capability review without changing the storyboard.
- Technical resegmentation invalidates affected packets, jobs, endpoints, renders, QC, post, and delivery while preserving unaffected creative approvals.

### WP2B — QC, repair, conform edit, and final-QC propagation

Owners: `continuity-qc-supervisor`, `repair-director`, `post-editor`, `production-orchestrator`
Priority: P2
Depends on: WP2

Steps:

1. Separate camera-path QC, same-shot segment-seam QC, editorial-cut QC, and final assembly QC.
2. Replace universal stable-tail assumptions with mode-specific handoff suitability.
3. Allow a moving cut candidate with a valid editorial handle while continuing to reject accidental blur, occlusion, or geometry failure.
4. Make repair changes from cut to continuation, or vice versa, return to creative plan review.
5. Keep Animatic’s editorial-intent EDL distinct from Post Editor’s conform/final EDL using actual source revisions and handles.
6. Preserve approved source bytes and route every repaired/revised result through new QC.

Acceptance:

- Final QC distinguishes shot-grammar failure from generation-seam failure.
- A cut does not require a motionless endpoint.
- A continuation requires suitable motion phase, identity, geometry, and successor-entry compatibility.
- Post realizes approved transitions without inventing coverage or camera intent.
- A creative transition change invalidates the correct downstream closure and requires new approval.

### WP3 — Validators, migration, fixtures, and documentation

Owners: shared validation and test suites
Priority: P3
Depends on all prior contract versions

Scripts and validators:

- Add `skills/storyboard-director/scripts/validate_storyboard.py` for scene geography, camera setup/motion, staging, time domains, coverage, axes, bilateral boundaries, handoffs, and traceability.
- Extend `scripts/validate_production_system.py` for schema versions, enum parity, strict v2 objects, and ownership boundaries.
- Extend `scripts/validate_review_document.py` for shot-level EDL, segment assembly, source/record timing, camera traceability, and boundary completeness.
- Extend `skills/production-orchestrator/scripts/validate_package.py` for two-graph topology, invalidation scope, moving-handoff capability gates, and transition dependency rules.

Migration requirements:

- Implement strict v1 and v2 readers.
- Provide deterministic v1→v2 migration in dry-run/new-revision mode.
- Map unresolved opaque camera fields to `migration_review_required`; never guess.
- Reject mixed legacy and structured authoritative fields.
- Use `additionalProperties: false` on authoritative v2 objects.
- Never reuse an old approval hash for migrated content.
- Validate cross-artifact IDs, hashes, timebases, boundaries, and source-field traceability.

Fixtures and tests:

- Keep current PRJ01 as a valid historical v1 artifact and a failing v2 cinematic-admission fixture.
- Add a sanitized real-cinematic fixture under `examples/` with masters, inserts, reactions, overlapping scene-time coverage, a moving master, a new offscreen setup, a motivated axis crossing, independent cuts, a same-shot moving continuation, and one J/L audio transition.
- Ship unit, contract, and integration tests with each work package rather than deferring all tests to WP3.
- Add byte-stable canonical serialization tests for camera plans, boundary records, continuity states, and source maps.

## 5. Corrected PRJ01-style fixture

This is a validation fixture, not a replacement production plan. Every boundary is bilateral and exact:

| Shot | Camera/setup intent | Scene-time relationship | Editorial boundary | Generation relationship |
|---|---|---|---|---|
| SH01 | Doorway master, eye-level normal lens, short visible dolly following entrance | Establishes the room and overlaps the opening performance phase | `mechanism: cut`, motivation: action complete | `independent` |
| SH02 | New low tub-side setup, longer-lens insert on controls/hand action; in-shot motion static | Overlaps SH01’s action phase rather than creating a new event | `mechanism: cut`, motivations: action + insert | `independent` |
| SH03 | Rear-wall-side medium profile, lateral track following movement | Covers the same movement phase from a new viewpoint | `mechanism: cut`, motivation: eyeline | `independent` |
| SH04 | Moving master arcs from counter toward tub-side; coordinated pan preserves eyeline | Covers the transition and settle phases in one editorial shot | No editorial boundary inside the shot | 14 seconds split into two `same_shot_continue` segments with moving handoff suitability |
| SH05 | New close reaction setup on the same axis side, static longer lens | Overlaps the end of SH04’s reaction phase | `mechanism: cut`, motivations: reaction + eyeline | `independent` |
| SH06 | Wider mirror composition from a deliberate new position | Reuses the relevant state without duplicating the performance event | `mechanism: cut`, motivation: declared visual match or eyeline | `independent` |
| SH07 | Medium three-quarter tracking shot with a motivated reveal | Covers the next approved performance phase | `mechanism: cut`, motivation: action progression | `independent` |
| SH08 | Wide pull-back as the subject exits; settle on empty space | Terminal closing phase | No outgoing boundary; editorial timeline terminator | `terminal` |

Across the fixture, identity, environment geometry, persistent props, lighting, wardrobe/state, eyelines, and active action axis remain traceable. Camera position, viewpoint, height, lens, and framing change intentionally. No boundary uses the vague phrase “match or eyeline.”

## 6. Approval, migration, and invalidation

This is a shared-skill change, not an automatic rewrite of PRJ01 production outputs.

1. Approve each revised schema family, skill contract, validator, fixture, and migration tool as a versioned development revision.
2. Run repository contract/unit/integration validation before migrating any production plan.
3. Treat camera intent, editorial shot order, coverage, editorial mechanisms/motivations, and generation topology changes as creative changes requiring plan review and human approval.
4. Permit technical segment re-splitting without creative reapproval only when editorial shot identity, camera path, boundary semantics, assembled timing, and continuity intent remain unchanged.
5. Even technical resegmentation must invalidate and regenerate affected prompt packets, jobs, endpoints, renders, QC, post, and delivery artifacts as appropriate.
6. Preserve all existing approved artifacts immutably; create superseding revisions rather than overwrite.
7. Migrate PRJ01 only as a new plan revision after the shared skills pass validation and the revised plan passes preflight.
8. Do not change H3 modes, workflow graphs, render settings, or models as part of the storyboard-model change unless capability review finds a separate blocker.
9. Maintain a field-to-artifact invalidation matrix covering storyboard, animatic, sound map, preflight, plan, H3, keyframes, workflows, DAG, renders, QC, repair, post, and delivery.

## 7. Completion definition

The development is complete when:

- a feature-film shot plan can contain motivated camera relocation and viewpoint changes;
- offscreen setup changes are distinct from visible in-shot camera paths;
- scene-time, source-time, and record-time remain consistent across overlapping coverage and final EDL conform;
- the same plan can contain long takes split into technical segments without invented editorial cuts or forced settling;
- moving handoffs are capability-gated rather than creatively flattened;
- references preserve character, environment, and evolving state without silently fixing the camera;
- editorial boundaries and generation handoffs are independently represented and validated;
- sound intent and post-storyboard J/L boundary behavior remain traceable;
- H3, keyframe, compiler, render, QC, repair, orchestration, and post preserve approved camera/shot intent without authoring new decisions;
- PRJ01 remains valid as a historical v1 artifact but fails v2 cinematic admission for repetitive one-beat/equal-duration construction, missing camera setups, opaque paths, boundary conflation, and universal stable exits;
- the corrected cinematic fixture passes all contract and integration tests;
- all changed skills, schemas, scripts, and tests pass repository validation;
- no approved production artifact was overwritten or silently reinterpreted.

Implementation begins only after this revised plan is approved. The first implementation stage is WP0A–WP0C; no render or production migration is authorized by this document.
