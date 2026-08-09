from __future__ import annotations

import sys
from pathlib import Path

import yaml


FORBIDDEN = {"plot", "plot_beats", "scene", "shot", "camera", "blocking", "canon", "prompt_packet"}


def fail(message: str) -> None:
    raise AssertionError(message)


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: validate_request.py project-request.yaml assumptions.md open-decisions.yaml")
    request_path, assumptions_path, decisions_path = map(Path, sys.argv[1:])
    request = yaml.safe_load(request_path.read_text(encoding="utf-8"))
    assumptions_path.read_text(encoding="utf-8")
    yaml.safe_load(decisions_path.read_text(encoding="utf-8"))
    required = {"artifact", "project_id", "request", "constraints", "asset_inputs", "execution", "policy", "normalization"}
    if not required <= set(request): fail(f"missing sections: {sorted(required - set(request))}")
    if request["policy"].get("max_generation_segment_seconds") != 10: fail("segment cap must be 10")
    execution = request["execution"]
    if execution.get("effective_mode") != "PLAN_ONLY": fail("intake mode must be PLAN_ONLY")
    if execution.get("compile_authorized") or execution.get("render_authorized"): fail("intake cannot authorize production")
    normalization = request["normalization"]
    if normalization.get("next_skill") != "reference-canon-manager": fail("invalid handoff target")
    if normalization.get("handoff_ready") and (normalization.get("blocking_decisions") or normalization.get("failure_codes")): fail("invalid ready state")
    if FORBIDDEN & set(walk_keys(request)): fail("downstream-owned field present")
    print("Validated request-normalizer outputs")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
