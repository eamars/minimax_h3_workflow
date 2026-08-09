"""Approval-gated, live-profile-validated ComfyUI workflow compiler."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from validate_live_graph import validate as validate_live_graph


PLACEHOLDER = re.compile(r"^\$\{([A-Za-z0-9_.-]+)\}$")


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def canonical_hash(value) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=lambda item: item.isoformat()).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def authoritative_hash(document: dict) -> str:
    value = copy.deepcopy(document)
    artifact = value.get("artifact", {})
    for key in ("content_hash", "status", "superseded_by"):
        artifact.pop(key, None)
    approval = value.get("approval", {})
    for key in ("approved_at", "approved_by", "plan_hash", "status", "approved_scope", "conditions"):
        approval.pop(key, None)
    return canonical_hash(value)


def replace(value, bindings):
    if isinstance(value, dict):
        return {key: replace(child, bindings) for key, child in value.items()}
    if isinstance(value, list):
        return [replace(child, bindings) for child in value]
    if isinstance(value, str):
        match = PLACEHOLDER.fullmatch(value)
        if match:
            key = match.group(1)
            if key not in bindings:
                raise AssertionError(f"WORKFLOW_MAPPING_INVALID: missing binding {key}")
            return bindings[key]
        if "${" in value:
            raise AssertionError(f"WORKFLOW_MAPPING_INVALID: embedded placeholder {value}")
    return value


def all_installed_models(profile: dict) -> set[str]:
    models = profile.get("evidence", {}).get("models") or profile.get("models") or {}
    result = set()
    for values in models.values():
        if isinstance(values, list):
            result.update(str(value) for value in values)
    return result


def validate_gate(plan: dict, approval: dict):
    artifact = plan.get("artifact", {})
    if artifact.get("status") != "approved" or approval.get("status") != "approved":
        raise AssertionError("PLAN_APPROVAL_REQUIRED")
    declared = artifact.get("content_hash")
    if not declared or approval.get("plan_hash") != declared:
        raise AssertionError("PLAN_HASH_MISMATCH")
    actual = authoritative_hash(plan)
    if actual != declared:
        raise AssertionError(f"PLAN_HASH_MISMATCH: declared {declared}, computed {actual}")


def validate_bindings(bindings: dict, entry: dict, profile: dict):
    missing = set(entry["input_bindings"]) - set(bindings)
    if missing:
        raise AssertionError(f"WORKFLOW_MAPPING_INVALID: missing {sorted(missing)}")
    effective = float(bindings.get("effective_duration_seconds", 0))
    if not 0 < effective <= 10:
        raise AssertionError("SEGMENT_TOO_LONG: effective duration must be >0 and <=10")
    target = float(bindings.get("target_duration_seconds", effective))
    if not 0 < target <= 10:
        raise AssertionError("SEGMENT_TOO_LONG: target duration must be >0 and <=10")
    model_frames = int(bindings.get("model_frame_count", 0))
    effective_frames = int(bindings.get("effective_frame_count", 0))
    if model_frames <= 0 or model_frames % 17 != 5 or effective_frames <= 0 or effective_frames > model_frames:
        raise AssertionError("INVALID_FRAME_GRID")
    if abs(effective_frames / 24.0 - effective) > 1 / 24.0:
        raise AssertionError("INVALID_FRAME_GRID: effective frames/duration disagree")
    width, height = int(bindings.get("width", 0)), int(bindings.get("height", 0))
    if width <= 0 or height <= 0 or width % 32 or height % 32:
        raise AssertionError("RESOLUTION_UNSUPPORTED")
    installed = all_installed_models(profile)
    for field in entry.get("required_models", []):
        filename = bindings.get(field)
        if filename and str(filename) not in installed:
            raise AssertionError(f"REQUIRED_MODEL_MISSING: {filename}")
    for key, value in bindings.items():
        if key.endswith("_path") and value:
            path = Path(str(value))
            if path.is_absolute() or ".." in path.parts:
                raise AssertionError(f"OUTPUT_PATH_UNSAFE: {value}")
            if not path.is_file():
                raise AssertionError(f"REQUIRED_ASSET_MISSING: {value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--catalog-root", type=Path, required=True)
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--capability-profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        raise AssertionError("APPROVED_ARTIFACT_OVERWRITE_FORBIDDEN")

    plan, approval = load(args.plan), load(args.approval)
    validate_gate(plan, approval)
    catalog = load(args.catalog_root / "catalog.yaml")
    entries = {item["template_id"]: item for item in catalog["templates"]}
    if args.template_id not in entries:
        raise AssertionError(f"WORKFLOW_TEMPLATE_MISSING: {args.template_id}")
    entry = entries[args.template_id]
    bindings, profile = load(args.bindings), load(args.capability_profile)
    if not profile.get("profile_hash") or not (profile.get("evidence", {}).get("object_info") or profile.get("object_info")):
        raise AssertionError("CAPABILITY_PROBE_MISSING")
    validate_bindings(bindings, entry, profile)
    template_path = args.catalog_root / entry["file"]
    if not template_path.is_file():
        raise AssertionError(f"WORKFLOW_TEMPLATE_MISSING: {template_path}")
    graph = replace(load(template_path), bindings)
    object_info = profile.get("evidence", {}).get("object_info") or profile.get("object_info")
    validate_live_graph(graph, object_info)

    payload = json.dumps(graph, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    report = {
        "status": "PASS",
        "template_id": args.template_id,
        "plan_hash": approval["plan_hash"],
        "capability_profile_hash": profile["profile_hash"],
        "catalog_hash": canonical_hash(catalog),
        "workflow_hash": "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "target_duration_seconds": float(bindings.get("target_duration_seconds", bindings["effective_duration_seconds"])),
        "model_frame_count": int(bindings["model_frame_count"]),
        "effective_frame_count": int(bindings["effective_frame_count"]),
        "effective_duration_seconds": float(bindings["effective_duration_seconds"]),
        "output": args.output.as_posix(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    args.report.write_text(yaml.safe_dump(report, sort_keys=True, allow_unicode=True), encoding="utf-8")
    print(report["workflow_hash"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Compilation blocked: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
