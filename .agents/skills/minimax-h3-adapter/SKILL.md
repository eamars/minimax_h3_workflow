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
For official-manual-derived prompt patterns and style-neutral examples, also
read [official prompt patterns](references/official-prompt-patterns.md).
Do not duplicate or override its language rules here. Preserve the H3 field
names, reference labels, timing notation, and control markers required by the
selected mode while applying that document to natural-language prompt text.

## Inputs

Consume the current production-plan revision, segment cards, canon/reference order, optional sound plan, and live H3 capability evidence. Require validated endpoint media only when the declared mode needs it.

## Required outputs

Write revisioned prompt text, `h3-prompt-packets.yaml`, and `h3-validation-report.yaml`, linked by plan/segment revision IDs.

## Processing method

1. Validate plan revision, sources, IDs, segment states, and assets.
2. Build immutable reference bindings in node presentation order and state one exact, declared use for every bound asset. Never ask H3 to infer a reference's job from its ordinal.
3. Select T2VA, I2VA, FL2VA, L2VA, or R2VA from declared endpoint/reference roles.
4. Verify live capability support and defer a continuation until its endpoint validates.
5. Map every prompt field to exact upstream fields; preserve typed camera and the hard environment projection. Compile the official high-level order `reference usage → core creative → visible process`, without inventing creative content.
6. Project a declared multi-shot segment into one timed block per upstream editorial shot. Each block must carry shot size, visible content, camera, action, dialogue/speaker state, and sound plus the exact declared transition. Never rely on H3's default cut behavior.
7. Compile a declared one-take segment as one continuous action description with no invented internal `[Shot N]` structure or cut. Treat FL2VA endpoint pairs as continuous interpolation unless the upstream plan explicitly times a transition.
8. Preserve dialogue verbatim, fit its word span to upstream timing, identify on-screen/off-screen speakers, encode declared J-cuts/L-cuts, and separate dialogue, ambience/effects, and score.
9. For a continuation, repeat only declared identity/environment/style locks, bind the predecessor's actual final frame, restate the full entry state, and describe only the next allowed delta. Do not replay an action already completed before the boundary.
10. If style is unspecified upstream, add no named style family or habitual “cinematic/photorealistic” boilerplate. If style is declared, express its observable rendering, palette, light, texture, motion, typography, and edit behavior without narrowing it to a different style.
11. Compute the smallest valid `17k+5` frame count at 24 fps and explicit post-trim effective timing.
12. Validate labels, ordering, timing, prompt length, continuity, visible text, and traceability. Enforce the official 7000-character prompt ceiling and the selected mode's public input envelope in addition to live local capability.

## Invariants

- Require a current plan revision and live capability evidence, never a human gate or plan fingerprint.
- Keep target/effective duration positive and at most 10 seconds.
- Preserve creative fields, IDs, camera path, time domains, continuity, dialogue, and reference roles.
- Preserve declared shot/cut structure exactly; do not add shots, cuts, montage beats, or transitions.
- Preserve style latitude when no style source is declared.
- Require every reference binding to have a prompt-visible purpose.
- Preserve the environment profile and reject forbidden architectural inventions.
- Never reinterpret endpoint/general-reference roles.
- Produce filesystem artifacts only.

## Non-responsibilities

Do not rewrite plot, performance, dialogue, canon, camera, shots, segments, boundaries, handoffs, or durations. Do not choose graphs, nodes, models, seeds, or execute/QC/repair media.

## Failure conditions

Return `BLOCKED` for invalid plan revision, overlong timing, unsupported mode, invalid reference labels, missing/ambiguous reference use, missing asset, prompt over 7000 characters, undeclared cuts, one-take/cut conflict, dialogue timing or speaker ambiguity, missing entry/exit state, or invalid continuation endpoint.

## Validation rules

Validate packet schema, revision linkage, live capability, deterministic relative paths, exact H3 field order, timestamps, camera binding, reference order and purpose, shot structure, style provenance, dialogue span, audio layers, continuation delta, visible text, character count, and frame-grid/trim counts.

## Minimal example

For a ready 6-second segment with no references, select T2VA, compute aligned model frames and 144 effective frames, and emit the required prompt fields without creative additions.

## Adversarial example

For incompatible FL2VA endpoints plus an unsupported reference or an 11-second segment, block with evidence. Do not switch modes, shorten, cut, or request human sign-off.

## Acceptance tests

- Map all five modes exactly and block unsupported mixtures.
- Preserve reference labels/order, dialogue, sound layers, camera, and time bounds.
- Preserve one-take versus multi-shot semantics, declared cuts, and FL2VA interpolation behavior.
- Keep an unspecified style unnamed while accepting explicit live-action, animation, MG, UI, AR, fashion, documentary, or other style families without adapter bias.
- Reject a continuation that substitutes an earlier tail frame or repeats a completed interaction.
- Compute deterministic `17k+5` and effective-trim accounting.
- Produce revision-linked outputs without ComfyUI calls or human gates.
