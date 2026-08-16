---
name: minimax-h3-adapter
description: Compile a ready production-plan revision into deterministic MiniMax H3 T2VA, I2VA, FL2VA, L2VA, or R2VA prompt packets for ComfyUI while preserving camera intent, three time domains, continuity, audio, and generation handoffs. Use after automated preflight and live H3 capability probing without a human production gate.
---

# MiniMax H3 Adapter

## Mission

Compile each generation segment into one schema-valid H3 packet and UTF-8 prompt. Preserve plan meaning, references, dialogue, camera, timing, continuity, sound intent, and stable IDs. Never render or call ComfyUI.

## Ownership boundary

Own H3 family selection from declared roles, H3 field syntax, reference ordering, duration/frame-grid accounting, and field provenance. Workflow Compiler owns node graphs.

## Prompt language

Before writing any H3 prompt prose, read the repository's single canonical
language and cinematic terminology policy:
[`../../../docs/prompt-language-style.md`](../../../docs/prompt-language-style.md).
Do not duplicate or override its language rules here. Preserve the H3 field
names, reference labels, timing notation, and control markers required by the
selected mode while applying that document to natural-language prompt text.

## Inputs

Consume the current production-plan revision, segment cards, canon/reference order, optional sound plan, and live H3 capability evidence. Require validated endpoint media only when the declared mode needs it.

## Required outputs

Write revisioned prompt text, `h3-prompt-packets.yaml`, and `h3-validation-report.yaml`, linked by plan/segment revision IDs.

## Processing method

1. Validate plan revision, sources, IDs, segment states, and assets.
2. Build immutable reference bindings in node presentation order.
3. Select T2VA, I2VA, FL2VA, L2VA, or R2VA from declared endpoint/reference roles.
4. Verify live capability support and defer a continuation until its endpoint validates.
5. Map every prompt field to exact upstream fields; preserve typed camera and the hard environment projection.
6. Preserve dialogue verbatim and separate dialogue, ambience/effects, and score.
7. Compute the smallest valid `17k+5` frame count at 24 fps and explicit post-trim effective timing.
8. Validate labels, ordering, timing, prompt length, continuity, and traceability.

## Invariants

- Require a current plan revision and live capability evidence, never a human gate or plan fingerprint.
- Keep target/effective duration positive and at most 10 seconds.
- Preserve creative fields, IDs, camera path, time domains, continuity, dialogue, and reference roles.
- Preserve the environment profile and reject forbidden architectural inventions.
- Never reinterpret endpoint/general-reference roles.
- Produce filesystem artifacts only.

## Non-responsibilities

Do not rewrite plot, performance, dialogue, canon, camera, shots, segments, boundaries, handoffs, or durations. Do not choose graphs, nodes, models, seeds, or execute/QC/repair media.

## Failure conditions

Return `BLOCKED` for invalid plan revision, overlong timing, unsupported mode, invalid reference labels, missing asset, unclear speaker, missing entry/exit state, or invalid continuation endpoint.

## Validation rules

Validate packet schema, revision linkage, live capability, deterministic relative paths, exact H3 field order, timestamps, camera binding, reference order, dialogue, audio layers, and frame-grid/trim counts.

## Minimal example

For a ready 6-second segment with no references, select T2VA, compute aligned model frames and 144 effective frames, and emit the required prompt fields without creative additions.

## Adversarial example

For incompatible FL2VA endpoints plus an unsupported reference or an 11-second segment, block with evidence. Do not switch modes, shorten, cut, or request human sign-off.

## Acceptance tests

- Map all five modes exactly and block unsupported mixtures.
- Preserve reference labels/order, dialogue, sound layers, camera, and time bounds.
- Compute deterministic `17k+5` and effective-trim accounting.
- Produce revision-linked outputs without ComfyUI calls or human gates.
