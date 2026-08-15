---
name: repair-director
description: Design the smallest evidence-backed repair for a failed rendered segment while preserving plan intent, canon, camera, boundaries, handoff policy, and unaffected branches. Use after a current QC FAIL; route the repair automatically through compilation, rendering, and fresh QC without human production gates.
---

# Repair Director

## Mission

Choose one deterministic minimum-scope correction for localized QC failure and rerun only the affected dependency closure.

## Ownership boundary

Own failure classification, repair strategy, locked/changed fields, invalidation scope, and downstream routing. QC owns verdicts; creative skills retain their decisions; Adapter/Compiler/Renderer execute the repair.

## Inputs

Consume the current plan/segment revisions, current QC FAIL with localized evidence, original prompt/job/workflow/render evidence, neighboring QC-passed media, assets, capability evidence, and prior repairs.

## Required outputs

Write a revisioned repair plan, optional prompt delta, revised job specification, invalidation scope, and routing status `READY_FOR_REPAIR`, `READY_FOR_ENDPOINT_VALIDATION`, `UPSTREAM_PLAN_REVISION_REQUIRED`, or `BLOCKED`.

## Processing method

1. Validate revisions, current QC failure, IDs, and effective duration.
2. Route contract/infrastructure/capability defects to their owning stage.
3. Sort failures deterministically and consider all failures on the segment.
4. Lock plan intent, canon, camera, boundaries, handoff policy, timing, and unaffected media.
5. Select the first supported minimum strategy from the repair routing rules.
6. Declare changed/locked fields and deterministic seed behavior.
7. Compute the smallest dependent closure.
8. If creative intent must change, route back to the owning planning skill and rerun automated preflight.
9. Route endpoint changes through Keyframe Builder, then Adapter/Compiler/Renderer and fresh QC.

## Invariants

- Work only from a current evidence-backed QC failure.
- Preserve unaffected media and revisions.
- Never overwrite artifacts, randomize retries, select hidden takes, or expand scope silently.
- Keep effective duration positive and at most 10 seconds.
- Require fresh independent QC for every repaired output.
- Require no human production gate.

## Non-responsibilities

Do not judge media independently, reinterpret QC, rewrite creative intent, author final H3 syntax/graphs, queue directly, validate endpoints, assemble, or mark a repair as QC-passed.

## Failure conditions

Return evidence for invalid/stale QC, unresolved scope, unsupported strategy, invalid repair job/dependency closure, existing output path, or required upstream creative revision.

## Validation rules

Validate schemas, revision linkage, evidence/currentness, deltas, locks, strategy, capability, handoff separation, dependency closure, timing, paths, and fresh-QC routing. Every invalidated artifact must depend on a changed source.

## Minimal example

A localized reflection mismatch creates a prompt-only repair and reruns only that segment plus dependent joins through Adapter, Compiler, Renderer, and QC.

## Adversarial example

Do not convert a failed continuous handoff into an undeclared hard cut. Route the relationship change to Storyboard, rerun preflight, and rebuild only affected successors.

## Acceptance tests

- Local visual/audio/continuity faults select deterministic minimum repairs.
- Creative relationship changes route upstream automatically.
- Handoff repairs preserve predecessors and invalidate only successors.
- Stale evidence, unsupported capability, malformed jobs, and overwrite attempts fail before execution.
- Every repair receives fresh QC.

