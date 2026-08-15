"""Validate the automatic production-orchestrator skill package."""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment diagnostic
    raise SystemExit("PyYAML is required to validate this skill package") from exc


PACKAGE = Path(__file__).resolve().parents[1]
REFERENCES = PACKAGE / "references"


def load_yaml(name: str):
    path = REFERENCES / name
    if not path.is_file():
        raise AssertionError(f"missing reference: {path}")
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    frontmatter_parts = (PACKAGE / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
    check(len(frontmatter_parts) == 3, "SKILL.md must have YAML frontmatter")
    frontmatter = yaml.safe_load(frontmatter_parts[1])
    check(set(frontmatter) == {"name", "description"}, "frontmatter must contain only name and description")
    name = frontmatter["name"]
    check(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None, "invalid skill name")
    check(name == PACKAGE.name, "skill folder and frontmatter name must match")

    interface = yaml.safe_load((PACKAGE / "agents" / "openai.yaml").read_text(encoding="utf-8"))["interface"]
    check(f"${name}" in interface["default_prompt"], "default_prompt must mention the skill")
    check(25 <= len(interface["short_description"]) <= 64, "short_description must be 25-64 characters")

    package_contract = load_yaml("skill-package-contract.yaml")
    instance_contract = load_yaml("skill-contract.yaml")
    for field in package_contract["sidecar"]["required_fields"]:
        check(field in instance_contract, f"skill-contract missing {field}")
    check(instance_contract["may_modify_upstream_decisions"] is False, "orchestrator cannot modify upstream decisions")

    routing = load_yaml("routing-policy.yaml")
    check(routing["default_mode"] == "FULL_PIPELINE", "default mode must be FULL_PIPELINE")
    check(routing["segment_policy"]["maximum_duration_seconds"] == 10, "segment cap must be 10 seconds")
    generation = routing["generation_handoff_policy"]
    check(set(generation["allowed_relationships"]) == {"independent", "same_shot_continue", "endpoint_bridge", "reference_reestablish", "terminal"}, "generation relationships are invalid")
    continuation = generation["same_shot_continue"]["dependency_order"]
    check(continuation.index("qc_predecessor") < continuation.index("validate_endpoint"), "QC must precede endpoint validation")
    check(continuation.index("validate_endpoint") < continuation.index("compile_successor"), "endpoint validation must precede successor compilation")
    check(continuation.index("compile_successor") < continuation.index("render_successor"), "successor compilation must precede successor render")
    continuity = routing["continuity_profile"]
    check(continuity["frame_relay"] == "predecessor_actual_final_frame", "continuity must relay the actual final frame")
    check(continuity["serial_continuations"] is True, "continuations must serialize")

    state_machine = load_yaml("state-machine.yaml")
    ready_transition = next(
        transition
        for transition in state_machine["transitions"]
        if transition["from"] == "PLAN_PREFLIGHT" and transition["to"] == "PLAN_READY"
    )
    check("preflight_pass" in ready_transition["requires"], "automated preflight transition is missing")

    metadata = load_yaml("artifact-metadata.yaml")
    rules = metadata["rules"]
    check(any("revision IDs" in rule for rule in rules), "revision identity rule is missing")
    check(any("file-integrity" in rule for rule in rules), "technical integrity rule is missing")

    taxonomy = load_yaml("failure-taxonomy.yaml")
    codes = {failure["code"] for failure in taxonomy["failures"]}
    required = {
        "SEGMENT_TOO_LONG", "HANDOFF_UNSPECIFIED",
        "WORKFLOW_NODE_UNAVAILABLE", "HANDOFF_TAIL_INVALID",
        "HANDOFF_MISMATCH", "EDITORIAL_GENERATION_BOUNDARY_CONFLATED", "CAMERA_MODEL_OPAQUE", "ARTIFACT_OVERWRITE_FORBIDDEN",
    }
    check(required <= codes, f"failure taxonomy missing {sorted(required - codes)}")
    check(len(codes) == len(taxonomy["failures"]), "failure taxonomy contains duplicate codes")

    naming = load_yaml("naming-conventions.yaml")
    for definition in naming["stable_ids"].values():
        check(re.fullmatch(definition["regex"], definition["example"]) is not None, f"ID example does not match {definition['regex']}")

    print(f"Validated {PACKAGE.name} skill package")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
