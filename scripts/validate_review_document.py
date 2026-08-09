"""Validate the exact production review pair and its authoritative content hash."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def canonical_hash(plan: dict) -> str:
    value = copy.deepcopy(plan)
    artifact = value.get("artifact", {})
    for key in ("content_hash", "status", "superseded_by"):
        artifact.pop(key, None)
    approval = value.get("approval", {})
    for key in ("approved_at", "approved_by", "plan_hash", "status", "approved_scope", "conditions"):
        approval.pop(key, None)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=lambda item: item.isoformat()).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--yaml", type=Path, required=True)
    args = parser.parse_args()
    plan = yaml.safe_load(args.yaml.read_text(encoding="utf-8"))
    version = plan.get("planning_model_version", 1)
    if version == 2:
        contract_path = ROOT / "skills/production-orchestrator/references/review-document-contract-v2.yaml"
        schema_path = ROOT / "schemas/production-plan-v2.schema.json"
        if "handoffs" in plan:
            raise AssertionError("v2 review YAML cannot use the legacy handoffs field")
    else:
        contract_path = ROOT / "skills/production-orchestrator/references/review-document-contract.yaml"
        schema_path = ROOT / "schemas/production-plan.schema.json"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    plan_schema = json.loads(schema_path.read_text(encoding="utf-8"))
    missing = set(plan_schema["required"]) - set(plan)
    if missing:
        raise AssertionError(f"review YAML missing fields: {sorted(missing)}")
    if plan["artifact"].get("status") != contract["status_before_human_approval"]:
        raise AssertionError("review YAML status must be review_ready")
    expected_hash = canonical_hash(plan)
    if plan["artifact"].get("content_hash") != expected_hash or plan["approval"].get("plan_hash") != expected_hash:
        raise AssertionError(f"review hash mismatch; expected {expected_hash}")
    if plan["approval"].get("status") != "pending":
        raise AssertionError("review approval placeholder must be pending")
    markdown = args.markdown.read_text(encoding="utf-8")
    headings = re.findall(r"(?m)^## (.+?)\s*$", markdown)
    if headings != contract["required_sections"]:
        raise AssertionError("review Markdown headings do not exactly match the 20-section contract")
    if args.markdown.stem != args.yaml.stem:
        raise AssertionError("review pair filenames must share a revision stem")
    print(f"Validated review pair {args.yaml}: {expected_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
