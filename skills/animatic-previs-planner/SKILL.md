---
name: animatic-previs-planner
description: Convert a validated storyboard and optional sound plan or seed thumbnails into a schema-valid timed paper animatic, EDL, pacing/readability findings, and optional deterministic preview specification. Use after Storyboard Director and before Production Preflight without generating media or changing shots.
---

# Animatic and Previs Planner

## Mission

Convert a valid storyboard into a time-ordered paper animatic and pacing/readability analysis. Compute edit timing, action/reaction windows, audio cue placement, handles, and transition dependencies for preflight. Optionally specify—but never execute—a static preview.

Read the [timing rules](references/timing-readability-rules.yaml), [skill contract](references/skill-contract.yaml), and `schemas/animatic-plan.schema.json`.

## Ownership boundary

Own paper timing, EDL order, pacing/readability analysis, arithmetic, action/reaction coverage, cue placement checks, and optional preview specification. Preserve shots, segments, blocking, camera, handoffs, plot, canon, and sound intent. Report defects to owners; do not redesign.

## Inputs

Consume exact valid revisions of storyboard, project request/timebase, conditional sound plan, optional canon/asset/thumbnail metadata, and optional prior animatic revision. Reject stale or superseded sources.

## Required outputs

Return authoritative `animatic-plan.yaml`, `paper-edit.edl.yaml`, `pacing-review.yaml`, and optional `preview-spec.yaml`. Include shared envelope, intended runtime, handles, one timeline row per segment, pacing findings, paper edit, and machine status/affected IDs/next owner.

## Processing method

1. Validate envelopes, source hashes, IDs, status, and FPS/timebase.
2. Copy storyboard order and exact transition semantics.
3. Build a contiguous frame-quantized display timeline while retaining target seconds.
4. Mark readable entry, primary action, reaction/settle, and stable exit windows.
5. Join sound cue IDs and check their timing and carry policy.
6. Run deterministic runtime, gap/overlap, readability, audio, transition, and duration checks.
7. If requested, specify timestamped existing thumbnails/slates only; execute nothing.
8. Emit canonical artifacts and return review-ready only without blocking findings.

## Invariants

- Require every segment to be >0 and <=10 seconds; recommend shorter risk-heavy segments without splitting them here.
- Match intended runtime within one frame with no unexplained gap/overlap.
- Require readable entry, action after entry, necessary reaction, and stable exit.
- Require explicit continuation/bridge dependencies and reject unusable exits.
- Keep required cues within bounds and off the final frame unless expressly safe.
- Preserve stable IDs, source hashes, reference roles, and upstream decisions.
- Perform no generation, workflow compilation, media processing, or approval.

## Non-responsibilities

Do not invent or change plot, dialogue, performance, canon, camera, shots, segments, transitions, H3 modes, workflows, keyframes, renders, QC, repair, or post decisions.

## Failure conditions

Use shared codes and evidence. Block over-cap/overloaded segments, missing entry/unstable exit, unspecified handoff, out-of-range or discontinuous audio, purposeless/ambiguous upstream content, or runtime mismatch. Route each finding to the smallest owning upstream skill and never repair silently.

## Validation rules

- Validate animatic schema, metadata, IDs, hashes, and exact sources.
- Round half-up to integer frames; require positive frames, <=10*FPS, contiguous ranges, and runtime tolerance <=1/FPS.
- Validate transition dependencies, cue bounds/tolerances, declared audio carry, and conditional sound presence.
- Run deterministic fixture checks without media inspection.

## Minimal example

For 10 seconds at 24 FPS, map a 6-second continuation segment and a 4-second successor with entry/action/reaction/exit windows, 240 total effective frames, cue IDs in range, and sequential tail dependency. Render nothing.

## Adversarial example

For a 10.5-second segment with a cue at 10.5 and a request to shorten/use the raw tail, block with duration/audio/exit evidence and route changes to Storyboard/Sound owners. Do not trim, switch transition, or execute.

## Acceptance tests

- Pass a valid 8-second vignette.
- Reject 10.001 seconds without auto-splitting.
- Validate exact two-segment continuation timing/dependencies.
- Reject runtime gaps/overlaps, missing states, overload, out-of-range cues, and superseded sources.
- Keep preview specs deterministic, source-only, and side-effect-free.
