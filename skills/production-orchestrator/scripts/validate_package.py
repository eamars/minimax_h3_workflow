"""Validate the self-contained production-orchestrator skill package.

This is a deterministic validator for the approval-gated real-cinematic
orchestrator contract. Detailed artifact validation belongs to the specialist
validators, but topology and lifecycle invariants are checked here.
"""

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
    check(routing["default_mode"] == "PLAN_ONLY", "default mode must be PLAN_ONLY")
    check(routing["segment_policy"]["maximum_duration_seconds"] == 10, "segment cap must be 10 seconds")
    check(set(routing["editorial_boundary_policy"]["allowed_mechanisms"]) == {"cut", "dissolve", "fade", "end"}, "editorial boundary mechanisms are invalid")
    generation = routing["generation_handoff_policy"]
    check(set(generation["allowed_relationships"]) == {"independent", "same_shot_continue", "endpoint_bridge", "reference_reestablish", "terminal"}, "generation relationships are invalid")
    continuation = generation["same_shot_continue"]["dependency_order"]
    check(continuation.index("qc_predecessor") < continuation.index("evaluate_declared_endpoint_policy"), "QC must precede endpoint-policy evaluation")
    check(continuation.index("evaluate_declared_endpoint_policy") < continuation.index("compile_successor_job"), "endpoint-policy evaluation must precede successor compilation")
    check(continuation.index("compile_successor_job") < continuation.index("render_successor"), "successor compilation must precede successor render")

    approval_policy = load_yaml("approval-invalidation-policy.yaml")
    technical_rule = approval_policy["change_control"]["technical_only_changes"]["rule"]
    check("camera" in technical_rule and "continuity" in technical_rule and "editorial" in technical_rule, "technical resegmentation rule does not protect creative fields")

    state_machine = load_yaml("state-machine.yaml")
    approval_transition = next(
        transition
        for transition in state_machine["transitions"]
        if transition["from"] == "PLAN_REVIEW_READY" and transition["to"] == "PLAN_APPROVED"
    )
    check("human_approval_matches_plan_hash" in approval_transition["requires"], "approval/hash gate is missing")
    forbidden = {(item["from"], item["to"]) for item in state_machine["forbidden_transitions"]}
    check(("PLAN_REVIEW_READY", "COMPILING") in forbidden, "review-to-compile bypass is not blocked")

    metadata = load_yaml("artifact-metadata.yaml")
    duration_rules = metadata["conditional_fields"]["generated_media"]["duration_rules"]
    check(any("effective_duration_seconds" in rule for rule in duration_rules), "effective duration rule is missing")
    check(any("post-trim" in rule for rule in duration_rules), "post-trim handoff rule is missing")

    taxonomy = load_yaml("failure-taxonomy.yaml")
    codes = {failure["code"] for failure in taxonomy["failures"]}
    required = {
        "SEGMENT_TOO_LONG", "HANDOFF_UNSPECIFIED", "PLAN_APPROVAL_REQUIRED",
        "PLAN_HASH_MISMATCH", "WORKFLOW_NODE_UNAVAILABLE", "HANDOFF_TAIL_UNAPPROVED",
        "HANDOFF_MISMATCH", "EDITORIAL_GENERATION_BOUNDARY_CONFLATED", "CAMERA_MODEL_OPAQUE", "APPROVED_ARTIFACT_OVERWRITE_FORBIDDEN",
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
