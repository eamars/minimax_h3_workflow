"""Compatibility compiler; require the frozen live profile before emitting a graph."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

import yaml


PLACEHOLDER = re.compile(r"^\$\{([a-zA-Z0-9_.-]+)\}$")


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
                raise AssertionError(f"missing binding {key}")
            return bindings[key]
        if "${" in value:
            raise AssertionError(f"embedded placeholder is forbidden: {value}")
    return value


def validate(graph, object_info=None):
    node_ids = set(graph)
    for node_id, node in graph.items():
        if set(node) != {"class_type", "inputs"}:
            raise AssertionError(f"node {node_id} is not ComfyUI API format")
        for value in node["inputs"].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], int) and value[0] not in node_ids:
                raise AssertionError(f"node {node_id} has dangling link {value[0]}")
    if object_info is not None:
        validator_path = Path(__file__).resolve().parents[1] / "skills" / "comfyui-workflow-compiler" / "scripts" / "validate_live_graph.py"
        spec = importlib.util.spec_from_file_location("compatibility_compiler_live_validator", validator_path)
        if spec is None or spec.loader is None:
            raise AssertionError("live validator is unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.validate(graph, object_info)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--capability-profile", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    template = json.loads(args.template.read_text(encoding="utf-8"))
    bindings = yaml.safe_load(args.bindings.read_text(encoding="utf-8"))
    profile = json.loads(args.capability_profile.read_text(encoding="utf-8"))
    object_info = profile.get("evidence", {}).get("object_info") or profile.get("object_info")
    if not object_info:
        raise AssertionError("CAPABILITY_PROBE_MISSING: object_info")
    duration = bindings.get("effective_duration_seconds")
    if duration is not None and not (0 < float(duration) <= 10):
        raise AssertionError("effective duration must be >0 and <=10 seconds")
    graph = replace(template, bindings)
    validate(graph, object_info)
    if args.output.exists():
        raise AssertionError(f"refusing to overwrite {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Compiled {len(graph)} nodes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
