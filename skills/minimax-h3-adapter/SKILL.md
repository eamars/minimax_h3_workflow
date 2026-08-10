---
name: minimax-h3-adapter
description: Compile an explicitly approved real-cinematic production-plan revision into deterministic MiniMax H3 T2VA, I2VA, FL2VA, L2VA, or R2VA prompt packets for ComfyUI without flattening typed camera setup/motion, three time domains, continuity invariants, or generation handoffs. Invoke only after the plan approval/hash gate and frozen live H3 capability profile.
---

# MiniMax H3 Adapter

## Mission

Compile each approved generation-segment card into one schema-valid H3 packet and UTF-8 prompt text. Preserve plan meaning, reference roles/order, dialogue, typed camera setup plus in-shot motion, scene/source/record time maps, continuity invariants, audio intent, and stable IDs. Never render or call ComfyUI.

Read [mode rules](references/h3-mode-rules.yaml), [prompt rules](references/prompt-rules.yaml), [skill contract](references/skill-contract.yaml), and `schemas/h3-prompt-packet-v2.schema.json` for v2 plans; retain the v1 schema only for historical packets.

## Ownership boundary

Own semantic H3 family selection from declared roles, H3 field syntax, reference tags/order, duration/frame-grid accounting, and field provenance. The Workflow Compiler owns concrete graphs/nodes. Preserve the approved plan hash exactly.

## Inputs

Require approved production plan plus exact approval hash, approved segment cards, canon/asset/reference order, optional sound plan, and a frozen live H3 capability profile with node/model/limits evidence. Treat stale defaults as non-authoritative.

## Required outputs

Write `compiled/prompt-packets/<segment-id>.txt`, `h3-prompt-packets.yaml`, and `h3-validation-report.yaml`. Link every packet to exact plan/source/capability hashes and create immutable revisions only.

## Processing method

1. Validate plan approval/hash, sources, stable IDs, segment states, and assets.
2. Build immutable reference bindings in node presentation order with one-to-one Picture/Video/Audio labels.
3. Derive mode: no endpoints/refs T2VA; first only I2VA; first+last FL2VA; last only L2VA; nonendpoint references R2VA. Fail unsupported mixtures.
4. Verify frozen capability support; defer continuation path binding until approved tail.
5. Map each prompt field to exact upstream paths before prose and reuse canon anchors verbatim; preserve the camera setup/motion interval map rather than replacing it with a generic “cinematic camera” phrase. Serialize the hard environment projection as positive landmark/boundary language plus a profile ID; keep forbidden architecture as negated validation-only exclusions and never as a positive scene feature.
6. Serialize base-family or exact R2VA section order with required endpoint prefixes.
7. Preserve dialogue verbatim and stable speakers; separate dialogue, ambience/effects, and score layers.
8. Compute smallest `17k+5` model frame count at 24 FPS above target; keep target/model/effective values separate and require explicit trim to effective <=10 seconds.
9. Validate timestamps, prompt length, labels, modes, required fields, traceability, and canonical hash.
10. Return PASS/BLOCKED and route to conditional Keyframe Builder then Workflow Compiler.

## Invariants

- Require exact approved plan hash and frozen live capability evidence.
- Keep target/effective duration >0 and <=10; model duration may exceed only for frame grid and must be trimmed.
- Preserve all approved creative fields, typed camera path, three time domains, continuity invariants/deltas, dialogue, reference roles/order, and IDs.
- Preserve the hard environment profile ID and required landmarks in every prompt; reject positive forbidden-feature language and missing unknown-space/boundary language before the graph compiler.
- Map every label one-to-one; never reinterpret endpoints/general references.
- Take limits from frozen capability profile.
- Produce filesystem artifacts only; never select workflows, queue, render, judge, repair, or approve.

## Non-responsibilities

Do not rewrite plot/performance/dialogue/canon/camera setup/motion/shots/segments/editorial boundaries/generation handoffs/durations. Do not flatten a camera position change into a static reference, generate endpoints, normalize media, choose graphs/nodes/models/seeds, call ComfyUI, render, QC, repair, or hide unsupported combinations.

## Failure conditions

Use shared plan approval/hash, duration, H3 mode/label, missing asset, unclear speaker, entry/exit, and unapproved-tail codes with affected IDs/evidence. Fail closed without best-effort prompts.

## Validation rules

- Validate packet schema, metadata, approved plan linkage, frozen capability hash, deterministic relative paths, and no overwrite.
- Require exact base or R2VA field ordering, monotonic in-range scene/source/record timestamps, structured camera interval binding, reference presentation order, verbatim dialogue, correct sound layers, deterministic grid/trim counts, and reproducible hashes.
- Reject any node/workflow selection or creative mutation.

## Minimal example

For an approved 6-second segment with no endpoint/reference, select T2VA, model frame count 158, effective 144 frames/6 seconds, and emit the three base fields plus exact plan/source map. Add nothing creative.

## Adversarial example

For FL2VA endpoints plus an untested full reference, or 11 seconds from an unapproved tail, return H3 mode/duration/handoff failures. Do not switch modes, shorten, cut, or use the raw tail.

## Acceptance tests

- Enforce approval/hash before writes.
- Map the five modes exactly and block mixtures/unsupported capability.
- Verify labels/order/hashes for mixed reference media.
- Preserve dialogue/tags/layers and timestamp bounds.
- Compute deterministic 17k+5/effective trim accounting.
- Produce byte-identical, provenance-complete immutable outputs without ComfyUI calls.
