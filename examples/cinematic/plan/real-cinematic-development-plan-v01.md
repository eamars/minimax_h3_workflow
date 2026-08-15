# Real-Cinematic Production Skills Development Plan

Status: draft_for_external_review
Version: v01
Scope: shared storyboard, planning, validation, compilation, QC, orchestration, and post-production contracts
Reference failure case: `projects/PRJ01`
Implementation status: planning only; no production artifacts or validated plans are to be changed by this document

## 1. Goal

Make the production system capable of planning and preserving a real cinematic scene: deliberate coverage, motivated camera placement and movement, readable geography, editorial rhythm, continuity, and long takes where appropriate.

The system must design the movie first and divide it into model-sized generation work second. A ten-second generation limit is a technical constraint; it must not become the story's shot grammar.

“Real cinematic” means that the plan can express, validate, and preserve all of the following independently:

- editorial shots and their dramatic purposes;
- camera position and physical path;
- viewpoint, angle, height, orientation, and axis relationship;
- lens, focus, framing, and composition;
- actor blocking and subject movement;
- editorial cuts, dissolves, match cuts, and audio overlaps;
- technical generation segmentation and endpoint dependencies;
- character, environment, prop, wardrobe, lighting, wetness, eyeline, and screen-direction continuity.

The goal is not to force a generic “Hollywood” formula. Static observation, a long take, a jump cut, an axis crossing, or sparse coverage must remain valid when explicitly motivated and traceable.

## 2. Current failure baseline

The current system has the intended hierarchy `project → sequence → scene → shot → generation segment`, but camera and transition semantics are mostly opaque strings.

- `storyboard-director` requires camera size, angle, height, lens feel, position, depth, axis, horizon, and one dominant move or static camera, but the schema does not model those properties.
- `generationSegment.dominant_camera_move` is only a non-empty string; timeline camera entries are also unstructured.
- `transition_to_next` mixes editorial meaning (`cut`, `match_cut`, `dissolve`) with technical generation relationships (`continue`, `bridge`).
- PRJ01 turns eight plot beats into eight equal 8-second segments and eight independent cuts. Its director treatment limits the camera to static or slow push-in/pull-back behavior and globally repeats a fixed axis.
- PRJ01 does not identify camera positions, camera paths, shot coverage, edit motivation, or the difference between a shot boundary and a generation boundary.
- The separate 10-second storyboard prompt asks for a close-up and then a medium mirror composition while forbidding cuts, orbit, lens change, and meaningful camera relocation.
- Existing tests emphasize duration caps, basic transition presence, and endpoint stability. They do not test camera geometry, coverage, editorial motivation, axis reasoning, or shot/segment separation.

PRJ01 must remain available as a negative fixture. It should not be silently rewritten as part of this plan.

## 3. Target architecture

The authoritative planning sequence becomes:

```text
Canon and scene state
  → scene geography and action axes
  → feature-film shot and coverage plan
  → editorial timeline and transitions
  → ≤10-second generation segmentation
  → generation-handoff dependency graph
  → H3 compilation
  → render and QC
  → post realization and final QC
```

### 3.1 Editorial shot versus generation segment

An editorial shot owns the audience-facing cinematic decision. It has a purpose, coverage role, camera plan, blocking relationship, intended duration, edit-in cue, edit-out cue, and editorial transition.

A generation segment is a technical slice of one editorial shot. It has a maximum effective duration of 10 seconds, an entry/exit state, a bounded performance arc, a camera-path interval, and a generation handoff.

The same editorial shot ID must survive technical splitting. A same-shot continuation is not an editorial cut.

### 3.2 Structured camera plan

Add a model-neutral camera plan referenced by shots and copied into segment intervals by source reference, not by creative reauthoring.

```yaml
camera_plan:
  setup_id: CAM_SETUP_03
  coordinate_space: SC01_WORLD
  position:
    start_zone: doorway_interior
    end_zone: tub_side
    path:
      type: dolly_arc
      direction: forward_left
      distance_class: moderate
      motivation: follow_subject_into_space
  orientation:
    start: {angle: three_quarter_right, height: eye_level, pitch: level, roll: 0}
    end: {angle: profile_right, height: eye_level, pitch: slight_down, roll: 0}
    look_at: subject_upper_body_to_face
    tracking: preserve_eyeline_and_lead_room
  optics:
    lens_class: normal
    focal_length_equivalent_mm: 40
    zoom: none
    focus_target: subject
    focus_transition: hold
  composition:
    start_size: medium_wide
    end_size: medium
    headroom: normal
    lead_room: movement_direction
  axis:
    axis_id: AXIS_SC01_SUBJECT_SPACE
    camera_side: side_a
    crossing: none
  motivation: follow the subject while revealing the room relationship
  risk: medium
```

