"""Validate the v2 planning topology for a storyboard or production plan."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STORYBOARD_VALIDATOR = ROOT / ".agents/skills/storyboard-director/scripts/validate_storyboard.py"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def load_storyboard_validator():
    spec = importlib.util.spec_from_file_location("cinematic_storyboard_validator", STORYBOARD_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load storyboard validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_plan(plan: dict) -> None:
    if plan.get("planning_model_version") != 2:
        raise ValueError("V2_VERSION_REQUIRED: planning_model_version must be 2")
    required = {"director_treatment", "scene_geography", "shots", "generation_segments", "editorial_boundaries", "generation_handoffs", "continuity_registry", "animatic_intent", "creative_acceptance_tests"}
    missing = required - set(plan)
    if missing:
        raise ValueError(f"STORYBOARD_INPUT_SCHEMA_INVALID: missing {sorted(missing)}")
    if "handoffs" in plan:
        raise ValueError("EDITORIAL_GENERATION_BOUNDARY_CONFLATED: legacy handoffs field is forbidden")
    module = load_storyboard_validator()
    module.validate_v2(plan)
    for segment in plan["generation_segments"]:
        if any(field not in segment for field in ("scene_time", "source_time", "record_time", "camera_interval_map", "generation_handoff_to_next")):
            raise ValueError(f"TIME_DOMAIN_MISSING: {segment.get('segment_id', 'unknown')}")
        if any(field in segment for field in ("transition_to_next", "dominant_camera_move", "primary_performance_arc")):
            raise ValueError(f"EDITORIAL_GENERATION_BOUNDARY_CONFLATED: {segment.get('segment_id', 'unknown')}")
    for boundary in plan["editorial_boundaries"]:
        if boundary.get("mechanism") not in {"cut", "dissolve", "fade", "end"}:
            raise ValueError(f"TRANSITION_SEMANTICS_INVALID: {boundary.get('boundary_id', 'unknown')}")
    for handoff in plan["generation_handoffs"]:
        if handoff.get("relationship") not in {"independent", "same_shot_continue", "endpoint_bridge", "reference_reestablish", "terminal"}:
            raise ValueError(f"GENERATION_RELATIONSHIP_INVALID: {handoff.get('handoff_id', 'unknown')}")
        if "mechanism" in handoff:
            raise ValueError(f"EDITORIAL_GENERATION_BOUNDARY_CONFLATED: {handoff.get('handoff_id', 'unknown')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storyboard", type=Path)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    if bool(args.storyboard) == bool(args.plan):
        parser.error("provide exactly one of --storyboard or --plan")
    try:
        if args.storyboard:
            module = load_storyboard_validator()
            module.validate_v2(load(args.storyboard))
        else:
            validate_plan(load(args.plan))
        print("PASS: v2 cinematic package topology is valid")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI turns contract failures into deterministic FAIL output
        if not isinstance(exc, (OSError, ValueError, yaml.YAMLError)) and exc.__class__.__name__ != "ContractError":
            raise
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
