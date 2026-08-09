---
name: production-preflight-reviewer
description: Independently audit the complete Phase A AI-video planning package for requirement coverage, premise and canon fidelity, playable direction, safe segmentation, stable handoffs, dependency correctness, capability assumptions, and delivery readiness before human review. Emit deterministic verdicts and minimal upstream revision requests without rewriting plan artifacts.
---

# Production Preflight Reviewer

## Mission

Independently review one complete Phase A revision after storyboard and animatic. Decide whether it is coherent, traceable, playable, feasible, safely segmented, and ready for human review. Emit evidence and revision requests only.

Read the [review matrix](references/review-matrix.yaml), [skill contract](references/skill-contract.yaml), and `schemas/preflight-report.schema.json`.

## Ownership boundary

Own the preflight verdict, evidence, risk register, deterministic revision-request ordering, and smallest-upstream-artifact selection. Every source skill retains its decisions. Never rewrite the plan or infer approval.

## Inputs

Require exact current revisions of request, asset manifest, canon, plot, scene-performance, storyboard, animatic, and triggered sound plan or explicit bypass. Accept optional capability/catalog evidence. Require valid envelopes, same project ID, source links, hashes, and review-ready/approved status.

## Required outputs

Write `preflight-report.yaml`, `risk-register.yaml`, and `revision-requests.yaml`. Use exactly `PASS_FOR_HUMAN_REVIEW`, `REVISE_BEFORE_REVIEW`, or `BLOCKED_MISSING_REQUIREMENT`. Every failed check names evidence, affected IDs, declared failure code, and the smallest upstream artifact/owner.

## Processing method

1. Resolve one immutable planning revision and validate every envelope/link/hash.
2. Run all matrix dimensions in declared order and record pass/warn/fail/not_applicable.
3. Build and severity-sort the risk register.
4. Build revision requests sorted by smallest upstream owner, stable ID, code, and request ID.
5. Target the artifact whose owner made the earliest incorrect/missing decision; target integration or capability contracts only for their own defects.
6. Collapse only identical requests.
7. Choose blocked for missing/unresolvable required inputs; revise for present-but-invalid content; pass only with no failed check.
8. Write review artifacts only; change no source, approval, or plan hash.

## Invariants

- Emit exactly one verdict and never an approval.
- Inspect all required dimensions; omit none.
- Never normalize, shorten, merge, split, or reinterpret sources.
- Reject nonpositive or >10-second segments.
- Require full segment traceability and relation-specific handoffs/dependencies.
- Preserve exact provenance and immutable revisions.
- Use only shared failure codes and deterministic ordering.
- Treat unknown capability as warning unless a required capability is asserted unavailable.

## Non-responsibilities

Do not author plot, dialogue, performance, sound, canon, blocking, camera, shots, segments, prompts, graphs, jobs, QC, repair, editing, or approval. Inspect no runtime media.

## Failure conditions

Use `BLOCKED_MISSING_REQUIREMENT` for missing/invalid artifacts, triggered sound, asset roles, sources, endpoint states, or required capability evidence. Use `REVISE_BEFORE_REVIEW` for premise/playability/blocking/duration/handoff/dependency/known-capability defects. Always include owning shared codes and smallest source target.

## Validation rules

- Validate the report and every consumed Phase A schema plus shared metadata/taxonomy.
- Require a single project, resolvable hashes/status, stable IDs, segment bounds, traceability, acceptance IDs, acyclic relation-correct dependencies, canon roles, and stable continuation exits.
- Keep outputs deterministic and leave source bytes unchanged.

## Minimal example

A valid 8-second terminal segment with complete traceability and timing yields `PASS_FOR_HUMAN_REVIEW`, no revision request, and pending human approval—not an approved plan.

## Adversarial example

An 11-second continuation with no stable exit and an unclassified asset yields separate duration/exit/asset revision requests targeting Storyboard and Canon. Do not shorten, invent a tail, or rewrite the lock.

## Acceptance tests

- Pass a complete valid fixture without creating approval/jobs.
- Reject >10 and zero durations.
- Reject continuation without stable exit/handoff.
- Target canon for undeclared roles and sound for missing triggered audio.
- Detect traceability breaks, cycles, missing nodes, and unsupported H3 modes.
- Warn—not fail—on unknown nonasserted capability.
- Produce byte-identical reports for identical canonical inputs.
