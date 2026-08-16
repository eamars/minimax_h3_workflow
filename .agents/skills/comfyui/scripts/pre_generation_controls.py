"""Deterministic semantic controls that must pass before an H3 graph is queued."""

from __future__ import annotations

from typing import Any


IDENTITY_MODES = {"persistent_reference", "endpoint_image", "not_applicable"}
VISIBILITY_MODES = {"on_screen", "off_screen", "j_cut", "l_cut"}
MOTION_MODES = {"none", "static", "path"}
VISUAL_RESET_MODES = {
    "no_reset",
    "endpoint_bridge",
    "reference_reestablish",
    "editorial_cut",
}


class PreGenerationControlError(ValueError):
    """Raised when semantic risk is not bounded before generation."""


def _required_text(value: Any, label: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise PreGenerationControlError(f"{label} must be a non-empty string.")
    return text


def _seconds(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PreGenerationControlError(f"{label} must be a number of seconds.") from exc
    if result < 0:
        raise PreGenerationControlError(f"{label} cannot be negative.")
    return result


def _required_text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise PreGenerationControlError(f"{label} must be a non-empty list.")
    return [_required_text(item, f"{label}[{index}]") for index, item in enumerate(value)]


def validate_identity_control(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PreGenerationControlError(
            f"PREGEN_IDENTITY_CONTROL_MISSING: {context} requires identity control."
        )
    mode = _required_text(value.get("mode"), f"{context}.identity.mode")
    if mode not in IDENTITY_MODES:
        raise PreGenerationControlError(
            f"{context}.identity.mode must be one of {sorted(IDENTITY_MODES)}."
        )
    normalized: dict[str, Any] = {"mode": mode}
    if mode == "not_applicable":
        normalized["reason"] = _required_text(
            value.get("reason"), f"{context}.identity.reason"
        )
        return normalized

    normalized["subject_id"] = _required_text(
        value.get("subject_id"), f"{context}.identity.subject_id"
    )
    if mode == "persistent_reference":
        tokens = _required_text_list(
            value.get("prompt_tokens"), f"{context}.identity.prompt_tokens"
        )
        if "<Picture 1>" not in tokens:
            raise PreGenerationControlError(
                f"CANON_IDENTITY_BINDING_MISSING: {context} persistent identity "
                "must bind <Picture 1>."
            )
        asset_ids = value.get("reference_asset_ids")
        source_path = str(value.get("source_path") or "").strip()
        if not source_path and not (isinstance(asset_ids, list) and asset_ids):
            raise PreGenerationControlError(
                f"CANON_IDENTITY_BINDING_MISSING: {context} needs source_path or "
                "reference_asset_ids."
            )
        normalized["prompt_tokens"] = tokens
        if source_path:
            normalized["source_path"] = source_path
        if isinstance(asset_ids, list) and asset_ids:
            normalized["reference_asset_ids"] = [
                _required_text(item, f"{context}.identity.reference_asset_ids[{index}]")
                for index, item in enumerate(asset_ids)
            ]
        if value.get("input_name") is not None:
            normalized["input_name"] = _required_text(
                value.get("input_name"), f"{context}.identity.input_name"
            )
        normalized["use_as_start_image"] = bool(value.get("use_as_start_image", False))
    else:
        normalized["endpoint_asset_id"] = _required_text(
            value.get("endpoint_asset_id"), f"{context}.identity.endpoint_asset_id"
        )
    return normalized


def validate_pre_generation_controls(
    controls: Any,
    *,
    duration: float,
    prompt: str,
    opening_hold: float = 0.0,
    closing_hold: float = 0.0,
    scene_changed: bool = False,
    context: str = "segment",
) -> dict[str, Any]:
    """Validate identity, multiplicity, dialogue, motion, and reset controls."""
    if not isinstance(controls, dict):
        raise PreGenerationControlError(
            f"PREGEN_CONTROLS_MISSING: {context} requires pre_generation_controls."
        )
    identity = validate_identity_control(controls.get("identity"), context)

    subject_instances = controls.get("subject_instances")
    if not isinstance(subject_instances, list):
        raise PreGenerationControlError(
            f"SUBJECT_MULTIPLICITY_UNBOUNDED: {context}.subject_instances must be a list."
        )
    normalized_subjects: list[dict[str, Any]] = []
    seen_subjects: set[str] = set()
    for index, item in enumerate(subject_instances):
        if not isinstance(item, dict):
            raise PreGenerationControlError(
                f"{context}.subject_instances[{index}] must be an object."
            )
        subject_id = _required_text(
            item.get("subject_id"), f"{context}.subject_instances[{index}].subject_id"
        )
        if subject_id in seen_subjects:
            raise PreGenerationControlError(
                f"SUBJECT_MULTIPLICITY_UNBOUNDED: duplicate subject rule {subject_id}."
            )
        try:
            maximum = int(item.get("max_visible_instances"))
        except (TypeError, ValueError) as exc:
            raise PreGenerationControlError(
                f"{context}.subject_instances[{index}].max_visible_instances must be an integer."
            ) from exc
        if maximum < 1:
            raise PreGenerationControlError(
                f"{context}.subject_instances[{index}].max_visible_instances must be positive."
            )
        seen_subjects.add(subject_id)
        normalized_subjects.append(
            {"subject_id": subject_id, "max_visible_instances": maximum}
        )

    dialogue_cues = controls.get("dialogue_cues")
    if not isinstance(dialogue_cues, list):
        raise PreGenerationControlError(
            f"DIALOGUE_WINDOW_MISSING: {context}.dialogue_cues must be a list."
        )
    normalized_cues: list[dict[str, Any]] = []
    for index, cue in enumerate(dialogue_cues):
        if not isinstance(cue, dict):
            raise PreGenerationControlError(f"{context}.dialogue_cues[{index}] must be an object.")
        start = _seconds(cue.get("start_seconds"), f"{context}.dialogue_cues[{index}].start_seconds")
        end = _seconds(cue.get("end_seconds"), f"{context}.dialogue_cues[{index}].end_seconds")
        if start < opening_hold or end <= start or end > duration - closing_hold:
            raise PreGenerationControlError(
                f"DIALOGUE_TIMING_MISMATCH: {context} cue {index + 1} must stay "
                "after the opening hold and before the settled landing."
            )
        visibility = _required_text(
            cue.get("visibility"), f"{context}.dialogue_cues[{index}].visibility"
        )
        if visibility not in VISIBILITY_MODES:
            raise PreGenerationControlError(
                f"{context}.dialogue_cues[{index}].visibility must be one of "
                f"{sorted(VISIBILITY_MODES)}."
            )
        normalized_cue = {
            "speaker_id": _required_text(
                cue.get("speaker_id"), f"{context}.dialogue_cues[{index}].speaker_id"
            ),
            "start_seconds": start,
            "end_seconds": end,
            "visibility": visibility,
        }
        if visibility == "on_screen":
            visible_from = _seconds(
                cue.get("visible_from_seconds"),
                f"{context}.dialogue_cues[{index}].visible_from_seconds",
            )
            if visible_from > start:
                raise PreGenerationControlError(
                    f"SPEAKER_VISIBILITY_UNBOUND: {context} cue {index + 1} starts "
                    "before its on-screen speaker is visible."
                )
            normalized_cue["visible_from_seconds"] = visible_from
        normalized_cues.append(normalized_cue)
    has_dialogue_tag = "<d>" in prompt and "</d>" in prompt
    if has_dialogue_tag and not normalized_cues:
        raise PreGenerationControlError(
            f"DIALOGUE_WINDOW_MISSING: {context} contains <d> dialogue without a timed cue."
        )
    if normalized_cues and not has_dialogue_tag:
        raise PreGenerationControlError(
            f"DIALOGUE_TAG_MISSING: {context} has timed dialogue cues but no <d>...</d> prompt tag."
        )

    motion = controls.get("motion")
    if not isinstance(motion, dict):
        raise PreGenerationControlError(
            f"ACTOR_PATH_UNSIGNED: {context}.motion must be an object."
        )
    motion_mode = _required_text(motion.get("mode"), f"{context}.motion.mode")
    if motion_mode not in MOTION_MODES:
        raise PreGenerationControlError(
            f"{context}.motion.mode must be one of {sorted(MOTION_MODES)}."
        )
    normalized_motion: dict[str, Any] = {"mode": motion_mode}
    if motion_mode == "none":
        normalized_motion["reason"] = _required_text(
            motion.get("reason"), f"{context}.motion.reason"
        )
    elif motion_mode == "static":
        normalized_motion.update(
            subject_id=_required_text(
                motion.get("subject_id"), f"{context}.motion.subject_id"
            ),
            zone=_required_text(motion.get("zone"), f"{context}.motion.zone"),
        )
    else:
        normalized_motion.update(
            subject_id=_required_text(
                motion.get("subject_id"), f"{context}.motion.subject_id"
            ),
            from_zone=_required_text(motion.get("from_zone"), f"{context}.motion.from_zone"),
            to_zone=_required_text(motion.get("to_zone"), f"{context}.motion.to_zone"),
            direction=_required_text(motion.get("direction"), f"{context}.motion.direction"),
            forbidden_directions=_required_text_list(
                motion.get("forbidden_directions"),
                f"{context}.motion.forbidden_directions",
            ),
            endpoint_state=_required_text(
                motion.get("endpoint_state"), f"{context}.motion.endpoint_state"
            ),
        )
        if normalized_motion["from_zone"] == normalized_motion["to_zone"]:
            raise PreGenerationControlError(
                f"ACTOR_PATH_UNSIGNED: {context} path start and destination cannot match."
            )

    visual_reset = controls.get("visual_reset")
    if not isinstance(visual_reset, dict):
        raise PreGenerationControlError(
            f"TEXT_ONLY_VISUAL_RESET_UNSAFE: {context}.visual_reset must be an object."
        )
    reset_mode = _required_text(visual_reset.get("mode"), f"{context}.visual_reset.mode")
    if reset_mode not in VISUAL_RESET_MODES:
        raise PreGenerationControlError(
            f"TEXT_ONLY_VISUAL_RESET_UNSAFE: {context}.visual_reset.mode must be one of "
            f"{sorted(VISUAL_RESET_MODES)}."
        )
    normalized_reset: dict[str, Any] = {"mode": reset_mode}
    if reset_mode in {"endpoint_bridge", "reference_reestablish"}:
        normalized_reset["anchor_asset_id"] = _required_text(
            visual_reset.get("anchor_asset_id"),
            f"{context}.visual_reset.anchor_asset_id",
        )
    if scene_changed and reset_mode == "no_reset":
        raise PreGenerationControlError(
            f"TEXT_ONLY_VISUAL_RESET_UNSAFE: {context} changes scene without an "
            "endpoint bridge, reference re-establish, or editorial cut."
        )
    if not scene_changed and reset_mode != "no_reset":
        raise PreGenerationControlError(
            f"TEXT_ONLY_VISUAL_RESET_UNSAFE: {context} declares {reset_mode} but "
            "its scene does not change."
        )

    return {
        "status": "PRE_GENERATION_VALIDATED",
        "identity": identity,
        "subject_instances": normalized_subjects,
        "dialogue_cues": normalized_cues,
        "motion": normalized_motion,
        "visual_reset": normalized_reset,
    }


def build_prompt_guard(controls: dict[str, Any]) -> str:
    """Compile validated controls into concise Simplified-Chinese H3 direction."""
    parts: list[str] = []
    identity = controls["identity"]
    if identity["mode"] == "persistent_reference":
        parts.append(
            f"身份参考绑定：<Picture 1>只用于锁定{identity['subject_id']}的身份，"
            "每个镜头都保持同一面部、发型、身体比例与服装身份特征。"
        )
    for item in controls["subject_instances"]:
        subject_id = item["subject_id"]
        maximum = item["max_visible_instances"]
        if maximum == 1:
            parts.append(
                f"主体数量锁：任一画面中{subject_id}最多出现1个实例；"
                "禁止重复人物、分身、回声人物、反射副本或背景替身。"
            )
        else:
            parts.append(
                f"主体数量锁：任一画面中{subject_id}最多出现{maximum}个实例，"
                "不得超过上游明确声明的数量。"
            )
    cues = controls["dialogue_cues"]
    if not cues:
        parts.append("对白门控：本段全程无对白、无类似人声的临时发言，也不承接未声明台词。")
    else:
        for cue in cues:
            parts.append(
                f"对白时间窗：{cue['speaker_id']}只在{cue['start_seconds']:.2f}-"
                f"{cue['end_seconds']:.2f}秒发声，画面关系为{cue['visibility']}。"
            )
    motion = controls["motion"]
    if motion["mode"] == "static":
        parts.append(
            f"位置锁：{motion['subject_id']}保持在{motion['zone']}，不得迁移到其他区域。"
        )
    elif motion["mode"] == "path":
        forbidden = "、".join(motion["forbidden_directions"])
        parts.append(
            f"有向动作路径：{motion['subject_id']}只从{motion['from_zone']}沿"
            f"{motion['direction']}移动到{motion['to_zone']}；禁止{forbidden}；"
            f"最终状态为{motion['endpoint_state']}。"
        )
    parts.append("视觉上下文锁：禁止未声明的场景重置或模型自行生成的转场。")
    return " ".join(parts)
