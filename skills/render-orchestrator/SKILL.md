---
name: render-orchestrator
description: Execute an approved, compiled real-cinematic ComfyUI production DAG with dependency-aware scheduling, bounded deterministic retries, resumable state, and per-job provenance. Use after plan approval and compiler validation to queue video, keyframe, bridge, extraction, and post jobs while enforcing typed generation handoff policies; never revise prompts or choose creative takes.
---

# Render Orchestrator

## Mission

Execute only a valid, approved production DAG through the configured ComfyUI API. Preserve dependency semantics, immutable revisions, plan/workflow hashes, deterministic client IDs, concurrency limits, resumable state, and evidence-rich reports while routing each completed output immediately to QC.

## Ownership boundary

Own queue admission, topological scheduling, concurrency, ComfyUI submission/monitoring, transient infrastructure retry, interruption/resume, output-path/hash capture, execution events, and render-report provenance. The production orchestrator owns approval; the compiler owns graphs; keyframe builder owns endpoints; QC owns pass/fail; repair owns correction; post owns assembly.

## Inputs

Require an approved production plan and matching hash; compiler production DAG and immutable compiled bundle; approval record; compiler capability/endpoint profile; execution policy; project/run IDs; and optional prior run state. Every node must have a valid ComfyUI job, stable revision, duration at most 10 seconds, dependencies, output paths, and source hashes. Generation handoffs additionally require the endpoint evidence declared by their policy; only stable-tail relationships require a QC-approved stable tail.

## Required outputs

Write atomically without approved overwrite: `run-state.yaml`, `job-reports/<job-id>.yaml` per attempt, revisioned `renders/draft/`, `frames/extracted/` when declared, append-only `execution-log.jsonl`, and a QC-intake record for every completed output. Each report links run/job/attempt IDs, plan/workflow/payload hashes, seed, models/nodes, endpoint, client/prompt IDs, dependencies, timestamps, outputs/hashes, retry history, state, and errors.

## Processing method

1. Validate approval, exact plan hash, compiled-bundle status, sources, paths, and immutability before API calls.
2. Validate DAG IDs/edges/cycles/job types. Admit only dependency-ready jobs; `same_shot_continue` and bridge jobs require their declared endpoint gates, while independent jobs remain independent.
3. Load/create run state keyed by project, plan revision/hash, run ID, and execution-policy hash. On resume reconcile `/history/{prompt_id}`, `/queue`, and available job status before submission.
4. Schedule ready nodes in stable topological order within resource limits. Derive deterministic UUIDv5 prompt IDs from project/run/job/attempt and stable client IDs; send the compiled graph unchanged to `POST /prompt`.
5. Monitor queue/history with bounded polling. Mark complete only after server success and declared outputs exist, decode, remain under the output root, and hash successfully.
6. Retry only transient connection, timeout, 408/409/425/429/5xx, or temporary queue/history failures using the fixed attempt budget and deterministic 2/5/15-second backoff. Keep graph, inputs, seed, and workflow hashes unchanged.
7. Emit QC intake on success. On terminal failure, block only transitive dependents and keep unrelated branches schedulable.
8. On interruption, persist in-flight IDs and stop admissions. Resume by reconciliation without duplicating known queued/running/completed prompts.
9. Return counts, blocked branches, exhausted retries, and report/output paths and hashes. Route evidence through the production orchestrator.

## Invariants

- Exact plan approval/hash and a validated compiled bundle are mandatory.
- Compiled graph, prompt, seed, models, nodes, timing, and creative parameters never mutate.
- Prompt IDs are canonical and deterministic; reconciliation precedes resubmission.
- DAG gates are enforced, same-shot continuations serialize, moving endpoints retain their policy evidence, and independent generation relationships remain independent.
- Effective segment duration is positive and at most 10 seconds.
- Retry is bounded, deterministic, infrastructure-only, and spec-preserving.
- Reports/state/events/outputs are versioned, hashed, confined, and immutable once approved.
- A failed node blocks only transitive dependents. This skill never approves, repairs, selects takes, or assembles.

## Non-responsibilities

Do not alter canon, plot, performance, storyboard, sound, animatic, H3 prompts, modes, workflows, endpoint frames, handoff policies, creative parameters, QC verdicts, repair plans, or final edits. Do not auto-continue from unapproved evidence or randomize a retry.

## Failure conditions

Return affected job/attempt IDs, evidence, retryability, blocking scope and owner using only: `PLAN_APPROVAL_REQUIRED`, `PLAN_HASH_MISMATCH`, `COMPILED_BUNDLE_INVALID`, `DAG_INVALID`, `DAG_CYCLE`, `DAG_DEPENDENCY_MISSING`, `HANDOFF_TAIL_UNAPPROVED`, `COMFYUI_UNREACHABLE`, `COMFYUI_AUTH_FAILED`, `COMFYUI_QUEUE_REJECTED`, `COMFYUI_VALIDATION_FAILED`, `COMFYUI_TIMEOUT`, `COMFYUI_JOB_FAILED`, `COMFYUI_OUTPUT_MISSING`, `COMFYUI_OUTPUT_INVALID`, `TRANSIENT_RETRY_EXHAUSTED`, `CONCURRENCY_LIMIT_INVALID`, `APPROVED_ARTIFACT_OVERWRITE_FORBIDDEN`, `OUTPUT_PATH_ESCAPE`, `RUN_STATE_CORRUPT`, `PROMPT_ID_COLLISION`, or `DEPENDENCY_BLOCKED`.

## Validation rules

Before submit validate artifacts/hashes, approval, graph API shape/hash, IDs, node/job types, model/asset paths, duration, DAG topology, endpoint approvals, output-root confinement, execution policy, and prompt-ID derivation. During/after submit validate HTTP/returned prompt ID, reconcile queue/history, enforce timeout/retries, verify outputs/decodability/hashes, and compare report hashes. Unknown errors fail closed.

## Minimal example

Admit two independent cut segments concurrently. Admit a continuation only after its predecessor completes, QC passes, and the approved handoff exists. A transient 503 retries with the same graph and seed under deterministic attempt IDs; successful outputs immediately enter QC.

## Adversarial example

If a successor references draft endpoint evidence and `/prompt` returns 503, block it with the applicable handoff-approval failure; reconcile the submitted prompt before retrying the unchanged job within budget. Never invent an endpoint, alter the graph, or mark it complete.

## Acceptance tests

- Approval/hash and invalid DAG fixtures cause zero API calls.
- Dependency-ready jobs run; continuation/bridge serialize; independent cuts use configured concurrency.
- UUID prompt IDs/client ID are deterministic and resume does not duplicate submissions.
- Transient errors retry unchanged within budget; validation/creative errors never retry.
- Every attempt produces complete provenance and verified, confined outputs routed to QC.
- Terminal failure blocks only dependent branches and preserves unrelated work and approved artifacts.
- Unapproved handoffs, >10-second effective media, overwrite attempts, path escape, and unknown errors fail closed.
