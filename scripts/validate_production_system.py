"""Validate the AI-video production skill system without third-party JSON Schema tooling."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REQUIRED_SKILLS = [
    "request-normalizer", "reference-canon-manager", "plot-architect",
    "scene-performance-writer", "sound-dialogue-planner", "storyboard-director",
    "animatic-previs-planner", "production-preflight-reviewer", "minimax-h3-adapter",
    "keyframe-handoff-builder", "comfyui-workflow-compiler", "render-orchestrator",
    "continuity-qc-supervisor", "repair-director", "post-editor",
]
REQUIRED_SECTIONS = [
    "Mission", "Ownership boundary", "Inputs", "Required outputs",
    "Processing method", "Invariants", "Non-responsibilities", "Failure conditions",
    "Validation rules", "Minimal example", "Adversarial example", "Acceptance tests",
]
PLANNING_ORDER = REQUIRED_SKILLS[:8]
COMPILATION_ORDER = ["minimax-h3-adapter", "keyframe-handoff-builder", "comfyui-workflow-compiler"]


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def frontmatter(path: Path) -> dict:
    parts = path.read_text(encoding="utf-8").split("---", 2)
    check(len(parts) == 3, f"{path}: missing frontmatter")
    return yaml.safe_load(parts[1])


def validate_skill(name: str) -> None:
    package = SKILLS / name
    skill_path = package / "SKILL.md"
    contract_path = package / "references" / "skill-contract.yaml"
    agent_path = package / "agents" / "openai.yaml"
    check(skill_path.is_file(), f"missing {name}/SKILL.md")
    check(contract_path.is_file(), f"missing {name}/references/skill-contract.yaml")
    check(agent_path.is_file(), f"missing {name}/agents/openai.yaml")
    meta = frontmatter(skill_path)
    check(set(meta) == {"name", "description"}, f"{name}: frontmatter keys")
    check(meta["name"] == name, f"{name}: frontmatter/folder mismatch")
    check(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None, f"{name}: invalid name")
    body = skill_path.read_text(encoding="utf-8")
    check("TODO" not in body, f"{name}: unresolved TODO")
    positions = []
    for section in REQUIRED_SECTIONS:
        match = re.search(rf"^## {re.escape(section)}\s*$", body, re.MULTILINE | re.IGNORECASE)
        check(match is not None, f"{name}: missing section {section}")
        positions.append(match.start())
    check(positions == sorted(positions), f"{name}: required sections out of order")
    check(len(body.splitlines()) <= 500, f"{name}: SKILL.md exceeds 500 lines")
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    for field in ("name", "version", "stage", "mode", "consumes", "produces", "side_effects", "approval_required", "may_modify_upstream_decisions", "owner"):
        check(field in contract, f"{name}: contract missing {field}")
    check(contract["name"] == name and contract["owner"] == name, f"{name}: contract owner/name mismatch")
    check(contract["may_modify_upstream_decisions"] is False, f"{name}: may modify upstream decisions")
    package_contract = yaml.safe_load((SKILLS / "production-orchestrator" / "references" / "skill-package-contract.yaml").read_text(encoding="utf-8"))
    enums = package_contract["sidecar"]["enums"]
    for key in ("stage", "mode", "side_effects"):
        check(contract[key] in enums[key], f"{name}: invalid {key} {contract[key]}")
    approval_values = package_contract["sidecar"]["invariants"]["approval_required_values"]
    check(contract["approval_required"] in approval_values, f"{name}: invalid approval_required {contract['approval_required']}")
    agent = yaml.safe_load(agent_path.read_text(encoding="utf-8"))
    interface = agent["interface"]
    check(25 <= len(interface["short_description"]) <= 64, f"{name}: invalid short description")
    check(f"${name}" in interface["default_prompt"], f"{name}: default prompt missing skill token")


def validate_schemas() -> None:
    schema_dir = ROOT / "schemas"
    required = [
        "project-request.schema.json", "asset-manifest.schema.json", "canon-lock.schema.json",
        "plot-package.schema.json", "scene-performance.schema.json", "sound-plan.schema.json",
        "storyboard-package.schema.json", "animatic-plan.schema.json", "preflight-report.schema.json",
        "production-plan.schema.json", "approval-record.schema.json", "h3-prompt-packet.schema.json",
        "storyboard-package-v2.schema.json", "production-plan-v2.schema.json", "animatic-plan-v2.schema.json",
        "h3-prompt-packet-v2.schema.json", "edit-decision-list-v2.schema.json", "camera-plan.schema.json", "scene-geography.schema.json",
        "continuity-state.schema.json", "editorial-boundary.schema.json", "generation-handoff.schema.json",
        "keyframe-job.schema.json", "comfyui-job.schema.json", "production-dag.schema.json",
        "keyframe-job-v2.schema.json", "comfyui-job-v2.schema.json", "production-dag-v2.schema.json", "qc-report-v2.schema.json", "sound-plan-v2.schema.json",
        "render-report.schema.json", "qc-report.schema.json", "repair-plan.schema.json",
        "edit-decision-list.schema.json", "delivery-manifest.schema.json", "project-state.schema.json",
    ]
    for name in required:
        path = schema_dir / name
        check(path.is_file(), f"missing schema {name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        check(data.get("$schema", "").endswith("2020-12/schema"), f"{name}: wrong draft")
    storyboard = json.loads((schema_dir / "storyboard-package.schema.json").read_text(encoding="utf-8"))
    segment_ref = json.dumps(storyboard)
    check("generationSegment" in segment_ref, "storyboard schema missing generation segment contract")
    common = json.loads((schema_dir / "common-defs.schema.json").read_text(encoding="utf-8"))
    duration = common["$defs"]["generationSegment"]["properties"]["duration_seconds"]
    check(duration.get("exclusiveMinimum") == 0 and duration.get("maximum") == 10, "segment duration contract invalid")
    cinematic_segment = common["$defs"]["generationSegmentV2"]
    check(set(("scene_time", "source_time", "record_time", "camera_interval_map", "generation_handoff_to_next")) <= set(cinematic_segment["required"]), "v2 segment contract missing cinematic fields")
    v2_storyboard = json.loads((schema_dir / "storyboard-package-v2.schema.json").read_text(encoding="utf-8"))
    check(v2_storyboard["properties"]["planning_model_version"].get("const") == 2, "v2 storyboard model version missing")
    check("editorial_boundaries" in v2_storyboard["required"] and "generation_handoffs" in v2_storyboard["required"], "v2 boundary split missing")
    job_v2 = json.loads((schema_dir / "comfyui-job-v2.schema.json").read_text(encoding="utf-8"))
    check(job_v2["properties"]["planning_model_version"].get("const") == 2, "v2 job model version missing")
    check({"shot_id", "segment_id", "camera_interval_map", "continuity_contract"} <= set(job_v2["required"]), "v2 job traceability fields missing")
    dag_v2 = json.loads((schema_dir / "production-dag-v2.schema.json").read_text(encoding="utf-8"))
    check("edges" not in dag_v2["properties"] and "generation_edges" in dag_v2["required"], "v2 DAG must separate generation and editorial topology")
    dag_relations = dag_v2["properties"]["generation_edges"]["items"]["properties"]["relation"]["enum"]
    check("continue" not in dag_relations and "bridge" not in dag_relations, "v2 DAG contains legacy edge relations")
    qc_v2 = json.loads((schema_dir / "qc-report-v2.schema.json").read_text(encoding="utf-8"))
    check({"camera_path", "generation_handoff", "editorial_boundary"} <= set(qc_v2["properties"]["mode"]["enum"]), "v2 QC modes are incomplete")


def validate_graph(graph: dict, label: str) -> None:
    check(isinstance(graph, dict) and graph, f"{label}: empty graph")
    node_ids = set(graph)
    for node_id, node in graph.items():
        check(set(node) == {"class_type", "inputs"}, f"{label}: node {node_id} is not API format")
        check(isinstance(node["class_type"], str) and node["class_type"], f"{label}: empty node type")
        for value in node["inputs"].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], int):
                check(value[0] in node_ids, f"{label}: dangling link {value[0]}")


def validate_catalog() -> None:
    root = ROOT / "workflow-catalog"
    catalog = yaml.safe_load((root / "catalog.yaml").read_text(encoding="utf-8"))
    expected = {"h3_t2va_api.json", "h3_i2va_api.json", "h3_fl2va_api.json", "h3_l2va_api.json", "h3_r2va_api.json", "still_keyframe_api.json", "frame_extract_api.json", "bridge_api.json", "concat_api.json", "audio_mix_api.json", "upscale_api.json"}
    actual = {Path(item["file"]).name for item in catalog["templates"]}
    check(expected == actual, f"workflow catalog mismatch: {sorted(expected ^ actual)}")
    required_fields = set(catalog["required_catalog_fields"])
    for item in catalog["templates"]:
        missing = required_fields - set(item)
        check(not missing, f"{item.get('template_id', 'unknown')}: catalog fields missing {sorted(missing)}")
        path = root / item["file"]
        validate_graph(json.loads(path.read_text(encoding="utf-8")), item["template_id"])


def validate_routing() -> None:
    routing = yaml.safe_load((SKILLS / "production-orchestrator" / "references" / "routing-policy.yaml").read_text(encoding="utf-8"))
    skills = [item["skill"] for item in routing["planning_dispatch"] if item.get("type") == "skill"]
    check(skills == PLANNING_ORDER, f"planning order mismatch: {skills}")
    order = routing["compilation_dispatch"]["order"]
    flattened = [item if isinstance(item, str) else item.get("skill") for item in order]
    for skill in COMPILATION_ORDER:
        check(skill in flattened, f"compilation routing missing {skill}")
    check(routing["default_mode"] == "PLAN_ONLY", "default mode must be PLAN_ONLY")
    registry_path = SKILLS / "production-orchestrator" / "references" / "specialist-registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    check(set(registry["specialists"]) == set(REQUIRED_SKILLS), "specialist registry mismatch")
    for name, entry in registry["specialists"].items():
        resolved = (registry_path.parent / entry["path"]).resolve()
        check(resolved == (SKILLS / name / "SKILL.md").resolve(), f"registry path mismatch for {name}: {resolved}")
        check(resolved.is_file(), f"registry path missing for {name}: {resolved}")
    taxonomy = yaml.safe_load((registry_path.parent / "failure-taxonomy.yaml").read_text(encoding="utf-8"))
    codes = [entry["code"] for entry in taxonomy["failures"]]
    check(len(codes) == len(set(codes)), "failure taxonomy contains duplicate codes")


def main() -> int:
    argparse.ArgumentParser().parse_args()
    for skill in REQUIRED_SKILLS:
        validate_skill(skill)
    validate_schemas()
    validate_catalog()
    validate_routing()
    print(f"Validated {len(REQUIRED_SKILLS)} specialist skills, shared schemas, workflow catalog, and routing")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
