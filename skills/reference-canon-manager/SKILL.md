---
name: reference-canon-manager
description: Lock user-supplied seed images, video, and audio references into traceable asset roles, canonical identity/environment anchors, endpoint declarations, conflict reports, and deterministic handoff metadata. Use when a video plan contains seed assets, exact first/last frames, continuation handoffs, reference conflicts, or canon consistency requirements.
---

# Reference and Canon Manager

## Mission

Lock supplied seed media as the visual source of truth. Extract only observable, traceable anchors and declared reference roles. Produce a conflict-aware canon package without inventing designs or story content.

## Ownership boundary

Own asset provenance, raw-byte SHA-256 hashes, media metadata, reference roles, timeline scope, priority, canon grouping, textual anchors, endpoint declarations, conflicts, and reference ordering. Let Plot Architect own what happens and why; allow no downstream skill to rewrite the lock silently.

## Inputs

Consume a valid project request, readable user seed media, optional declared meanings/priorities/scopes/endpoints, and an optional prior canon revision. Read [canon rules](references/canon-rules.yaml), [skill contract](references/skill-contract.yaml), and the shared artifact and failure contracts before processing.

## Required outputs

Create `asset-manifest.yaml`, `canon-lock.yaml`, `reference-conflict-report.yaml`, and `reference-order.yaml`. Wrap every artifact in shared metadata and return:

```yaml
status: PASS | WARN | BLOCKED
failure_codes: []
affected_scopes: []
artifact_revisions: []
plot_handoff: {ready: true, blocking_scopes: []}
```

## Processing method

1. Resolve every source without copying, renaming, cropping, re-encoding, or stripping metadata.
2. Hash raw bytes and collect deterministic media metadata.
3. Preserve prior stable IDs when the source hash is unchanged; otherwise derive deterministic asset IDs.
4. Assign one primary role and only explicitly declared compatible secondary roles. Keep endpoint meaning separate.
5. Group assets into canonical subjects, worlds, styles, wardrobes, props, compositions, motions, or audio references.
6. Record observable locked anchors and non-binding pose, expression, lighting, action, or incidental content separately.
7. Detect role, identity, environment, endpoint, scope, priority, and aspect-ratio conflicts.
8. Preserve explicit priority and never resolve ambiguity by filename, order, recency, confidence, or taste.
9. Produce deterministic role-specific ordering and H3 candidate labels without encoding endpoint semantics into them.
10. Mark handoff ready only for scopes with no unresolved blocking conflict.

## Invariants

- Treat original seed bytes as immutable.
- Record source hashes as `sha256:` plus 64 lowercase hexadecimal characters.
- Keep `role` and `endpoint_role` orthogonal.
- Default endpoints to `none`; require explicit evidence for first, last, or both.
- Separate identity/design from pose, expression, action, lighting, and incidental subjects.
- Put an incidental person in an environment reference under `must_not_transfer` unless explicitly assigned.
- Keep unresolved conflicts visible and scoped.
- Preserve stable IDs, provenance, priorities, source hashes, and immutable revisions.

## Non-responsibilities

Do not invent plot, motivation, action, dialogue, blocking, camera language, shots, prompts, workflows, repairs, or edits. Do not redesign, mutate, normalize, or prepare endpoint media. Delegate derived endpoint preparation to Keyframe and Handoff Builder.

## Failure conditions

Return a shared failure code, affected IDs/scopes, evidence, and owner. Use `REQUIRED_ASSET_MISSING`, `ASSET_HASH_MISMATCH`, or `ASSET_SOURCE_MUTATION_DETECTED` for source failures; `ASSET_ROLE_AMBIGUOUS` for incompatible roles; `ENDPOINT_ROLE_AMBIGUOUS` for ambiguous endpoint claims; `CANON_REFERENCE_CONFLICT` for unresolved overlapping canon claims; and `CANON_ID_COLLISION`, `CANON_OUTPUT_INVALID`, `REFERENCE_ORDER_INVALID`, or `PROVENANCE_MISSING` for contract failures.

## Validation rules

- Recompute raw-byte hashes without writing source assets.
- Reject absolute authoritative paths, traversal, missing files, ambiguous `latest` aliases, duplicate IDs, and invalid media-role combinations.
- Verify every canon asset and order entry resolves to the manifest with the same hash.
- Require explicit endpoint evidence and reject audio endpoints.
- Require `plot_handoff.ready: false` for affected blocking scopes.
- Validate against `schemas/asset-manifest.schema.json` and `schemas/canon-lock.schema.json`.
- Run `python scripts/validate_reference_canon.py --project-root <root> --asset-manifest <path> --canon-lock <path> --conflicts <path> --order <path>`.

## Minimal example

For four expression images of one character, a shower environment, and a declared opening still, group the character images into one identity canon with four non-binding performance observations, prevent the environment's incidental person from transfer, and mark only the declared opening still as `first_frame`.

## Adversarial example

For equal-priority character references with incompatible hair and costume in the same scope, preserve both assets, return `CANON_REFERENCE_CONFLICT`, and block only the affected scope. Keep a merely opening-like image at endpoint `none` unless explicitly declared.

## Acceptance tests

- Group expression variants without forcing source emotion.
- Prevent incidental-subject leakage.
- Distinguish explicit endpoints from general references.
- Scope contradictory hair, wardrobe, and environment conflicts.
- Keep deterministic ordering independent of input order.
- Detect source-byte changes and path violations.
- Preserve prior IDs for unchanged sources.
- Warn on aspect mismatch without source mutation.
- Hand Plot Architect only locked canon, roles, scope, conflicts, and explicit endpoints.
