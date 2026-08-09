---
name: continuity-qc-supervisor
description: Evaluate rendered MiniMax H3 and ComfyUI video segments or assembled masters against approved production plans, canon locks, prompt/workflow records, audio requirements, and endpoint handoffs. Use after every completed render, before continuation, and for final QC to produce evidence-backed QC reports and immutable media manifests without authoring repairs.
---

# Continuity and QC Supervisor

## Mission

Evaluate each completed segment and final assembly against the approved plan. Produce deterministic localized evidence, a machine-readable verdict, and continuation eligibility. Stop invalid, stale, unsafe, or unsupported media before downstream use.

## Ownership boundary

Own media inspection, acceptance-criteria traceability, continuity judgment, evidence capture, verdicts, handoff-tail eligibility, and approved-media manifest entries. Treat the approved plan, canon lock, prompt packet, workflow record, render report, and adjacent approved endpoints as authoritative.

## Inputs

Require the approved plan/approval/hash; segment card and acceptance criteria; render report/QC intake; effective media and hash; extracted-frame manifest; canon/assets; prompt packet, ComfyUI job, workflow/model/node/seed record; adjacent endpoints for handoff mode; and approved-media manifest/edit decision list for final mode. Reject stale, missing, superseded, or mismatched inputs before creative inspection.

## Required outputs

Write new revisions only: `qc/<segment-id>_r<revision>.yaml`, deterministic `qc/evidence/<segment-id>/` plus index, `approved-media-manifest.yaml`, handoff verdict in handoff mode, and final QC/delivery gate in final mode. Reports validate against `schemas/qc-report.schema.json` and include subject, mode, verdict, severity, failures, and criteria traceability.

## Processing method

1. Verify approval, hashes, revisions, and stable IDs before inspection.
2. Inspect media with `scripts/inspect_media.py`, preferring PyAV from `ComfyUI/.venv`; record decoder version and inspection hash.
3. Validate decode, frame order, effective duration, FPS, dimensions, color metadata, audio presence/rate/channels, and integrity. Effective duration is positive and at most 10 seconds.
4. Sample first/last, each declared boundary ±1 frame, quartiles, and the final 12 frames or 0.5 seconds; hash every evidence item.
5. Evaluate every approved criterion with source ID, time range, expected, observed, result, and evidence IDs.
6. Evaluate plot/action/performance, identity/design, costume/props/environment/light/wetness, hands, reflections, camera/axis/horizon, dialogue/ambience/audio, entry/exit, adjacency, and technical specs.
7. For continuation, require approved predecessor media and a stable tail with no major/blocking failure. A cut candidate may still be continuation-ineligible.
8. Assign exactly `PASS`, `PASS_WITH_EDITORIAL_FIX`, or `FAIL`. The middle verdict is cut/post only and never continuation-eligible.
9. Route localized failure evidence to Repair Director without changing plan, prompt, seed, workflow, job, or media.
10. Evaluate repaired/revised output as a new QC revision; never reuse a prior verdict.

## Invariants

- Judge only against approved artifacts and criteria, not preference.
- Preserve bytes, paths, hashes, frame indices, timestamps, and provenance.
- Never overwrite approved reports, evidence, manifests, or media.
- Missing trace/evidence, stale hash, or decode failure blocks approval.
- `PASS_WITH_EDITORIAL_FIX` never authorizes continuation.
- QC never authors or applies repair, and every repaired output receives a new evaluation.
- Independent segments may run in parallel; continuation chains serialize.
- Final master cannot pass with a failed join, audio transition, or delivery criterion.

## Non-responsibilities

Do not revise story, performance, dialogue, camera, segmentation, H3 prompts, seeds, workflows, render jobs, endpoint extraction, repair deltas, editorial fixes, or delivery specs. Do not queue ComfyUI or approve your own repair.

## Failure conditions

Return evidence and affected IDs with: `QC_INPUT_INVALID`, `QC_PLAN_HASH_MISMATCH`, `QC_MEDIA_DECODE_FAILURE`, `QC_MEDIA_SPEC_FAILURE`, `QC_CRITERIA_UNTRACEABLE`, `QC_EVIDENCE_MISSING`, `QC_TAIL_APPROVAL_BLOCKED`, `QC_MANIFEST_CONFLICT`, `IDENTITY_DRIFT`, `ENVIRONMENT_DRIFT`, `ACTION_ORDER_FAILURE`, `CAMERA_FAILURE`, `REFLECTION_FAILURE`, `AUDIO_SYNC_FAILURE`, or `HANDOFF_MISMATCH`. Use `FINAL_EDIT_CONTINUITY_FAILURE` in final mode for Post Editor-owned assembly failures.

## Validation rules

Validate artifact envelopes, approval/hash, source revisions, and IDs. Decode every frame with PyAV; require positive duration at most 10 seconds, expected FPS/dimensions, ordered timestamps, and no missing frames. Validate audio duration/sync/rate/channels and unexplained restarts. Trace every criterion to evidence, localize failures, distinguish failure domains, and require stable tails without blur, occlusion, unfinished expression, uncontrolled fluid/smoke, fast pan, or ambiguous reflection. Canonical ordering must make identical evaluations byte-identical apart from lifecycle metadata.

## Minimal example

A valid handoff report for a 4-second segment traces its action criterion to frame evidence, records the effective media SHA-256, returns `PASS`, and sets `tail_status: approved` plus `continuation_eligible: true`.

## Adversarial example

A clip matches identity, action, and camera but ends blurred and occluded. Return `PASS_WITH_EDITORIAL_FIX` plus `QC_TAIL_APPROVAL_BLOCKED` or `HANDOFF_MISMATCH`, preserve it only as a cut candidate, and do not extract a substitute tail or approve its successor.

## Acceptance tests

- Valid segment passes with full traceability and immutable manifest entry.
- Identity, camera-axis, reflection, action, environment, and audio fixtures classify independently with localized evidence.
- Unstable tail stays a cut candidate but cannot continue.
- Over-cap/wrong FPS/dimensions/missing frames/decode errors fail technically.
- Missing criteria or stale plan hash fails before manifest/creative approval.
- Repaired revisions require new QC; final mode rejects join/audio/delivery continuity faults.
- Identical inputs yield canonically identical reports and evidence indexes.