The first implementation should prefer symbolic zones and relational descriptors over false metric precision. Optional normalized coordinates may be added later when a project has a validated scene coordinate system.

The camera model must distinguish:

- `position/path`: physical camera relocation and translation;
- `orientation`: pan, tilt, roll, angle, height, and look-at changes;
- `optics`: lens, zoom, focus, and depth intent;
- `composition`: shot size, framing, headroom, lead room, and foreground elements;
- `subject_blocking`: actor/prop movement, owned by the storyboard but separate from the camera;
- `axis`: action line, camera side, and explicit crossing/reset strategy.

A coordinated dolly-and-pan is one motivated camera operation. It must not be rejected merely because it changes both position and orientation.

### 3.3 Continuity locks

Continuity is a separate state object. It must preserve, as applicable:

- subject identity and design;
- environment architecture and persistent props;
- lighting direction and scene time;
- wardrobe, wetness, and other state progressions;
- gaze, eyelines, screen direction, and action axis;
- reflection geometry and required mirror relationships;
- validated reference roles and binding strengths.

An environment reference must not silently become a fixed camera reference. A camera-composition reference is hard only when the user or project explicitly declares it hard; otherwise it may be style, framing, or soft guidance.

### 3.4 Independent editorial and generation transitions

Introduce two separate concepts.

Editorial transition types:

- `hard_cut`;
- `cut_on_action`;
- `reaction_cut`;
- `eyeline_cut`;
- `match_cut` with named outgoing and incoming motifs;
- `dissolve` with duration, intent, and audio policy;
- `fade`;
- `end`.

Generation handoff types:

- `independent`;
- `same_shot_continue` using the validated effective predecessor tail;
- `endpoint_bridge` using validated source and target endpoints;
- `reference_reestablish` using the continuity/reference state without pixel dependency;
- `terminal`.

Rules:

- A hard cut may require strong narrative and state continuity even though it has no pixel dependency.
- A cut may occur during controlled motion and needs a valid editorial cut point, not a motionless tail.
- `same_shot_continue` requires a stable validated tail and no visible editorial seam.
- `endpoint_bridge` requires both validated endpoints and a supported bridge path.
- A match cut is an editorial hard cut, not a generation continuation.
- A dissolve is post-production overlap and cannot claim physical or semantic continuity by itself.
- A transition-topology change remains a creative plan change requiring human validation.

## 4. Implementation work packages

### WP0 — Contract foundation: separate shots, transitions, and segments

Owners: `storyboard-director`, `production-orchestrator`
Priority: P0

Steps:

1. Add shared definitions for editorial shots, editorial transitions, generation handoffs, and structured camera plans.
2. Update `storyboard-package.schema.json`, `common-defs.schema.json`, `production-plan.schema.json`, and the handoff/transition manifests.
3. Preserve stable shot IDs across technical splits.
4. Add a migration path from the current `transition_to_next` field; do not silently reinterpret old validated artifacts.
5. Make `end` consistent across storyboard, orchestrator, compiler, post, and validation policies.

Acceptance:

- A 24-second uninterrupted shot becomes three or more segments with one shot ID and no editorial cut.
- Three independent 4-second shots remain three editorial shots even when each uses one generation job.
- A cut during controlled motion is valid without a continuation tail.
- A continuation without an validated stable tail fails.
- A bridge without both validated endpoints fails.
- A match cut without bilateral motifs fails.

### WP1 — Structured camera and axis model

Owners: `storyboard-director`, `reference-canon-manager`
Priority: P0

Steps:

1. Add `schemas/camera-plan.schema.json` or equivalent shared definitions.
2. Replace camera prose as the authoritative source with structured position, path, orientation, optics, composition, axis, motivation, and risk fields.
3. Allow camera relocation and coupled camera motion while retaining a one-dominant-operation risk rule per segment.
4. Make action-axis continuity contextual instead of a global fixed-camera rule.
5. Require explicit axis-crossing treatment: visible crossing, neutral/on-axis reset, re-establishing shot, cutaway reset, or declared disorientation.
6. Add 30-degree and jump-cut checks as heuristics with explicit motivated exceptions, not absolute cinematic laws.

