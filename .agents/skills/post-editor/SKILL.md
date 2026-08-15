---
name: post-editor
description: Assemble QC-passed MiniMax H3 media into a deterministic edit, audio mix, delivery workflow, and manifest. Use after required segment and seam QC; preserve declared editorial boundaries and route the master through final QC without human production gates.
---

# Post Editor

## Mission

Assemble the current QC-passed production into a reproducible final master, preserving source timing, transitions, audio continuity, and delivery specifications.

## Ownership boundary

Own the final EDL, source in/out selection within handles, transition realization, audio mix plan, assembly graph, master creation, and delivery manifest. Preserve source bytes, shot order, boundary motivations, handoffs, and sound intent.

## Inputs

Consume the current plan revision, QC-passed media manifest, segment/seam QC reports, editorial boundaries, animatic/assembly map, sound-boundary map, delivery spec, and live utility-workflow capability.

## Required outputs

Write revisioned final EDL, assembly plan, audio mix plan, assembly workflow, optional master, and delivery manifest. Route the exact master automatically to final QC.

## Processing method

1. Validate plan/media revisions, delivery spec, and QC PASS for every source.
2. Resolve exact source frame/sample ranges from stable IDs, never filename order.
3. Apply declared cuts, dissolves, fades, endpoint-duplicate rules, and audio edits only.
4. Build sample-accurate audio joins without gaps, clicks, restarts, drift, or double audio.
5. Normalize picture/audio to delivery specifications and record each operation.
6. Build and validate the final graph from live capability and utility templates.
7. Create a new master revision and route it to final QC. Mark delivery complete only after final QC PASS.

## Invariants

- Use only current QC-passed sources.
- Never overwrite media, masters, manifests, EDLs, workflows, or QC reports.
- Keep editorial mechanisms separate from generation handoffs.
- Remove a duplicated continuation frame only on exact frame equality; never remove frames at intentional cuts.
- Do not hide a failed seam with a transition.
- Use checksums only for technical integrity and reproducibility.
- Require final QC, never a human production gate.

## Non-responsibilities

Do not rewrite story, canon, storyboard, segmentation, prompts, model bindings, render schedule, QC evidence, repairs, or delivery requirements. Do not queue generation jobs.

## Failure conditions

Return evidence for missing/non-PASS media, revision mismatch, invalid transition, endpoint duplicate mismatch, audio continuity failure, runtime/spec mismatch, invalid workflow, failed final QC, unsafe path, or existing output.

## Validation rules

Validate revisions, QC PASS, safe paths, timeline monotonicity, boundary semantics, frame/sample bounds, runtime, duplicate/flash frames, audio, picture specs, graph validity, and final QC traceability.

## Minimal example

At a continuous boundary with an exact duplicated endpoint frame, retain the predecessor tail, drop successor frame zero, record the operation, join audio per the sound map, and send the master to final QC.

## Adversarial example

If a source fails seam QC, block assembly and route it to Repair Director. Do not hide it with a dissolve or request sign-off.

## Acceptance tests

- QC-passed inputs produce deterministic EDL, audio, workflow, master, and manifest revisions.
- Missing/stale/failed media blocks before assembly.
- Continuation duplicate removal is exact and transition-specific.
- A/V, delivery, or final-QC failures block delivery.
- Repeated canonical inputs yield the same assembly plan.

