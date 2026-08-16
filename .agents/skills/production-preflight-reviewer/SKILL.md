---
name: production-preflight-reviewer
description: Independently audit a complete real-cinematic planning revision for requirements, canon, playable direction, geography, camera coverage, continuity, boundaries, segmentation, dependencies, capability assumptions, and delivery readiness. Emit an automatic PASS, REVISE, or BLOCKED verdict and minimal upstream revision requests without rewriting plan artifacts.
---

# Production Preflight Reviewer

## Mission

Decide whether the current planning revision is coherent, traceable, playable, feasible, safely segmented, and ready to compile. Produce evidence and revision requests; never create a human production gate.

## Ownership boundary

Own the preflight verdict, evidence, risk register, deterministic revision ordering, and smallest upstream owner selection. Source skills retain their decisions.

## Inputs

Consume current request, asset, canon, plot, scene-performance, storyboard, animatic, and conditional sound revisions. Read the [wardrobe and surface-state contract](../reference-canon-manager/references/wardrobe-surface-state.md) for recurring subjects. Require one project ID, resolvable source revisions, scene/source/record time, geography, typed camera setup/motion, continuity registry, editorial boundaries, and generation handoffs.

## Required outputs

Write `preflight-report.yaml`, `risk-register.yaml`, and `revision-requests.yaml` with exactly one verdict: `PASS`, `REVISE`, or `BLOCKED`. Each failure names evidence, affected IDs, code, and smallest owning artifact/skill.

## Processing method

1. Resolve one planning revision and validate every required source.
2. Run all review-matrix dimensions in order.
3. Derive the pre-generation semantic requirements for every generation
   segment: canonical identity binding, per-subject multiplicity, dialogue
   timing/visibility, signed actor path, and destination-controlled visual reset.
   Also import the versioned wardrobe/surface contract for every recurring
   character or prop. Require an exact component inventory, region-level
   surface map, explicit transition/occlusion policy, and full opening/closing
   snapshots. Do not treat a generic clothing category as canon.
4. Build and severity-sort the risk register.
5. Sort revision requests by owner, stable ID, code, and request ID.
6. Target the earliest incorrect or missing specialist-owned decision.
7. Return `BLOCKED` for missing/unresolvable input, `REVISE` for invalid present content, and `PASS` only with no failed check.
8. On `REVISE`, let Production Orchestrator rerun the affected stages automatically.

## Invariants

- Emit one automated verdict and no human gate.
- Inspect every required dimension.
- Never normalize, shorten, merge, split, or reinterpret sources.
- Reject nonpositive or over-10-second formal generation segments.
- Require complete traceability, relation-specific handoffs, bilateral editorial boundaries, and typed camera/time ownership.
- Require each recurring canonical subject to have a downstream-bindable identity
  role; a first-frame endpoint alone is not a persistent identity role.
- Require every spoken cue to have a speaker, finite onset/end, and on-screen,
  off-screen, J-cut, or L-cut state. On-screen dialogue may not precede the
  declared visible-speaker beat.
- Require every translational actor move to have origin, destination, signed
  direction, forbidden reversal/exit directions, and endpoint state.
- Require explicit maximum visible instances for each canonical subject and
  reject an undeclared duplicate, echo, reflection copy, or destination copy.
- Require each recurring character or prop's wardrobe/surface contract to be
  present and revision-matched in every generation segment, endpoint reference,
  and pre-generation control. Compare structured fields and prompt semantics;
  do not accept a prose-only lock or a hash-only match. Block clean resets,
  alternate uniforms, recolors, missing accessories, unbound regions, and
  undeclared transitions before compilation. A post-render check may detect
  stochastic drift but cannot close this gate retroactively.
- Reject a text-only scene reset. Require an endpoint bridge, reference
  re-establish, or editorial cut with a validated destination anchor before
  compilation.
- Preserve source revisions and deterministic ordering.

## Non-responsibilities

Do not author or edit plot, dialogue, performance, sound, canon, blocking, camera, shots, segments, prompts, graphs, jobs, QC, repairs, or final edits. Inspect no runtime media.

## Failure conditions

Return `BLOCKED` for missing required artifacts, roles, sources, endpoint declarations, destination anchors, identity binding roles, or required capability evidence. Return `REVISE` for premise, playability, blocking, unsigned motion, dialogue timing/visibility, subject multiplicity, duration, handoff, dependency, text-only visual reset, unbound or stale wardrobe/surface state, undeclared surface transition, or known-capability defects.

## Validation rules

Validate the report and every consumed schema. Require stable IDs, positive time bounds, traceability, acceptance IDs, acyclic dependencies, canon roles, structured camera coverage, signed actor paths, timed speaker visibility, subject-instance bounds, destination-controlled visual resets, and policy-appropriate handoffs. A preflight `PASS` permits compilation only; the workflow compiler must still record `PRE_GENERATION_VALIDATED` before queueing. Identical canonical inputs must produce identical review findings.

## Minimal example

A complete 8-second terminal segment yields `PASS`, no revision request, and automatically routes to compilation.

## Adversarial example

An 11-second segment with opaque camera language, no geography, and conflated transitions yields separate duration/camera/boundary revision requests. Do not shorten or rewrite it in preflight.

## Acceptance tests

- Pass a complete valid fixture and route it to compilation automatically.
- Reject zero/over-cap durations, missing handoffs, ambiguous roles, traceability breaks, and cycles.
- Reject recurring identity with only a first-frame seed, `<d>` dialogue without a
  timed speaker/visibility window, actor travel without a signed path and
  forbidden reversal, unbounded canonical-subject multiplicity, and a text-only
  scene reset without a destination anchor.
- Warn rather than fail on unknown optional capability.
- Produce deterministic results without a human-review state.
