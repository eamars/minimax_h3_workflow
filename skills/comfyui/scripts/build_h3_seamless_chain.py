#!/usr/bin/env python3
"""Build a ready-to-load H3 Seamless Chain UI workflow from shot prompts.

The builder deliberately mutates only authoring fields in the verified CORE
workflow.  The RTX 4090 / DynamicVRAM model stack is validated before and
after the edit and is never selected or rewritten here.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_NODE_TYPES = {
    "H3StudioControls",
    "UnetLoaderGGUFDynamicVRAM",
    "CLIPLoader",
    "H3LoraStack",
    "VAELoader",
    "H3MultishotSampler",
    "CreateVideo",
    "SaveVideo",
    "SaveAudio",
}

LOCKED_MODEL = "minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf"
LOCKED_CLIP = [
    "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors",
    "minimax",
    "default",
]
LOCKED_VAES = {
    "minimax_h3_video_vae_fp16.safetensors",
    "minimax_h3_audio_vae_fp32.safetensors",
}


class WorkflowError(ValueError):
    pass


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def discover_template() -> Path:
    relative = Path("ComfyUI/custom_nodes/ComfyUI-H3-Multishot/workflows/H3_Seamless_Chain_CORE.json")
    candidates = [Path.cwd() / relative]
    try:
        candidates.append(Path(__file__).resolve().parents[3] / relative)
    except IndexError:
        pass
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise WorkflowError(
        "Verified H3_Seamless_Chain_CORE.json was not found. Pass --template explicitly; "
        "do not substitute another workflow silently."
    )


def aligned_h3_frames(effective_frames: int) -> int:
    if effective_frames <= 5:
        return 5
    return 5 + 17 * ((effective_frames - 5 + 16) // 17)


def load_shots(path: Path) -> list[dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        items: Any = [block.strip() for block in raw.split("\n---\n") if block.strip()]
        durations = frames = None
    else:
        if isinstance(parsed, dict):
            items = parsed.get("shots")
            if items is None:
                items = parsed.get("prompts")
            durations = parsed.get("durations_seconds")
            frames = parsed.get("target_frames")
        else:
            items, durations, frames = parsed, None, None
    if not isinstance(items, list) or not items:
        raise WorkflowError(
            "Input must contain a non-empty shots/prompts list or --- separated text.")

    shots: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        duration = target = None
        if isinstance(item, dict):
            prompt = item.get("prompt", item.get("text", ""))
            duration = item.get("duration_seconds")
            target = item.get("target_frames")
        else:
            prompt = item
        if target is None and isinstance(frames, list) and index < len(frames):
            target = frames[index]
        if duration is None and isinstance(durations, list) and index < len(durations):
            duration = durations[index]
        prompt = str(prompt).strip()
        if not prompt:
            raise WorkflowError(f"Shot {index + 1} has an empty prompt.")
        if len(prompt) > 8000:
            raise WorkflowError(
                f"Shot {index + 1} prompt exceeds 8000 characters; condense it before building.")
        if target is not None and duration is not None:
            from_duration = int(round(float(duration) * 24.0))
            if int(target) != from_duration:
                raise WorkflowError(
                    f"Shot {index + 1} target_frames and duration_seconds disagree.")
        if target is None and duration is not None:
            target = int(round(float(duration) * 24.0))
        shot: dict[str, Any] = {"prompt": prompt}
        if target is not None:
            target = int(target)
            if target <= 0:
                raise WorkflowError(f"Shot {index + 1} duration must be positive.")
            decoded_keep = target + (1 if index > 0 else 0)
            model_frames = aligned_h3_frames(decoded_keep)
            if model_frames > 362:
                raise WorkflowError(
                    f"Shot {index + 1} exceeds the verified H3 362-frame maximum; split it.")
            shot["target_frames"] = target
        shots.append(shot)

    timed = ["target_frames" in shot for shot in shots]
    if any(timed) and not all(timed):
        raise WorkflowError("Declare timing for every shot or for none of them.")
    return shots


def nodes_of_type(workflow: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [node for node in workflow.get("nodes", []) if node.get("type") == node_type]


def one_node(workflow: dict[str, Any], node_type: str) -> dict[str, Any]:
    matches = nodes_of_type(workflow, node_type)
    if len(matches) != 1:
        raise WorkflowError(f"Expected exactly one {node_type} node; found {len(matches)}.")
    return matches[0]


def hardware_fingerprint(workflow: dict[str, Any]) -> dict[str, Any]:
    model = one_node(workflow, "UnetLoaderGGUFDynamicVRAM")
    clip = one_node(workflow, "CLIPLoader")
    vaes = nodes_of_type(workflow, "VAELoader")
    controls = one_node(workflow, "H3StudioControls")
    mux = one_node(workflow, "CreateVideo")
    return {
        "model_loader_type": model.get("type"),
        "model_widgets": copy.deepcopy(model.get("widgets_values")),
        "clip_widgets": copy.deepcopy(clip.get("widgets_values")),
        "vae_widgets": sorted(node.get("widgets_values", [None])[0] for node in vaes),
        "master_controls": copy.deepcopy(controls.get("widgets_values")),
        "mux_widgets": copy.deepcopy(mux.get("widgets_values")),
    }


def validate_core(workflow: dict[str, Any]) -> dict[str, Any]:
    present = {node.get("type") for node in workflow.get("nodes", [])}
    missing = sorted(REQUIRED_NODE_TYPES - present)
    if missing:
        raise WorkflowError(f"CORE workflow is missing required node types: {', '.join(missing)}")

    model = one_node(workflow, "UnetLoaderGGUFDynamicVRAM")
    if model.get("widgets_values") != [LOCKED_MODEL]:
        raise WorkflowError("CORE workflow no longer has the locked RTX 4090 DynamicVRAM Q8 model binding.")

    clip = one_node(workflow, "CLIPLoader")
    if clip.get("widgets_values") != LOCKED_CLIP:
        raise WorkflowError("CORE workflow no longer has the locked text-encoder binding/device policy.")

    vaes = nodes_of_type(workflow, "VAELoader")
    actual_vaes = {node.get("widgets_values", [None])[0] for node in vaes}
    if actual_vaes != LOCKED_VAES:
        raise WorkflowError(f"CORE workflow VAE bindings changed: {sorted(actual_vaes)}")

    controls = one_node(workflow, "H3StudioControls").get("widgets_values", [])
    if len(controls) < 6 or controls[4:6] != ["euler", "beta"]:
        raise WorkflowError("CORE sampler/scheduler controls are not the verified euler/beta pair.")

    mux = one_node(workflow, "CreateVideo").get("widgets_values", [])
    if not mux or float(mux[0]) != 24.0:
        raise WorkflowError("CORE mux must remain at the H3 24 fps timebase.")

    links = workflow.get("links")
    if not isinstance(links, list) or not links:
        raise WorkflowError("CORE workflow has no graph links.")
    node_ids = {node.get("id") for node in workflow.get("nodes", [])}
    for link in links:
        if len(link) < 5 or link[1] not in node_ids or link[3] not in node_ids:
            raise WorkflowError(f"Invalid UI graph link: {link!r}")
    return hardware_fingerprint(workflow)


def set_output_prefix(workflow: dict[str, Any], prefix: str) -> None:
    normalized = prefix.replace("\\", "/").strip("/")
    if not normalized or normalized.startswith(".") or ".." in normalized.split("/"):
        raise WorkflowError("Output prefix must be a safe relative path below ComfyUI/output.")
    one_node(workflow, "SaveVideo")["widgets_values"][0] = f"video/{normalized}"
    one_node(workflow, "SaveAudio")["widgets_values"][0] = f"audio/{normalized}"


def build(template: Path, input_path: Path, output: Path, manifest_path: Path, output_prefix: str | None) -> None:
    if template.resolve() == output.resolve():
        raise WorkflowError("Refusing to overwrite the verified CORE template; choose a new --output path.")

    workflow = json.loads(template.read_text(encoding="utf-8"))
    before = validate_core(workflow)
    shots = load_shots(input_path)
    timed = all("target_frames" in shot for shot in shots)
    script_payload = {"shots": shots} if timed else {
        "prompts": [shot["prompt"] for shot in shots]
    }
    script = json.dumps(script_payload, ensure_ascii=False, separators=(",", ":"))

    sampler = one_node(workflow, "H3MultishotSampler")
    widgets = sampler.setdefault("widgets_values", [])
    if len(widgets) < 2:
        raise WorkflowError("H3MultishotSampler is missing its script/shot_count widgets.")
    widgets[0] = script
    # Zero makes the node count every prompt, including scripts longer than
    # the UI's manual 1..8 forced-count selector.
    widgets[1] = 0

    named = sampler.setdefault("properties", {}).setdefault("h3_widget_values", {})
    named.update(
        {
            "script": script,
            "shot_count": 0,
            "seed_per_shot": True,
            "self_anchor_voice": False,
            "preview_first_shot": True,
            "save_every_shot": True,
            "chain_gain_control": "flatten" if len(shots) > 5 else "off",
        }
    )
    if output_prefix:
        set_output_prefix(workflow, output_prefix)

    after = validate_core(workflow)
    if after != before:
        raise WorkflowError("Protected RTX 4090 model/offload/runtime controls changed during authoring.")

    controls = one_node(workflow, "H3StudioControls")["widgets_values"]
    fps = float(one_node(workflow, "CreateVideo")["widgets_values"][0])
    frames_per_shot = int(controls[2])
    if timed:
        master_frames = sum(int(shot["target_frames"]) for shot in shots)
        model_frames = [
            aligned_h3_frames(int(shot["target_frames"]) + (1 if i else 0))
            for i, shot in enumerate(shots)
        ]
    else:
        master_frames = len(shots) * frames_per_shot - (len(shots) - 1)
        model_frames = [frames_per_shot] * len(shots)

    for note in nodes_of_type(workflow, "Note"):
        if note.get("title") == "CORE - START HERE":
            note["title"] = "READY — CLICK QUEUE PROMPT"
            note["widgets_values"] = [
                "READY-TO-RUN H3 SEAMLESS CHAIN\n\n"
                f"Shots: {len(shots)}\n"
                f"Final duration: {master_frames / fps:.3f}s at 24 fps\n"
                f"Output: ComfyUI/output/video/{output_prefix or 'H3CHAIN/core'}\n\n"
                "Click Queue Prompt once. The sampler renders every shot in "
                "order, relays the last frame into the next shot, joins native "
                "audio, and saves the final master. First-shot preview and "
                "individual recovery shots are enabled.\n\n"
                "RTX 4090 + DynamicVRAM Q8 offload settings are locked."
            ]
            break

    atomic_json_write(output, workflow)
    manifest = {
        "status": "READY_TO_LOAD_AND_QUEUE",
        "workflow": str(output),
        "start_action": "Load the workflow in ComfyUI and click Queue Prompt once.",
        "shot_count": len(shots),
        "timing": {
            "fps": fps,
            "exact": timed,
            "final_frames": master_frames,
            "final_seconds": round(master_frames / fps, 3),
            "model_frames_per_shot": model_frames,
        },
        "recovery": {
            "preview_first_shot": True,
            "save_every_shot": True,
            "chain_gain_control": "flatten" if len(shots) > 5 else "off",
        },
        "hardware": "LOCKED_RTX4090_DYNAMICVRAM_Q8_OFFLOAD",
        "output_prefix": output_prefix or "H3CHAIN/core",
    }
    atomic_json_write(manifest_path, manifest)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "--prompts", dest="input_path", required=True, type=Path,
                        help="Shot JSON or --- separated prompt text")
    parser.add_argument("--output", required=True, type=Path, help="New ComfyUI UI-format workflow JSON")
    parser.add_argument("--manifest", type=Path, help="Build manifest; defaults beside --output")
    parser.add_argument("--template", type=Path, help="Verified H3_Seamless_Chain_CORE.json")
    parser.add_argument("--output-prefix", help="Optional relative prefix below ComfyUI/output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    template = args.template.resolve() if args.template else discover_template()
    manifest = args.manifest or args.output.with_suffix(".manifest.json")
    build(template, args.input_path.resolve(), args.output.resolve(), manifest.resolve(), args.output_prefix)
    print(f"READY_TO_LOAD_AND_QUEUE: {args.output.resolve()}")
    print(f"manifest: {manifest.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
