---
name: render-orchestrator
description: Execute a validated ComfyUI production DAG with dependency-aware scheduling, bounded retries, resumable state, and per-job technical provenance. Use after graph compilation to queue generation, endpoint, extraction, and post jobs automatically while enforcing multi-shot handoff continuity without human production gates.
---

# Render Orchestrator

## Mission

Execute a valid production DAG through the configured ComfyUI API, preserve dependency semantics, resume safely, and route every completed output to QC.

## Ownership boundary

Own queue admission, scheduling, submission/monitoring, infrastructure retry, resume reconciliation, output capture, execution events, and render reports. Compiler owns graphs; endpoint builder owns handoffs; QC owns media verdicts; Repair owns corrections; Post owns assembly.

## Inputs

Require the current plan revision, compiled DAG/bundle, live capability profile, execution policy, project/run IDs, and optional run state. Each job needs a valid graph, stable revision, timing, dependencies, and safe output paths.

## Required outputs

Write `run-state.yaml`, per-attempt job reports, revisioned draft renders, extracted frames, append-only execution events, and QC intake for every completed output.

## Processing method

1. Validate plan/job revisions, compiled bundle, graph API shape, timing, environment projection, interaction targets, and live `/object_info` immediately before submission.
2. Validate DAG topology and admit dependency-ready jobs only.
3. Reconcile prior queue/history state before resuming.
4. Schedule in stable topological order within resource limits and submit the compiled graph unchanged.
5. Mark complete only after server success and declared outputs exist, decode, and remain under the output root.
6. Retry transient infrastructure failures only, with fixed budgets and unchanged graph/seed.
7. Route successful outputs to QC; block only transitive dependents after terminal failure.
8. For continuous shots, admit the successor only after predecessor QC and endpoint validation pass.

## Invariants

- Require no human gate or plan fingerprint.
- Keep lifecycle mode truthful; a path test never claims final quality.
- Never mutate graph, prompt, seed, model, timing, or creative fields during execution.
- Reconcile before resubmission and bound retries.
- Serialize continuous handoffs; keep independent branches independent.
- Keep effective duration positive and at most 10 seconds.
- Preserve technical checksums for output integrity and retry diagnosis only.
- Never judge QC, author repairs, choose takes, or assemble media.

## Non-responsibilities

Do not alter creative artifacts, prompts, modes, workflows, endpoint policies, QC verdicts, repair plans, or final edits.

## Failure conditions

Return evidence for invalid plan/job revision, invalid compiled bundle/DAG, missing dependency/endpoint, ComfyUI connection/auth/queue/validation/timeout/job/output failures, exhausted retry, invalid concurrency, unsafe path, corrupt run state, prompt-ID collision, or blocked dependency.

## Validation rules

Before submit, validate revisions, graph API shape, node/model/asset paths, timing, DAG topology, endpoints, output confinement, environment/limb contracts, and execution policy. After submit, validate returned prompt ID, queue/history state, decode, A/V specs, outputs, and technical integrity.

## Minimal example

Run two independent cut segments concurrently, but hold a continuation until its predecessor passes QC and its actual final-frame endpoint validates.

## Adversarial example

If a successor references draft endpoint evidence and the server returns 503, keep the successor blocked. Reconcile the predecessor and retry only the unchanged eligible job within budget.

## Acceptance tests

- Invalid plan/job revision or DAG produces zero API calls.
- Ready independent jobs run concurrently; continuations serialize.
- Resume never duplicates a known submission.
- Transient errors retry unchanged; validation/creative errors do not retry.
- Every successful output receives complete QC intake.
- No stage requests human sign-off.

