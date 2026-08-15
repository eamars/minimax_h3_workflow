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

CONTINUITY_LOCK_KEYS = ("style", "identity", "environment", "lighting")
CONTINUITY_FIELDS = (
    "opening_scene",
    "opening_state",
    "opening_camera",
    "opening_audio",
    "opening_hold_seconds",
    "closing_scene",
    "closing_state",
    "closing_camera",
    "closing_audio",
    "closing_hold_seconds",
)
MIN_BOUNDARY_HOLD_SECONDS = 2.0
MIN_ACTION_SECONDS = 2.0
MID_TRANSITION_MIN_RATIO = 0.4
MID_TRANSITION_MAX_RATIO = 0.6
TRANSITION_KINDS = {
    "continuous_camera_move",
    "shot_cut",
    "scene_change",
    "match_cut",
    "dissolve",
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


def _required_text(value: Any, label: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise WorkflowError(f"{label} must be a non-empty string.")
    return text


def _seconds(value: Any, label: str) -> float:
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{label} must be a number of seconds.") from exc
    if seconds < 0:
        raise WorkflowError(f"{label} cannot be negative.")
    return seconds


def _validate_mid_segment_transition(
    shot: dict[str, Any],
    record: dict[str, str],
    duration: float,
    opening_hold: float,
    closing_hold: float,
    index: int,
) -> dict[str, Any] | None:
    """Require visual-context changes to occur near the segment midpoint."""
    label = f"Shot {index + 1}"
    scene_changed = record["opening_scene"] != record["closing_scene"]
    camera_changed = record["opening_camera"] != record["closing_camera"]
    transition = shot.get("transition")
    if not scene_changed and not camera_changed:
        if transition is not None:
            raise WorkflowError(
                f"{label} declares a transition but its opening and closing "
                "scene/camera contexts are identical."
            )
        return None
    if not isinstance(transition, dict):
        changed = "scene and camera" if scene_changed and camera_changed else (
            "scene" if scene_changed else "camera"
        )
        raise WorkflowError(
            f"{label} changes {changed} context and requires a time-coded "
            "mid-segment transition; transitions at generation boundaries are forbidden."
        )
    kind = _required_text(transition.get("kind"), f"{label} transition.kind")
    if kind not in TRANSITION_KINDS:
        raise WorkflowError(
            f"{label} transition.kind must be one of {sorted(TRANSITION_KINDS)}."
        )
    if scene_changed and kind != "scene_change":
        raise WorkflowError(
            f"{label} changes scene and must use transition.kind scene_change."
        )
    if kind == "scene_change" and not scene_changed:
        raise WorkflowError(
            f"{label} declares scene_change but opening_scene equals closing_scene."
        )
    at_seconds = _seconds(transition.get("at_seconds"), f"{label} transition.at_seconds")
    description = _required_text(
        transition.get("description"), f"{label} transition.description"
    )
    earliest = max(opening_hold, duration * MID_TRANSITION_MIN_RATIO)
    latest = min(duration - closing_hold, duration * MID_TRANSITION_MAX_RATIO)
    if earliest > latest or not earliest <= at_seconds <= latest:
        raise WorkflowError(
            f"{label} transition at {at_seconds:.2f}s is not in the protected "
            f"middle window {earliest:.2f}-{latest:.2f}s after the opening "
            "airlock and before the settled landing."
        )
    return {
        "kind": kind,
        "at_seconds": at_seconds,
        "description": description,
        "from_scene": record["opening_scene"],
        "to_scene": record["closing_scene"],
        "from_camera": record["opening_camera"],
        "to_camera": record["closing_camera"],
    }


def _compile_continuity_prompts(
    shots: list[dict[str, Any]], locks_value: Any
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not isinstance(locks_value, dict):
        raise WorkflowError(
            "Multi-shot input requires continuity_locks with style, identity, "
            "environment, and lighting. Phrase-only handoffs are not sufficient."
        )
    locks = {
        key: _required_text(locks_value.get(key), f"continuity_locks.{key}")
        for key in CONTINUITY_LOCK_KEYS
    }
    if locks_value.get("voice") is not None:
        locks["voice"] = _required_text(
            locks_value.get("voice"), "continuity_locks.voice"
        )

    lock_lines = [
        "GLOBAL CONTINUITY LOCK — repeat verbatim in every shot:",
        f"Style: {locks['style']}",
        f"Identity: {locks['identity']}",
        f"Environment: {locks['environment']}",
        f"Lighting: {locks['lighting']}",
    ]
    if "voice" in locks:
        lock_lines.append(f"Voice: {locks['voice']}")
    lock_block = " ".join(lock_lines)

    compiled: list[dict[str, Any]] = []
    boundary_records: list[dict[str, Any]] = []
    previous: dict[str, str] | None = None
    for index, shot in enumerate(shots):
        continuity = shot.get("continuity")
        if not isinstance(continuity, dict):
            raise WorkflowError(
                f"Shot {index + 1} requires a continuity object with explicit "
                "opening/closing state, camera, audio, and hold durations."
            )
        missing = [field for field in CONTINUITY_FIELDS if field not in continuity]
        if missing:
            raise WorkflowError(
                f"Shot {index + 1} continuity is missing: {', '.join(missing)}."
            )

        record = {
            "opening_scene": _required_text(
                continuity["opening_scene"],
                f"Shot {index + 1} continuity.opening_scene",
            ),
            "opening_state": _required_text(
                continuity["opening_state"],
                f"Shot {index + 1} continuity.opening_state",
            ),
            "opening_camera": _required_text(
                continuity["opening_camera"],
                f"Shot {index + 1} continuity.opening_camera",
            ),
            "opening_audio": _required_text(
                continuity["opening_audio"],
                f"Shot {index + 1} continuity.opening_audio",
            ),
            "closing_scene": _required_text(
                continuity["closing_scene"],
                f"Shot {index + 1} continuity.closing_scene",
            ),
            "closing_state": _required_text(
                continuity["closing_state"],
                f"Shot {index + 1} continuity.closing_state",
            ),
            "closing_camera": _required_text(
                continuity["closing_camera"],
                f"Shot {index + 1} continuity.closing_camera",
            ),
            "closing_audio": _required_text(
                continuity["closing_audio"],
                f"Shot {index + 1} continuity.closing_audio",
            ),
        }
        opening_hold = _seconds(
            continuity["opening_hold_seconds"],
            f"Shot {index + 1} continuity.opening_hold_seconds",
        )
        closing_hold = _seconds(
            continuity["closing_hold_seconds"],
            f"Shot {index + 1} continuity.closing_hold_seconds",
        )
        if index > 0 and opening_hold < MIN_BOUNDARY_HOLD_SECONDS:
            raise WorkflowError(
                f"Shot {index + 1} needs at least a {MIN_BOUNDARY_HOLD_SECONDS:.0f}s "
                "opening airlock before any new action or dialogue."
            )
        if closing_hold < MIN_BOUNDARY_HOLD_SECONDS:
            raise WorkflowError(
                f"Shot {index + 1} needs at least a {MIN_BOUNDARY_HOLD_SECONDS:.0f}s "
                "settled landing after its action/dialogue finishes."
            )
        if previous is not None:
            for channel in ("scene", "state", "camera", "audio"):
                opening = record[f"opening_{channel}"]
                closing = previous[f"closing_{channel}"]
                if opening != closing:
                    raise WorkflowError(
                        f"Boundary {index}->{index + 1} {channel} mismatch. The next "
                        f"opening must exactly equal the previous closing; got "
                        f"{opening!r} instead of {closing!r}."
                    )

        if "target_frames" not in shot:
            raise WorkflowError(
                "Every shot in a multi-shot seamless chain requires explicit timing."
            )
        duration = int(shot["target_frames"]) / 24.0
        action_seconds = duration - opening_hold - closing_hold
        if action_seconds < MIN_ACTION_SECONDS:
            raise WorkflowError(
                f"Shot {index + 1} leaves only {action_seconds:.2f}s for its primary "
                f"action after the opening/closing holds; allow at least "
                f"{MIN_ACTION_SECONDS:.0f}s or merge/rewrite the shot."
            )
        transition = _validate_mid_segment_transition(
            shot, record, duration, opening_hold, closing_hold, index
        )

        if index == 0 and opening_hold == 0:
            opening_instruction = (
                f"OPENING STATE: Begin exactly with {record['opening_state']}. "
                f"Opening scene: {record['opening_scene']}. "
                f"Opening camera: {record['opening_camera']}. "
                f"Opening audio: {record['opening_audio']}."
            )
        else:
            opening_instruction = (
                f"OPENING AIRLOCK — first {opening_hold:.1f} seconds: hold exactly "
                f"{record['opening_state']}. Keep the camera exactly "
                f"in scene {record['opening_scene']}. Keep the camera exactly "
                f"{record['opening_camera']}. Continue audio exactly as "
                f"{record['opening_audio']}. Use only natural micro-motion such as "
                "breathing or a tiny weight shift; no new action, dialogue, cut, "
                "reframe, or lens change during the airlock."
            )
        closing_instruction = (
            f"SETTLED LANDING — final {closing_hold:.1f} seconds: finish all action "
            f"and dialogue before this landing, then hold exactly "
            f"{record['closing_state']}. Settle the camera exactly "
            f"{record['closing_camera']}. Settle audio exactly as "
            f"{record['closing_audio']}. Allow only natural micro-motion; begin no "
            "new action, dialogue, cut, reframe, or lens change."
        )
        if transition is None:
            transition_instruction = (
                "NO VISUAL-CONTEXT TRANSITION: remain in the same declared scene "
                "and camera setup for the entire segment."
            )
        else:
            transition_instruction = (
                f"MID-SEGMENT TRANSITION — at {transition['at_seconds']:.1f} "
                f"seconds ({transition['kind']}): preserve the opening scene and "
                f"camera until this time, then {transition['description']} End in "
                f"scene {transition['to_scene']} with camera "
                f"{transition['to_camera']}. Never perform this transition at "
                "frame zero or a generation boundary; keep the new context "
                "established through the settled landing."
            )
        action_prompt = shot["prompt"]
        full_prompt = (
            f"{lock_block} {opening_instruction} PRIMARY ACTION — after the opening "
            f"airlock: {action_prompt} {transition_instruction} {closing_instruction}"
        )
        if len(full_prompt) > 8000:
            raise WorkflowError(
                f"Shot {index + 1} compiled prompt exceeds 8000 characters; "
                "condense its action or continuity fields."
            )
        compiled.append(
            {"prompt": full_prompt, "target_frames": int(shot["target_frames"])}
        )
        boundary_records.append(
            {
                **record,
                "opening_hold_seconds": opening_hold,
                "closing_hold_seconds": closing_hold,
                "action_budget_seconds": round(action_seconds, 3),
                "transition": transition,
            }
        )
        previous = record

    return compiled, {
        "status": "STRICT_BOUNDARY_VALIDATED",
        "mode": "first_frame",
        "scene_transition_policy": "MID_SEGMENT_ONLY",
        "locks": locks,
        "boundaries": boundary_records,
    }


def load_shots(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        items: Any = [block.strip() for block in raw.split("\n---\n") if block.strip()]
        durations = frames = None
        locks = None
    else:
        if isinstance(parsed, dict):
            items = parsed.get("shots")
            if items is None:
                items = parsed.get("prompts")
            durations = parsed.get("durations_seconds")
            frames = parsed.get("target_frames")
            locks = parsed.get("continuity_locks")
        else:
            items, durations, frames, locks = parsed, None, None, None
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
            continuity = item.get("continuity")
            transition = item.get("transition")
        else:
            prompt = item
            continuity = None
            transition = None
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
        shot: dict[str, Any] = {
            "prompt": prompt,
            "continuity": continuity,
            "transition": transition,
        }
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
    if len(shots) > 1:
        if not all(timed):
            raise WorkflowError(
                "Every shot in a multi-shot seamless chain requires explicit timing."
            )
        return _compile_continuity_prompts(shots, locks)
    shots[0].pop("continuity", None)
    return shots, {
        "status": "NOT_APPLICABLE_SINGLE_SHOT",
        "mode": "single_shot",
        "locks": {},
        "boundaries": [],
    }


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
    shots, continuity = load_shots(input_path)
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
                f"Continuity: {continuity['status']}\n"
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
        "continuity": continuity,
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