Acceptance:

- Doorway-to-tub camera relocation passes while character, room, props, lighting, and state remain locked.
- Dolly-plus-pan passes as one motivated camera operation.
- Dolly, pan/tilt, orbit/arc, zoom, and reframing remain distinguishable.
- An unexplained axis flip fails.
- A declared, motivated axis crossing passes.
- A fixed-camera/no-lens-change description cannot claim an unexplained close-up-to-medium change.

### WP2 — Feature-film storyboard drafting grammar

Owner: `storyboard-director`
Priority: P1

Steps:

1. Draft scene geography, action axes, entrances, exits, eyelines, and important spatial relationships.
2. Identify dramatic beats and audience information changes.
3. Design coverage before generation segmentation: establishing/master, moving master, singles, over-the-shoulders, inserts, reactions, eyeline shots, and cutaways when justified.
4. Give each shot one dramatic/editorial purpose and an edit-in/edit-out reason.
5. Permit variable shot duration and long takes; do not infer one shot per plot beat or one equal-duration segment per beat.
6. Split only after shot order and camera intent are validated. Preserve a continuous camera path through same-shot splits.
7. Add coverage, camera progression, editorial rhythm, handles, and transition motivation to acceptance tests.

Acceptance:

- Mechanically uniform one-beat/equal-duration coverage fails unless explicitly marked as intentional observational style.
- Every camera relocation or major move has motivation, path, and risk.
- A moving master can span multiple plot beats.
- A long shot can split into continuation segments without introducing an editorial cut.
- Static observation remains valid when its purpose and style are declared.

### WP3 — Reference and continuity separation

Owner: `reference-canon-manager`
Priority: P1

Steps:

1. Keep identity, environment, style, wardrobe, props, state, and camera-composition roles distinct.
2. Add scope and binding strength for camera-composition references.
3. Prevent environment architecture references from acquiring fixed camera position/viewpoint unless explicitly declared.
4. Add camera/state continuity snapshots for shot entry, shot exit, and same-shot segment boundaries.
5. Preserve source hashes, role ordering, and immutable reference bytes.

Acceptance:

- The same character and room references can support multiple validated camera positions.
- A hard camera-composition reference remains binding when explicitly declared.
- A soft/style-only camera reference does not block a motivated relocation.
- Identity, environment, lighting, props, wardrobe/wetness, eyeline, and axis changes are independently traceable.

### WP4 — Animatic, preflight, and paper-edit support

Owners: `animatic-previs-planner`, `production-preflight-reviewer`
Priority: P1

Steps:

1. Add a shot-level EDL while retaining the segment-level assembly map.
2. Record editorial duration, handles, edit cues, shot order, and transition type separately from generation timing.
3. Add preflight checks for coverage sufficiency, camera geometry, motivated movement, impossible reframing, axis crossings, edit motivation, and shot/segment separation.
4. Allow intentional sparse coverage and long takes when explicitly declared.
5. Route each finding to the smallest upstream owner.

Acceptance:

- Paper edits show the intended film sequence independently of generation job count.
- Segment timing remains <=10 seconds while shot timing may be longer.
- Coverage gaps and unexplained camera jumps are reported before human plan review.
- Preflight does not rewrite shots or camera intent.

### WP5 — Downstream preservation and execution topology

Owners: `minimax-h3-adapter`, `continuity-qc-supervisor`, `production-orchestrator`, `post-editor`
Priority: P2

Steps:

1. Compile structured camera intent into deterministic H3 prose while preserving source-field traceability.
2. Prevent H3 compilation from adding, removing, or changing camera path, viewpoint, optics, shot boundaries, or editorial transitions.
3. Maintain two graphs: an editorial timeline/EDL and a generation dependency DAG.
4. Update orchestrator invalidation: creative camera, shot, or transition changes invalidate downstream planning/compilation/render/post artifacts and require revalidation; purely technical resegmentation may be versioned and revalidated without creative revalidation when assembled shot intent is unchanged.
5. Separate QC modes for camera-path quality, same-shot segment seams, editorial cuts, and final assembly.
6. Require exact stable tails only for continuation/bridge paths; allow cut candidates to retain moving exits when editorially valid.
7. Make Post Editor realize validated transitions without inventing coverage or camera intent.

Acceptance:

