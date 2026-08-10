#!/usr/bin/env python3
"""Build a deterministic N-way ComfyUI post-concat graph.

The catalog's two-input concat node remains a schema fixture.  This builder
expands the same live node pattern into an explicit chain, so an editor never
silently drops sources after the second clip or substitutes blind file concat.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def safe_relative(value: str, field: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not value:
        raise ValueError(f"{field} must be a non-empty relative path")
    return path.as_posix()


def build_graph(sources: list[str], fps: int, output_prefix: str) -> dict[str, dict]:
    if len(sources) < 2:
        raise ValueError("concat requires at least two sources")
    if fps <= 0:
        raise ValueError("fps must be positive")
    output_prefix = safe_relative(output_prefix, "output_prefix")
    sources = [safe_relative(source, "source") for source in sources]
    graph: dict[str, dict] = {}
    for index, source in enumerate(sources, start=1):
        graph[str(index)] = {"class_type": "LoadVideo", "inputs": {"file": source}}
    get_start = len(sources) + 1
    for index in range(len(sources)):
        node_id = get_start + index
        load_id = index + 1
        graph[str(node_id)] = {"class_type": "GetVideoComponents", "inputs": {"video": [str(load_id), 0]}}

    next_id = get_start + len(sources)
    image_value = [str(get_start), 0]
    audio_value = [str(get_start), 1]
    for index in range(1, len(sources)):
        image_node = next_id
        audio_node = next_id + 1
        current_get = get_start + index
        graph[str(image_node)] = {
            "class_type": "ImageBatch",
            "inputs": {"image1": image_value, "image2": [str(current_get), 0]},
        }
        graph[str(audio_node)] = {
            "class_type": "AudioConcat",
            "inputs": {"audio1": audio_value, "audio2": [str(current_get), 1], "direction": "after"},
        }
        image_value = [str(image_node), 0]
        audio_value = [str(audio_node), 0]
        next_id += 2

    create_id = next_id
    save_id = create_id + 1
    graph[str(create_id)] = {
        "class_type": "CreateVideo",
        "inputs": {"images": image_value, "audio": audio_value, "fps": fps, "bit_depth": 8},
    }
    graph[str(save_id)] = {
        "class_type": "SaveVideo",
        "inputs": {"video": [str(create_id), 0], "filename_prefix": output_prefix, "format": "auto", "codec": "auto"},
    }
    return graph


def validate_graph(graph: dict[str, dict], capability_profile: Path | dict) -> None:
    """Validate the generated graph against frozen live ComfyUI object-info."""
    validator_path = (
        Path(__file__).resolve().parents[3]
        / "skills"
        / "comfyui-workflow-compiler"
        / "scripts"
        / "validate_live_graph.py"
    )
    spec = importlib.util.spec_from_file_location("post_editor_live_graph_validator", validator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("COMFYUI_VALIDATION_FAILED: live validator unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    profile = (
        capability_profile
        if isinstance(capability_profile, dict)
        else json.loads(capability_profile.read_text(encoding="utf-8"))
    )
    object_info = profile.get("evidence", {}).get("object_info") or profile.get("object_info")
    if not object_info:
        raise RuntimeError("CAPABILITY_PROBE_MISSING: object_info")
    try:
        module.validate(graph, object_info)
    except AssertionError as error:
        raise RuntimeError(f"COMFYUI_VALIDATION_FAILED: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--output-prefix", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capability-profile", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError(f"refusing to overwrite {args.output}")
    graph = build_graph(args.source, args.fps, args.output_prefix)
    if args.capability_profile is not None:
        validate_graph(graph, args.capability_profile.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"built {len(args.source)}-way concat graph with {len(graph)} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
