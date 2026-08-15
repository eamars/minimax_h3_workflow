---
name: sound-dialogue-planner
description: Create a schema-valid narrative audio plan from plot, playable-scene, canon, and request artifacts, then preserve it through a later editorial sound-boundary pass. Invoke for dialogue, voice-over, singing, music, voice references, strong sound motifs, or cross-segment audio continuity; assign speakers, cue categories, timing, bridges, voice continuity, and native-vs-post intent without choosing H3 syntax, camera, ComfyUI nodes, render settings, or plot changes.
---

# Sound and Dialogue Planner

## Mission

Produce the authoritative narrative sound plan: stable speakers, dialogue/voice-over/singing/ambience/effects/music cues, timing, cross-boundary behavior, voice continuity, and native-vs-post intent. Preserve upstream text, IDs, provenance, and ownership.

Read [sound rules](references/sound-rules.yaml), the [skill contract](references/skill-contract.yaml), and `schemas/sound-plan.schema.json`.

## Ownership boundary

Own narrative audio intent, cue classification and scene-time timing, speaker registry, voice-reference role, diegetic status, ambience/effect/music continuity, audio bridges, and capability-agnostic native/post/hybrid intent. Animatic/Previs owns the post-storyboard mapping of those cues to editorial boundaries and record time. Do not own plot, performance wording, camera, segments, H3 syntax, workflows, rendering, QC, or final mix.

## Inputs

Consume revision-pinned project request, plot, scene-performance, canon/asset manifest when audio references exist, and optional scoped revision request. Reject superseded revisions and infer nothing from filenames.

## Required outputs

Produce `sound-plan.yaml`, `dialogue-cue-sheet.yaml`, and `voice-continuity.yaml`, all linked to exact source revisions. Use exactly: `dialogue`, `voice_over`, `singing`, `ambience`, `physical_effect`, `non_verbal_human`, `diegetic_music`, or `non_diegetic_music`. Give each cue a source, timing, acceptance tests, and `native_h3`, `post_production`, or `hybrid` intent.

## Processing method

1. Validate source envelopes, revisions, IDs, triggers, and audio reference roles.
2. Build stable speaker profiles from unambiguous upstream IDs and canon references.
3. Convert playable beats and supplied lines into cue records without rewriting.
4. Classify every cue using the deterministic category precedence.
5. Express finite nonnegative timing, tolerances, anchors, and pre/post-roll.
6. Define carried/reset/bridge audio state for the narrative events supplied by the storyboard; do not collapse editorial mechanisms and generation relationships into one transition field.
7. Record voice constraints and permissible variation from explicit/canon sources.
8. Select capability-agnostic native/post/hybrid intent with rationale and fallback.
9. Group cues by supplied scene/performance phase and declare cross-generation continuity without inventing editorial shot or segment IDs.
10. Sort deterministically and return ready or blocked status.

## Invariants

- Attribute each spoken/sung cue to one stable speaker or group.
- Keep all eight categories distinct.
- Preserve exact wording, beat IDs, and performance timing intent.
- Require finite positive timing and source provenance for every cue.
- Make cross-boundary audio behavior explicit.
- Treat editorial `cut`, `dissolve`, and `fade` semantics as downstream record-time decisions; never claim physical continuity from a dissolve or generation handoff.
- Resize or merge no segment; report supplied over-cap segments to Storyboard Director.
- Preserve declared upstream revisions.

## Non-responsibilities

Do not choose plot, outcomes, camera, blocking, shots, segments, edit order, H3 fields/mode, nodes/graphs, models/seeds, queue order, QC, repair, or final export settings. Do not inspect or alter source media.

## Failure conditions

Author `DIALOGUE_SPEAKER_UNCLEAR` for ambiguous attribution. Propagate `CANON_REFERENCE_CONFLICT`, `SCENE_NOT_PLAYABLE`, and `SEGMENT_TOO_LONG` with original owner/evidence. Stop the affected branch; never guess or silently downgrade routing intent.

## Validation rules

- Validate sound schema, artifact envelope, exact sources, and declared revision.
- Require unique speakers/cues and resolvable plot/performance links.
- Require category-specific fields, explicit music diegesis, timing bounds, tolerances, continuity rules, and one native/post/hybrid intent.
- Reject undeclared H3 fields, node IDs, seeds, model names, camera, or render settings.
- Record bypass instead of fabricating an empty plan when no trigger exists.

## Minimal example

For a silent shower vignette, emit continuous ambience, timed physical water effects, and only performance-supplied nonverbal breath. Add no dialogue, score, camera, or H3 syntax.

## Adversarial example

For one line with two plausible speakers, conflicting voice canon, and a same-shot generation handoff with no ambience carry state, block with attribution/canon evidence. Do not choose a speaker, alter the line, or invent an editorial boundary.

## Acceptance tests

- Produce deterministic schema-valid sound, cue, and voice artifacts.
- Distinguish all eight categories and stable speakers.
- Reject invalid timing and ambiguous attribution.
- Preserve ambience/voice state across declared transitions only.
- Include native/post/hybrid intent, rationale, and fallback without model syntax.
- Invalidate correct downstream artifacts when sound or sources change.
- Refuse validated overwrites and downstream-authority leakage.