- Every compiled prompt camera statement maps to a structured source field.
- H3 compilation cannot silently change lens, path, angle, shot boundary, or transition.
- Independent cut branches have no false technical dependency.
- Continuation and bridge branches serialize behind the required endpoint validations.
- A cut with a non-motionless but editorially valid handle is accepted.
- Final QC distinguishes a shot-grammar failure from a generation-seam failure.

### WP6 — Validators, fixtures, migration, and documentation

Owners: shared validation and test suites
Priority: P2

Scripts and validators:

- Add `.agents/skills/storyboard-director/scripts/validate_storyboard.py` for structured camera, shot/segment, transition, axis, coverage, and traceability validation.
- Extend `scripts/validate_production_system.py` for new schemas, enum parity, and ownership boundaries.
- Extend `scripts/validate_cinematic_package.py` for shot-level EDL, segment assembly, camera traceability, and transition completeness.
- Extend `.agents/skills/production-orchestrator/scripts/validate_package.py` for two-graph topology, invalidation scope, and transition dependency rules.

Fixtures and tests:

- Keep current PRJ01 as a negative fixture.
- Add a sanitized real-cinematic fixture under `examples/` with masters, inserts, reactions, a moving master, a camera relocation, a motivated axis crossing, independent cuts, and a same-shot continuation.
- Add unit, contract, and integration tests for every WP0–WP5 acceptance condition.
- Add byte-stable canonical serialization tests for structured camera plans and source trace maps.
- Document the migration from v1 opaque camera/transition fields to the versioned structured model.

## 5. Corrected PRJ01-style camera fixture

This is a validation fixture, not a replacement production plan:

| Shot | Camera intent | Editorial transition | Generation relationship |
|---|---|---|---|
| SH01 | Doorway master, eye-level normal lens, short dolly following entrance | Hard cut after the entrance action | Independent |
| SH02 | New low position near the tub, longer-lens insert on the hand/controls | Cut on action | Independent |
| SH03 | Rear-wall-side medium profile, lateral track following movement | Eyeline cut | Independent |
| SH04 | Moving master arcs from the counter toward the tub-side position; coordinated pan maintains eyeline | No editorial cut inside the shot | 14 seconds split into two same-shot continuation segments |
| SH05 | New close reaction position on the same axis side, static longer lens | Reaction cut | Independent |
| SH06 | Wider mirror composition from a deliberate new position | Match or eyeline cut with declared motif | Independent |
| SH07 | Medium three-quarter tracking shot with a motivated reveal | Hard cut | Independent |
| SH08 | Wide pull-back as the subject exits; settle on the empty space | Terminal end | Independent |

Across the fixture, identity, environment geometry, persistent props, lighting, wardrobe/state, eyelines, and screen direction remain locked. Camera position, viewpoint, height, lens, and framing change intentionally.

## 6. Validation and change-control rules

This work is a shared-skill change, not an automatic rewrite of PRJ01 production outputs.

1. Validate the revised schemas, skill contracts, and validator fixtures as a development revision.
2. Run repository contract/unit/integration validation before any production plan migration.
3. Treat camera intent, editorial shot order, editorial transitions, and coverage as creative changes requiring plan review and human validation.
4. Permit technical segment re-splitting without creative revalidation only when the editorial shot, camera path, transition semantics, assembled timing, and continuity intent remain unchanged.
5. Preserve all existing validated artifacts immutably; create superseding revisions rather than overwrite.
6. Migrate PRJ01 only as a new plan revision after the shared skills pass validation and the new plan passes preflight.
7. Do not change H3 modes, workflow graphs, render settings, or models as part of the storyboard-model change unless a downstream capability review finds a separate blocker.

## 7. Completion definition

The development is complete when:

- a feature-film shot plan can contain motivated camera relocation and viewpoint changes;
- the same plan can contain long takes split into technical segments without invented editorial cuts;
- references preserve character, environment, and state continuity without silently fixing the camera;
- editorial transitions and generation handoffs are independently represented and validated;
- H3, QC, orchestration, and post preserve the validated camera/shot intent without authoring new decisions;
- PRJ01 fails the old short-video fixture tests and the corrected cinematic fixture passes;
- all changed skills, schemas, scripts, and tests pass the repository validation suite;
- no validated production artifact was overwritten or silently reinterpreted.

The next action after this draft is an independent SOL review of this exact document. Implementation begins only after that review is incorporated and the development plan is validated.
