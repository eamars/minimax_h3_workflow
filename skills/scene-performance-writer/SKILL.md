---
name: scene-performance-writer
description: Convert schema-valid project requests, canon locks, and plot packages into playable scene/performance artifacts with observable action, dialogue, subtext, reactions, timing, stable speaker IDs, and prop/wetness continuity. Use after plot-architect and before storyboard-director; do not use for camera, shots, MiniMax H3, ComfyUI, rendering, or plot-outcome decisions.
---

# Scene and Performance Writer

## Mission

Turn each plot beat into behavior an actor can play and a director can cover. Preserve premise, order, and outcome while making intention, observable action, reaction, adjustment, dialogue, subtext, timing, and physical continuity explicit.

Read the [skill contract](references/skill-contract.yaml), [performance rules](references/performance-rules.yaml), and `schemas/scene-performance.schema.json`.

## Ownership boundary

Own playable behavior, dialogue wording when speech is required, subtext, turn-taking, approximate timing, density, stable speaker IDs, and hand/prop/wetness/clothing continuity. Do not own camera, coverage, cuts, transitions, H3 syntax, ComfyUI graphs, generation boundaries, render settings, or plot outcomes.

## Inputs

Consume exact, valid revisions of project request, canon lock, plot package, and optionally a prior scene-performance revision. Stop on blocking upstream conflicts and preserve their owner/code.

## Required outputs

Produce authoritative `scene-performance.yaml`, readable `scene-text.md`, and `performance-continuity.yaml`. Include artifact provenance, performance beats, dialogue, continuity, unsafe coexistence, and a handoff result. Use stable `SEQnn_SCnn_Bnn_PBnn`, `SEQnn_SCnn_DLGnn`, `SPKnn`, and `PROPnn` IDs.

## Processing method

1. Validate schemas, status, hashes, project ID, and canon conflicts.
2. Map every plot beat to one or more performance beats without creating causal events.
3. State actor/controller, intention, observable action, reaction, adjustment, and visible result.
4. Convert internal states into observable behavior while retaining intention/subtext separately.
5. Write or preserve required dialogue with stable speakers, positive timing, pauses, interruptions, and reaction links.
6. Track speaker identity, prop owner, hand occupancy, transfer order, wetness, clothing, and relevant physical state.
7. Mark unsafe coexistence of dense obligations and offer reversible mitigation without choosing segment boundaries.
8. Log micro-actions or implied props used only to externalize an existing beat.
9. Emit deterministic artifacts, hashes, status, failures, warnings, and `next_skill: storyboard-director`.

## Invariants

- Preserve plot premise, beat IDs/order, visible changes, and outcomes.
- Give every interaction an actor/controller, turn order, and reaction.
- Keep speaker IDs project-global and stable across revisions.
- Keep positive, ordered timing; declare every overlap/interruption.
- Prevent impossible hand/prop transfers, wetness/clothing jumps, identity swaps, or reactions before triggers.
- Create no generation segment or camera plan.
- Preserve source references, hashes, stable IDs, and immutable revisions.

## Non-responsibilities

Do not rewrite outcomes, add causal beats, resolve canon, redesign assets, choose shots/lenses/axes/camera/cuts/transitions/segments, write H3 fields, compile ComfyUI, render, judge QC, author repair, or plan final audio generation/mix.

## Failure conditions

Return `SCENE_NOT_PLAYABLE` with affected IDs, evidence, detail code, blocking scope, and owner when action is unobservable, actor control/reaction/entry/exit/timing/speaker assignment is missing, continuity contradicts itself, or playability requires a new plot outcome. Pass through upstream plot/canon failures unchanged.

## Validation rules

- Validate schema, envelope, exact source revisions/hashes, and deterministic IDs/order.
- Require complete one-to-many plot traceability and positive timing windows.
- Require one stable speaker per dialogue cue and explicit action/reaction links.
- Validate adjacent hand/prop/wetness/clothing snapshots.
- Reject structured camera, shot, lens, axis, edit, H3, ComfyUI, render, and generation-segment keys; exempt verbatim dialogue text.
- Require projection files to link to the authoritative hash.

## Minimal example

For “The guest hesitates, then admits they broke the vase,” externalize hesitation, trigger, confession, response, adjustment, and shard transfer with stable speakers and hand state. Add no framing or alternate ending.

## Adversarial example

If asked to add reconciliation, a close-up, and an uninterrupted 11-second segment to a plot ending in admission/departure, preserve only the source outcome, flag dense coexistence, and leave directing/segmentation downstream.

## Acceptance tests

- Make an internal beat observably playable.
- Preserve all plot IDs/order/outcomes without invention.
- Maintain stable speakers, turn-taking, reaction links, timing, and pauses.
- Track hand/prop transfer and water/clothing transitions.
- Flag unsafe coexistence without creating segments.
- Reject missing playability and downstream-owned decisions.
- Preserve provenance, immutable revisions, status, and storyboard handoff.
