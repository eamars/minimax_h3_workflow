"""Validate a ComfyUI API graph against a frozen /object_info profile."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict, deque
from pathlib import Path


PLACEHOLDER = re.compile(r"\$\{[^}]+\}")


def input_spec(node_info: dict) -> tuple[dict, set[str]]:
    inputs = node_info.get("input", {})
    required = inputs.get("required", {}) if isinstance(inputs, dict) else {}
    optional = inputs.get("optional", {}) if isinstance(inputs, dict) else {}
    merged = dict(required)
    merged.update(optional)
    return merged, set(required)


def expected_type(spec):
    if isinstance(spec, (list, tuple)) and spec:
        head = spec[0]
        if isinstance(head, str):
            return head
        if isinstance(head, list):
            return "ENUM"
    return None


def is_link(value, graph) -> bool:
    return isinstance(value, list) and len(value) == 2 and str(value[0]) in graph and isinstance(value[1], int)


def validate_literal(value, spec, label: str):
    if isinstance(value, str) and PLACEHOLDER.search(value):
        raise AssertionError(f"WORKFLOW_MAPPING_INVALID: unresolved placeholder at {label}")
    kind = expected_type(spec)
    if kind == "ENUM":
        choices = spec[0]
        if value not in choices:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} is not in live enum")
    elif kind == "COMBO":
        choices = spec[1].get("options", []) if len(spec) > 1 and isinstance(spec[1], dict) else []
        combo_options = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
        if not choices and combo_options.get("video_upload") is True:
            upload_path = Path(str(value)) if isinstance(value, str) else None
            if upload_path is None or not str(value) or upload_path.is_absolute() or ".." in upload_path.parts:
                raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be a safe relative uploaded-media path")
        elif value not in choices:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} is not in live combo")
    elif kind == "COMFY_DYNAMICCOMBO_V3":
        if not isinstance(value, str):
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be a dynamic-combo selector string")
        selector = label.rsplit(".", 1)[-1]
        options = spec[1].get("options", []) if len(spec) > 1 and isinstance(spec[1], dict) else []
        option = next((item for item in options if item.get("key") == value), None)
        if option is None:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} has unknown dynamic selection")
    elif kind in {"INT", "INTEGER"} and (not isinstance(value, int) or isinstance(value, bool)):
        raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be integer")
    elif kind in {"FLOAT", "NUMBER"} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be number")
    elif kind in {"STRING"} and not isinstance(value, str):
        raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be string")
    elif kind in {"BOOLEAN", "BOOL"} and not isinstance(value, bool):
        raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} must be boolean")
    options = spec[1] if isinstance(spec, (list, tuple)) and len(spec) > 1 and isinstance(spec[1], dict) else {}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "min" in options and value < options["min"]:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} below live minimum")
        if "max" in options and value > options["max"]:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {label} above live maximum")


def validate(graph: dict, object_info: dict):
    if not isinstance(graph, dict) or not graph:
        raise AssertionError("WORKFLOW_MAPPING_INVALID: graph must be a non-empty object")
    dependencies = defaultdict(set)
    reverse = defaultdict(set)
    output_nodes = 0
    for raw_id, node in graph.items():
        node_id = str(raw_id)
        if set(node) != {"class_type", "inputs"} or not isinstance(node["inputs"], dict):
            raise AssertionError(f"WORKFLOW_MAPPING_INVALID: invalid API node {node_id}")
        class_type = node["class_type"]
        if class_type not in object_info:
            raise AssertionError(f"WORKFLOW_NODE_UNAVAILABLE: {class_type}")
        info = object_info[class_type]
        if info.get("output_node"):
            output_nodes += 1
        specs, required = input_spec(info)
        dynamic_indices = defaultdict(list)
        for name in set(node["inputs"]) - set(specs):
            for group_name, group_spec in list(specs.items()):
                if expected_type(group_spec) != "COMFY_AUTOGROW_V3":
                    continue
                options = group_spec[1] if len(group_spec) > 1 and isinstance(group_spec[1], dict) else {}
                template = options.get("template", {})
                prefix = template.get("prefix", "")
                match = re.fullmatch(rf"{re.escape(group_name)}\.{re.escape(prefix)}([0-9]+)", name)
                if not match:
                    continue
                index = int(match.group(1))
                maximum = int(template.get("max", 0))
                if index < 0 or index >= maximum:
                    raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {name} exceeds live autogrow limit")
                template_required = template.get("input", {}).get("required", {})
                if len(template_required) != 1:
                    raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {group_name} autogrow template is ambiguous")
                specs[name] = next(iter(template_required.values()))
                dynamic_indices[group_name].append(index)
                break
        for group_name, indices in dynamic_indices.items():
            if sorted(indices) != list(range(len(indices))):
                raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {group_name} autogrow ordinals must be contiguous from zero")
        # ComfyUI's live V3 API serializes a dynamic combo as a scalar selector
        # (for example ``codec: auto``). The executor expands that selector into
        # the nested runtime object. Nested selectors, when present, remain
        # dotted graph inputs such as ``codec.encoding``.
        pending_dynamic = list(specs.items())
        expanded_dynamic = set()
        while pending_dynamic:
            dynamic_name, dynamic_spec = pending_dynamic.pop(0)
            if expected_type(dynamic_spec) != "COMFY_DYNAMICCOMBO_V3" or dynamic_name in expanded_dynamic:
                continue
            expanded_dynamic.add(dynamic_name)
            if dynamic_name not in node["inputs"]:
                continue
            selector_value = node["inputs"][dynamic_name]
            if not isinstance(selector_value, str):
                raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {class_type}.{dynamic_name} must be a dynamic-combo selector string")
            options = dynamic_spec[1].get("options", []) if len(dynamic_spec) > 1 and isinstance(dynamic_spec[1], dict) else []
            option = next((item for item in options if item.get("key") == selector_value), None)
            if option is None:
                raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {class_type}.{dynamic_name} has unknown dynamic selection")
            nested = option.get("inputs", {})
            for category in ("required", "optional"):
                for child_name, child_spec in nested.get(category, {}).items():
                    full_name = f"{dynamic_name}.{child_name}"
                    specs[full_name] = child_spec
                    if category == "required":
                        required.add(full_name)
                    pending_dynamic.append((full_name, child_spec))
        unknown = set(node["inputs"]) - set(specs)
        if unknown:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: {class_type}.{sorted(unknown)[0]}")
        missing = required - set(node["inputs"])
        if missing:
            raise AssertionError(f"WORKFLOW_INPUT_UNSUPPORTED: missing {class_type}.{sorted(missing)[0]}")
        for name, value in node["inputs"].items():
            label = f"{class_type}.{name}"
            if is_link(value, graph):
                source_id, slot = str(value[0]), value[1]
                source_info = object_info[graph[source_id]["class_type"]]
                outputs = source_info.get("output", [])
                if slot < 0 or slot >= len(outputs):
                    raise AssertionError(f"WORKFLOW_LINK_INVALID: bad output slot at {label}")
                target_kind = expected_type(specs[name])
                source_kind = outputs[slot] if slot < len(outputs) else None
                if target_kind not in {None, "ENUM", "*"} and source_kind not in {target_kind, "*"}:
                    raise AssertionError(f"WORKFLOW_LINK_INVALID: {source_kind} to {target_kind} at {label}")
                dependencies[node_id].add(source_id)
                reverse[source_id].add(node_id)
            elif isinstance(value, list) and len(value) == 2 and isinstance(value[1], int):
                raise AssertionError(f"WORKFLOW_LINK_INVALID: dangling link at {label}")
            else:
                validate_literal(value, specs[name], label)
    if output_nodes == 0:
        raise AssertionError("WORKFLOW_MAPPING_INVALID: graph has no output node")
    indegree = {str(node_id): len(dependencies[str(node_id)]) for node_id in graph}
    queue = deque(sorted(node_id for node_id, count in indegree.items() if count == 0))
    visited = 0
    while queue:
        node_id = queue.popleft()
        visited += 1
        for target in sorted(reverse[node_id]):
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(graph):
        raise AssertionError("WORKFLOW_CYCLE: graph is cyclic")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--capability-profile", type=Path, required=True)
    args = parser.parse_args()
    graph = json.loads(args.workflow.read_text(encoding="utf-8"))
    profile = json.loads(args.capability_profile.read_text(encoding="utf-8"))
    object_info = profile.get("evidence", {}).get("object_info") or profile.get("object_info")
    if not object_info:
        raise AssertionError("CAPABILITY_PROBE_MISSING: object_info")
    validate(graph, object_info)
    print(f"Validated {len(graph)} ComfyUI API nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
