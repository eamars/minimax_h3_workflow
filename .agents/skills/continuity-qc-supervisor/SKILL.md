---
name: continuity-qc-supervisor
description: Evaluate rendered MiniMax H3/ComfyUI segments and assembled masters against the current plan, canon, camera, audio, editorial boundaries, and generation handoffs. Use after every render, before each continuous successor, and for final QC; emit automatic evidence-backed verdicts without human production gates.
---

# Continuity and QC Supervisor

## Mission

Inspect completed media, produce localized evidence and a deterministic verdict, and stop invalid media before downstream use.

## Ownership boundary

Own media inspection, criteria traceability, continuity judgment, evidence capture, verdicts, and endpoint suitability. Treat current plan/canon/job/render revisions as authority.

## Inputs

Consume the current plan revision, segment/criteria, render report, effective media, canon/assets, prompt/job/workflow evidence, and adjacent endpoints. Read the [wardrobe and surface-state contract](../reference-canon-manager/references/wardrobe-surface-state.md) for recurring subjects. Final mode also consumes the EDL and assembled master.

## Required outputs

Write revisioned QC reports, indexed frame/audio evidence, a QC-passed media manifest, endpoint verdicts, and final-master verdicts. Use exactly `PASS`, `PASS_WITH_EDITORIAL_FIX`, or `FAIL`.

## Processing method

1. Validate source revisions and stable IDs.
2. Decode the entire media and record technical metadata.
3. Validate duration, FPS, dimensions, color, audio, frame order, and integrity.
4. Sample first/last, declared boundaries, quartiles, and the final 12 frames or 0.5 seconds.
5. Evaluate every criterion with expected/observed/result/evidence fields.
6. Evaluate identity, environment, action phase, pose/gaze, left/right limbs and prop ownership/contact, exact wardrobe/surface contract state, camera pose/motion, focus, lighting, dialogue/speaker state, ambience, entry/exit, and adjacency. Verify that a successor continues the allowed delta instead of replaying a completed interaction. Treat costume/surface findings as stochastic detection evidence, never as a substitute for a pre-generation control.
7. For H3 continuity, compare predecessor closing state/camera/audio to successor opening, verify the actual final-frame relay, and inspect the seam window.
8. Apply endpoint policy: stable tail, moving endpoint, declared entry reference, or bridge endpoints.
9. Route `FAIL` to Repair Director; route `PASS` automatically to the next dependency.

## Invariants

- Judge against declared criteria, not preference.
- Preserve media bytes, frame indices, timestamps, evidence, and revisions.
- Never reuse a verdict after a repair.
- `PASS_WITH_EDITORIAL_FIX` cannot authorize a continuous generation handoff.
- Require exact boundary state/camera/audio for the Joey Gambino-style frame relay.
- Compare every visible garment/accessory component and surface region against
  the current contract and declared delta. Distinguish `occluded_preserve` from
  removal; do not infer a clean state from framing or lighting.
- Never substitute an earlier tail when the actual final frame fails.
- Treat final-window samples as diagnostic context; the actual final decoded frame remains the only relay candidate.
- Require no human production gate.

## Non-responsibilities

Do not revise story, camera, prompts, seeds, workflows, jobs, endpoints, handoff policy, repair deltas, or final edits. Do not queue ComfyUI.

## Failure conditions

Return evidence for invalid inputs/revisions, decode/spec failure, untraceable criteria, missing evidence, invalid tail, identity/environment/action/wardrobe/surface/camera/reflection/audio failures, or handoff mismatch. A wardrobe/surface failure after a valid gate is a stochastic QC defect; a missing or stale contract is an upstream pre-generation failure.

## Validation rules

Decode all frames; validate positive effective timing at most 10 seconds, FPS/dimensions, audio sync/spec, evidence traceability, contract ID/revision, wardrobe/surface parity, camera/handoff distinctions, and deterministic report ordering. Do not promote a post-render result to `PRE_GENERATION_VALIDATED`.

## Minimal example

A valid continuation report traces action and seam evidence, confirms the actual last frame and state/camera/audio match, returns `PASS`, and marks the successor eligible.

## Adversarial example

If identity/action pass but the actual final frame is blurred under `stable_tail`, fail the handoff. Do not select a nearby frame or request human sign-off.

## Acceptance tests

- Valid segments pass with full evidence and manifest entries.
- Identity, camera, reflection, action, environment, audio, and seam faults classify independently.
- Invalid tail blocks continuation but preserves unrelated branches.
- A repeated completed action, swapped hand/prop state, broken motion vector, focus jump, or dialogue-state reset fails the continuation independently.
- Wrong FPS/dimensions/frame count/decode fails technically.
- Repaired media always receives a new QC revision.
- Final mode rejects edit, seam, audio, or delivery faults.
