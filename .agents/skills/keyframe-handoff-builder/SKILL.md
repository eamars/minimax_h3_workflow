---
name: keyframe-handoff-builder
description: Prepare exact endpoint images and deterministic MiniMax H3 generation handoffs, including stable tails, moving endpoints, declared entry references, and endpoint bridges. Use when a seed is an exact first/last frame or a continuation needs the predecessor's actual final frame; validation is automatic and requires no human production gate.
---

# Keyframe and Handoff Builder

## Mission

Resolve, extract, normalize, validate, and version exact endpoint images for planned jobs. Bind declared seeds directly and derive continuation tails only from effective rendered media.

## Ownership boundary

Own endpoint source resolution, extraction, deterministic normalization, candidate rejection, endpoint job specs, and handoff records. QC owns media verdicts; Storyboard owns handoff meaning; Workflow Compiler owns graphs.

## Inputs

Consume the current plan revision, storyboard segment/handoff data, canon assets, exact seeds, and—when continuing—the predecessor's QC-passed effective clip. Bridges require both validated endpoints.

## Required outputs

Emit endpoint files, `keyframe-report.yaml`, and `handoff-frame-selection.yaml` with `pending`, `passed`, or `failed` validation status. Route passed endpoints automatically to Workflow Compiler.

## Processing method

1. Validate plan/segment revisions, assets, generation relationship, and endpoint policy.
2. Resolve endpoints by stable IDs; use checksums only to verify raw media identity.
3. Bind declared user seeds without regeneration.
4. For `same_shot_continue`, use the predecessor's actual final decoded frame. Validate the final window but never substitute an earlier frame.
5. Preserve motion evidence for `moving_endpoint` and bind a `declared_entry_reference` exactly as declared.
6. Require both endpoints for a bridge.
7. Normalize only through declared pad/crop/letterbox rules; never stretch, retouch, denoise, or redesign.
8. Validate decode, dimensions, color, frame index, duplicate policy, transforms, and safe paths.
9. Create a new revision and expose dependency order only after automated validation passes.

## Invariants

- Require no human gate or plan fingerprint.
- Keep declared user endpoints as source of truth.
- Extract only from effective post-trim clips of at most 10 seconds.
- Do not impose a stable-tail rule on moving-endpoint or declared-entry-reference policies.
- Preserve actual bytes, frame index/time, transforms, and revision IDs.
- Never queue ComfyUI or select a creative take.

## Non-responsibilities

Do not classify references, redesign imagery, invent poses, write prompts, choose modes, change boundaries/handoffs, compile graphs, render, judge QC, repair, or assemble.

## Failure conditions

Return evidence for invalid revision, missing asset, invalid/unstable endpoint, incompatible dimensions, unsupported bridge/mode, unsafe path, or existing output. Block only the dependent continuation branch.

## Validation rules

Validate schema, revision linkage, endpoint role, source type, effective timing/FPS/frame index, dimensions, color, normalization, policy-specific evidence, dependency order, mode capability, and output paths.

## Minimal example

For SEG01→SEG02, extract SEG01's actual final decoded frame, validate its last-frame window and declared state/camera/audio match, then bind it as SEG02's first frame.

## Adversarial example

For a blurry tail from an 11-second draft, fail the endpoint. Do not shorten, choose a nearby frame, regenerate, change the cut, or request sign-off.

## Acceptance tests

- Bind exact user endpoints without regeneration.
- Reject general references masquerading as endpoints.
- Use the actual final frame for continuous successors.
- Block invalid candidates and incompatible dimensions deterministically.
- Require two valid endpoints for bridges.
- Route passed endpoints automatically with no human gate.

