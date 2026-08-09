# AI video production development status

## Approval-gated production skill system

Status: complete and contract-validated.

Implemented:

- one invokable `production-orchestrator` and 15 dedicated specialist skills;
- normalized request, canon, plot, performance, sound, storyboard, animatic,
  and independent preflight planning packages;
- the complete two-file review-document contract and explicit human approval
  bound to the authoritative production-plan SHA-256;
- MiniMax H3 prompt packets, exact endpoint/handoff preparation, live ComfyUI
  capability probing, typed API-workflow compilation, and production DAGs;
- render execution, independent continuity QC, localized repair, post assembly,
  independent final QC, and hashed delivery manifests;
- shared JSON Schemas, stable IDs, immutable revisions, failure taxonomy,
  deterministic workflow catalog, install script, and contract validators;
- a strict positive/10-second maximum target and effective generation-segment
  duration, with longer shots represented as approved-tail dependency chains.

Validation commands:

```powershell
python scripts\validate_production_system.py
python skills\production-orchestrator\scripts\validate_package.py
python -m unittest tests.unit.test_system_contracts -v
```

Operational model:

1. Invoke `$production-orchestrator` with a general video idea and any asset
   roles. It defaults to `PLAN_ONLY` and writes the complete Markdown/YAML
   review pair, then stops at `PLAN_REVIEW_READY`.
2. Approve the exact authoritative YAML content hash.
3. Invoke `COMPILE_APPROVED_PLAN`; the system probes live ComfyUI capabilities,
   freezes the catalog/profile, compiles H3 packets and typed API workflows,
   and validates the DAG without queueing.
4. Execution is a separate authorized stage. Every render goes through QC;
   repairs are localized and revisioned; only QC-PASS media may enter post;
   delivery requires an independent final-QC PASS.

Live ComfyUI `/object_info`, `/models`, and `/system_stats` remain authoritative
at compilation time. Installed nodes/models can change after repository
validation, so capability probing is intentionally a required runtime gate.
