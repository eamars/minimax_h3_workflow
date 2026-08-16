---
name: scene-performance-writer
description: Convert schema-valid project requests, canon locks, and plot packages into playable scene/performance artifacts with observable action, dialogue, subtext, reactions, scene-time phases, stable speaker IDs, and prop/wetness continuity. Use after plot-architect and before storyboard-director; do not use for camera, spatial staging, shots, MiniMax H3, ComfyUI, rendering, or plot-outcome decisions.
---

# Scene and Performance Writer

## Mission

Turn each plot beat into behavior an actor can play and a director can cover. Preserve premise, order, and outcome while making intention, observable action, reaction, adjustment, dialogue, subtext, timing, and physical continuity explicit.

Read the [skill contract](references/skill-contract.yaml), [performance rules](references/performance-rules.yaml), the [wardrobe and surface-state contract](../reference-canon-manager/references/wardrobe-surface-state.md), and `schemas/scene-performance.schema.json`.

## Ownership boundary

Own playable behavior, dialogue wording when speech is required, subtext, turn-taking, approximate scene-time timing, density, stable speaker IDs, performance phase IDs, and hand/prop/wetness/clothing continuity. Do not own camera, geography, spatial staging, coverage, cuts, transitions, H3 syntax, ComfyUI graphs, generation boundaries, render settings, or plot outcomes.

## Inputs

Consume exact, valid revisions of project request, canon lock, plot package, and optionally a prior scene-performance revision. Stop on blocking upstream conflicts and preserve their owner/code.

## Required outputs

Produce authoritative `scene-performance.yaml`, readable `scene-text.md`, and `performance-continuity.yaml`. Include artifact provenance, performance beats, dialogue, scene-time phase ranges, continuity snapshots, unsafe coexistence, and a handoff result. Use stable `SEQnn_SCnn_Bnn_PBnn`, `SEQnn_SCnn_DLGnn`, `SPKnn`, and `PROPnn` IDs; storyboard later binds those phases to editorial shots.

## Processing method

1. Validate schemas, status, revisions, project ID, and canon conflicts.
2. Map every plot beat to one or more performance beats without creating causal events; assign ordered scene-time phase IDs.
3. State actor/controller, intention, observable action, reaction, adjustment, and visible result.
4. Convert internal states into observable behavior while retaining intention/subtext separately.
5. Write or preserve required dialogue with stable speakers, positive timing, pauses, interruptions, and reaction links.
6. Import the canonical `wardrobe_surface_contract` unchanged. Track speaker
   identity, prop owner, hand occupancy, transfer order, clothing components,
   region-level surface state, and relevant physical state as continuity
   invariants and expected scene-time deltas. Declare every permitted change;
   do not infer removal or cleaning from an occluded or out-of-frame region.
7. For every interactive hand action, assign stable per-limb IDs (`HAND_L`, `HAND_R`, or a subject-qualified equivalent) and emit before-contact, contact/transfer, and after-contact snapshots. Never use an unqualified “hand” as the only state for a door, selector, towel, garment, or handheld shower action.
8. If source material does not establish handedness or hardware geometry, declare the blocking choice in performance state without promoting it to canon; do not infer a handle side, hinge side, or swing direction from the image crop.
9. Mark unsafe coexistence of dense obligations and offer reversible mitigation without choosing segment boundaries.
10. Log micro-actions or implied props used only to externalize an existing beat.
11. Emit deterministic artifacts, revision references, status, failures, warnings, and `next_skill: storyboard-director`.

## Invariants

- Preserve plot premise, beat IDs/order, visible changes, and outcomes.
- Give every interaction an actor/controller, turn order, and reaction.
- Keep speaker IDs project-global and stable across revisions.
- Keep positive, ordered timing; declare every overlap/interruption.
- Prevent impossible hand/prop transfers, wardrobe/surface-state jumps,
  identity swaps, or reactions before triggers. Carry the full opening and
  closing wardrobe/surface snapshots for every phase boundary.
- Require an authoritative two-sided limb state in every continuity snapshot. A prop or fixture state may change only across an explicit contact/transfer sequence with a declared owner and adjacent snapshots.
- Keep canon uncertainty separate from performance blocking: a declared left/right choice may control the actor, but it cannot silently canonize unknown door hardware or room geometry.
- Create no geography, spatial staging, editorial shot, generation segment, or camera plan.
- Preserve source references, stable IDs, and declared revisions.

## Non-responsibilities

Do not rewrite outcomes, add causal beats, resolve canon, redesign assets, choose shots/lenses/axes/camera/cuts/transitions/segments, write H3 fields, compile ComfyUI, render, judge QC, author repair, or plan final audio generation/mix.

## Failure conditions

Return `SCENE_NOT_PLAYABLE` with affected IDs, evidence, detail code, blocking scope, and owner when action is unobservable, actor control/reaction/entry/exit/timing/speaker assignment is missing, a limb is undefined, a prop contact has no adjacent snapshots, a wardrobe/surface contract is missing or changes without a declared transition, continuity contradicts itself, or playability requires a new plot outcome. Pass through upstream plot/canon failures unchanged. Use detail codes `LIMB_STATE_UNDEFINED`, `PROP_CONTACT_SNAPSHOT_MISSING`, `HAND_ASSIGNMENT_CONFLICT`, `WARDROBE_SURFACE_STATE_MISSING`, `SURFACE_STATE_TRANSITION_UNDECLARED`, or `UNKNOWN_HARDWARE_USED_AS_CANON` where applicable.

## Validation rules

- Validate schema, envelope, exact source revisions, and deterministic IDs/order.
- Require complete one-to-many plot traceability and positive timing windows.
- Require one stable speaker per dialogue cue and explicit action/reaction links.
- Validate adjacent hand/prop/wardrobe/surface-state snapshots, including the
  full contract ID/revision, explicit deltas, and occlusion semantics.
- Validate `limb_states` for stable IDs, left/right sides, legal states, explicit holding/contact targets, and no simultaneous incompatible ownership.
- Validate before/contact/after snapshots for every interactive action, including door opening/closing at entry and exit.
- Require scene-time phase ranges to be positive, ordered, and distinct from later source/record time.
- Reject structured camera, shot, lens, axis, geography, staging, edit, H3, ComfyUI, render, and generation-segment keys; exempt verbatim dialogue text.
- Require projection files to link to the authoritative revision.

## Minimal example

For “The guest hesitates, then admits they broke the vase,” externalize hesitation, trigger, confession, response, adjustment, and shard transfer with stable speakers and hand state. Add no framing or alternate ending.

## Adversarial example

If asked to add reconciliation, a close-up, and an uninterrupted 11-second segment to a plot ending in admission/departure, preserve only the source outcome, flag dense coexistence, and leave directing/segmentation downstream.

## Acceptance tests

- Make an internal beat observably playable.
- Preserve all plot IDs/order/outcomes without invention.
- Maintain stable speakers, turn-taking, reaction links, timing, and pauses.
- Track per-hand/per-limb prop transfers and water/clothing transitions.
- Reject an entry or exit door action that says only “open/close door” without a declared contacting limb, door state, release state, and adjacent snapshots.
- Flag unsafe coexistence without creating segments.
- Reject missing playability and downstream-owned decisions.
- Preserve provenance, immutable revisions, status, and storyboard handoff.
