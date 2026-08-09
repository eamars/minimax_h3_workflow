---
name: keyframe-handoff-builder
description: Prepare exact, approved endpoint images and deterministic continuation or bridge handoffs for MiniMax H3 video jobs. Use after plan approval when a user seed is an exact first/last frame, a continuation must reuse an approved tail, FL2VA/bridge endpoints are required, or a failed handoff needs a new version; never redesign canon or alter approved composition.
---

# Keyframe and Handoff Builder

## Mission

Prepare, extract, normalize, validate, and version exact endpoint images for approved jobs. Bind exact user endpoints directly; otherwise derive a stable approved tail or emit an approved target-still job spec. Stop dependent work until the required endpoint gate passes.

Read [endpoint rules](references/endpoint-handoff-rules.yaml), [validation fixtures](references/validation-tests.yaml), [skill contract](references/skill-contract.yaml), and `schemas/keyframe-job.schema.json`.

## Ownership boundary

Own endpoint source resolution, extraction, deterministic approved normalization, candidate rejection, endpoint job specs, provenance, endpoint status, and handoff records. Do not own canon roles, transition meaning, prompt syntax, workflows, queueing, QC verdicts, or repair strategy.

## Inputs

Require approved production plan/hash, storyboard/segment/handoff plan, canon/asset manifest, exact seeds, and—when continuing—approved predecessor QC/render/effective clip. For bridges require both approved endpoints. Use capability evidence only to confirm supported endpoint mode.

## Required outputs

Emit approved/pending keyframes and retained candidates at deterministic paths plus `keyframe-report.yaml` and `handoff-frame-selection.yaml`. Return ready/blocked/failed and route to Workflow Compiler only when all required endpoint gates pass.

## Processing method

1. Verify plan approval/hash, assets, trigger, and transition authority.
2. Resolve endpoints by stable IDs/hashes; never infer from names or appearance.
3. Bind an exact declared user seed directly; preserve original bytes and record any required deterministic derived conversion.
4. For continue, require predecessor QC PASS and approved effective clip; scan the declared final window and choose the latest candidate passing every stability check.
5. For bridge, require approved source tail and target head.
6. Emit a target-still job only when the plan requires it and no approved endpoint exists; consume approved description/prompt.
7. Normalize only via approved pad/crop/letterbox rule; never stretch, inpaint, retouch, denoise, or redesign.
8. Validate decode, dimensions, color, paths, hashes, frame range, duplicate policy, and transforms.
9. Version outputs; exact user seed may be approved by plan+canon binding, while derived tails/stills remain pending until endpoint review.
10. Expose relation-specific dependency order and no successor-ready handoff before gates.

## Invariants

- Operate on media only for an approved plan hash.
- Keep declared user endpoints as source of truth and never regenerate them.
- Extract only from effective post-trim clips <=10 seconds.
- Require approved stable predecessor tail before continuation successor compile/render.
- Require both approved endpoints before a bridge.
- Preserve bytes, hashes, frame indices/times, transforms, tools, stable IDs, and revisions.
- Reject unstable/blurred/occluded/off-model/unfinished/impossible-reflection/ambiguous-hand states.
- Preserve transitions, canon, composition, plot, performance, camera, and segment boundaries.
- Never submit ComfyUI jobs or select creative takes.

## Non-responsibilities

Do not classify references, redesign, invent poses, write prompts, choose modes, alter segments/transitions, author graphs, queue, QC, repair, hide seams, or overwrite/delete artifacts.

## Failure conditions

Return shared plan/hash/asset/endpoint/handoff/bridge/overwrite codes plus keyframe detail codes with IDs, evidence, owner, blocking scope, and retryability. Never random-retry an unstable frame.

## Validation rules

- Validate envelope, hashes, plan link, IDs, paths, no overwrite, endpoint role, transition, source type, effective duration/FPS/frame index, dimensions, color, normalization, stability evidence, dependency order, and mode compatibility.
- Fail closed on unknown rejection flags or missing capability; preserve sources and emit a report even when blocked.

## Minimal example

For SEG01→SEG02 continue, select the latest stable frame from the approved effective SEG01 tail, normalize under the approved composition rule, record hashes/index, and bind SEG02 first frame only after endpoint approval.

## Adversarial example

For a blurry tail from an unapproved 11-second draft, return unapproved-tail/duration/unstable evidence. Do not shorten, choose a nearby frame, regenerate, cut, or emit successor-ready binding.

## Acceptance tests

- Bind an exact user endpoint without regeneration.
- Reject general references as endpoints.
- Block unapproved tails and unstable candidates.
- Select latest passing effective-tail candidate deterministically.
- Block aspect mismatch without approved rule and never stretch.
- Require two endpoints and capability for bridges.
- Enforce dependency order, immutable revisions, and no artificial cut dependency.
