---
name: request-normalizer
description: Convert a plain-language AI-video brief and supplied asset metadata into a conservative, provenance-preserving project request for approval-gated planning. Use first in the production-orchestrator pipeline to normalize runtime, delivery constraints, exclusions, seed-asset declarations, and lifecycle preference before reference-canon-manager; never use it for plot, camera, image interpretation, prompt compilation, or rendering.
---

# Request Normalizer

## Mission

Normalize the user's brief into a conservative `project_request` suitable for planning. Preserve intent exactly, label values by provenance, expose material uncertainty, and establish the mandatory ten-second generation-segment policy.

## Ownership boundary

Own user intent, explicit constraints, exclusions, lifecycle preference, and intake assumptions. Preserve user wording and source references. Create no plot beats, performance actions, camera language, canon interpretation, image semantics, prompts, workflows, or renders.

## Inputs

Consume the raw brief; requested runtime and delivery constraints; supplied image, video, and audio paths or metadata; user-declared asset roles; exclusions; lifecycle preference; and an existing request revision only for an orchestrator-authorized revision. Treat missing optional values as unknown. Do not inspect media to infer meaning.

Read [normalization rules](references/normalization-rules.yaml), the package [skill contract](references/skill-contract.yaml), and `schemas/project-request.schema.json` before emitting artifacts.

## Required outputs

Write `project-request.yaml`, `assumptions.md`, and `open-decisions.yaml`. Make YAML authoritative; keep Markdown a projection of structured assumptions. Include:

```yaml
normalization:
  status: review_ready | blocked | failed
  failure_codes: []
  warnings: []
  blocking_decisions: []
  handoff_ready: true
  next_skill: reference-canon-manager
```

Attach the shared artifact envelope to every YAML artifact.

## Processing method

1. Load shared metadata, naming, taxonomy, and schema contracts.
2. Preserve the supplied project ID; allocate the lowest unused `PRJnn` only for a new project.
3. Capture the raw brief and create a lossless intent paraphrase with source references.
4. Separate explicit requirements, exclusions, delegations, assumptions, policy, and unknowns.
5. Normalize runtime and delivery constraints without fabricating missing values.
6. Copy supplied asset paths, types, user roles, and supplied hashes into provisional `asset_inputs`; do not classify content.
7. Set `policy.max_generation_segment_seconds: 10`, `execution.effective_mode: PLAN_ONLY`, and both compile/render authorization flags to false.
8. Ask only when an answer changes premise, safety, or an irreversible choice; otherwise record a reversible assumption.
9. Preserve unresolved contradictions as blocking decisions.
10. Hash canonical authoritative content, create a new revision, and never overwrite an approved or superseded artifact.
11. Set `handoff_ready` only when no blocking intake decision remains.
12. Return machine-readable status and shared failure codes.

## Invariants

- Preserve the exact raw brief and explicit constraints.
- Distinguish user facts from assumptions and policy defaults.
- Keep the maximum generation segment at exactly 10 seconds while allowing longer total runtimes.
- Keep requested lifecycle mode separate from the enforced planning gate.
- Preserve user asset roles as provisional declarations only.
- Do not infer subject, world, emotion, pose, style, or endpoint role from media.
- Preserve stable IDs, provenance, source versions, hashes, and immutable revisions.
- Permit no compilation or rendering before approved-plan verification.
- Keep ordering deterministic for identical semantic input.

## Non-responsibilities

Do not invent narrative events; decide actions or speech; interpret images; resolve canon conflicts; choose camera, shots, transitions, or segments; select MiniMax H3 modes; compile ComfyUI; probe or queue ComfyUI; approve outputs; reconcile conflicts silently; or modify upstream decisions.

## Failure conditions

Return `INTAKE_MISSING_CORE_REQUIREMENT` with affected fields, evidence, and a structured reason for an empty or unintelligible brief, unresolved premise/safety/irreversible conflicts, unsupported lifecycle mode, invalid required project ID, or an explicitly required single segment over 10 seconds. Do not fail because optional runtime, format, style, or role information is absent. Route asset-role ambiguity downstream.

## Validation rules

- Validate all YAML against the shared artifact and project-request contracts.
- Require provenance for each requirement, exclusion, asset declaration, assumption, and decision.
- Reject fabricated plot, scene, shot, camera, blocking, canon, or prompt fields.
- Require the ten-second policy, `PLAN_ONLY`, and false compile/render authorization.
- Require blocking decisions to make `handoff_ready` false.
- Reject traversal, absolute production paths, ambiguous `latest` aliases, duplicate IDs, and approved-artifact mutation.
- Run `python scripts/validate_request.py project-request.yaml assumptions.md open-decisions.yaml` from this package.

## Minimal example

For “A 10-second video showing Kazusa having a shower,” preserve the sentence, extract the visible premise and 10-second total runtime as explicit requirements, leave unspecified delivery values unknown, set the segment cap to 10, and hand off without adding actions, emotions, camera, costume, or plot escalation.

## Adversarial example

For “Make one uninterrupted 12-second generated segment; it must obey a 10-second maximum,” preserve both constraints and return `INTAKE_MISSING_CORE_REQUIREMENT` with reason `generation_segment_cap_conflict`, a blocking decision asking whether the intended shot may be split, and `handoff_ready: false`. Do not silently shorten or split.

## Acceptance tests

- Normalize a one-line brief without downstream invention.
- Preserve source quotes and explicit runtime precedence.
- Leave unspecified runtime unknown.
- Allow a total project runtime above 10 seconds without creating segments.
- Block an explicit single segment above 10 seconds.
- Preserve requested compilation while enforcing `PLAN_ONLY`.
- Keep asset roles provisional and avoid visual interpretation.
- Emit stable IDs, provenance, hashes, revisions, and machine-readable failures.
- Hand off only to `reference-canon-manager` when ready.
