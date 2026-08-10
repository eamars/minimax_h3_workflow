"""Validate the v2 cinematic storyboard contract without a JSON Schema dependency.

The v1 storyboard contract remains intentionally permissive for historical plans. A
v2 package must model editorial shots, generated segments, camera setup/motion,
scene geography, continuity state, and generation handoffs as separate objects.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml


SHOT_RE = re.compile(r"^SEQ[0-9]{2,}_SC[0-9]{2,}_SH[0-9]{2,}$")
SEGMENT_RE = re.compile(r"^SEQ[0-9]{2,}_SC[0-9]{2,}_SH[0-9]{2,}_SEG[0-9]{2,}$")
EDITORIAL_MECHANISMS = {"cut", "dissolve", "fade", "end"}
GENERATION_RELATIONSHIPS = {
    "independent",
    "same_shot_continue",
    "endpoint_bridge",
    "reference_reestablish",
    "terminal",
}
ENDPOINT_POLICIES = {
    "none",
    "moving_endpoint",
    "stable_tail",
    "approved_entry_reference",
    "bridge_endpoints",
}
CAMERA_MOTION_TYPES = {
    "static",
    "dolly",
    "track",
    "pan",
    "tilt",
    "crane",
    "arc",
    "handheld",
    "zoom",
    "rack_focus",
    "compound",
}
LIMB_STATES = {"unknown", "free", "occupied", "contact", "transferring"}
LIMB_SIDES = {"left", "right"}
INTERACTION_TARGET_TYPES = {"prop", "body_zone", "landmark", "surface"}
LEGACY_SEGMENT_FIELDS = {
    "primary_performance_arc",
    "dominant_camera_move",
    "transition_to_next",
}


class ContractError(Exception):
    """A deterministic contract failure with a stable code."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise ContractError(code, message)


def load_document(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "STORYBOARD_NOT_OBJECT", f"{path} must contain an object")
    return value


def finite_number(value: object, field: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), "TIME_VALUE_INVALID", f"{field} must be numeric")
    result = float(value)
    require(math.isfinite(result), "TIME_VALUE_INVALID", f"{field} must be finite")
    return result


def validate_range(value: object, field: str, *, positive: bool = False) -> tuple[float, float]:
    require(isinstance(value, dict), "TIME_RANGE_INVALID", f"{field} must be an object")
    start = finite_number(value.get("start_seconds"), f"{field}.start_seconds")
    end = finite_number(value.get("end_seconds"), f"{field}.end_seconds")
    require(start >= 0, "TIME_RANGE_INVALID", f"{field} cannot start before zero")
    require(end >= start, "TIME_RANGE_NONMONOTONIC", f"{field} ends before it starts")
    if positive:
        require(end > start, "TIME_RANGE_NONPOSITIVE", f"{field} must have positive duration")
    return start, end


def require_list(value: object, field: str, minimum: int = 1) -> list:
    require(isinstance(value, list) and len(value) >= minimum, "FIELD_MISSING", f"{field} requires at least {minimum} item(s)")
    return value


def validate_environment_lock(lock: object) -> dict:
    require(isinstance(lock, dict), "ENVIRONMENT_LOCK_MISSING", "director_treatment.environment_lock is required")
    required = {"environment_profile_id", "source_asset_id", "enforcement", "required_landmarks", "allowed_features", "forbidden_inventions", "unknown_regions", "negative_space_rule"}
    require(required <= set(lock), "ENVIRONMENT_LOCK_MISSING", f"environment lock missing {sorted(required - set(lock))}")
    require(lock.get("enforcement") == "hard_reference_no_expansion", "ENVIRONMENT_LOCK_MISSING", "environment lock must use hard_reference_no_expansion")
    for field in ("required_landmarks", "allowed_features", "forbidden_inventions"):
        value = lock.get(field)
        require(isinstance(value, list) and value and all(isinstance(item, str) and item.strip() for item in value), "ENVIRONMENT_LOCK_MISSING", f"environment lock {field} must be non-empty")
    require(isinstance(lock.get("unknown_regions"), list), "ENVIRONMENT_LOCK_MISSING", "environment lock unknown_regions must be a list")
    require(isinstance(lock.get("negative_space_rule"), str) and lock["negative_space_rule"].strip(), "ENVIRONMENT_LOCK_MISSING", "environment lock needs a negative_space_rule")
    positive = {item.strip().lower() for field in ("required_landmarks", "allowed_features") for item in lock[field]}
    forbidden = {item.strip().lower() for item in lock["forbidden_inventions"]}
    require(not positive & forbidden, "ENVIRONMENT_FEATURE_FORBIDDEN", f"environment lock overlaps positive and forbidden features: {sorted(positive & forbidden)}")
    return lock


def _normalise_environment_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(_normalise_environment_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_normalise_environment_text(item) for item in value)
    return str(value).lower().replace("_", " ")


def _forbidden_term_groups(lock: dict) -> list[set[str]]:
    groups: list[set[str]] = []
    for value in lock["forbidden_inventions"]:
        alternatives = str(value).lower().replace("/", " or ").split(" or ")
        for alternative in alternatives:
            tokens = {token for token in re.findall(r"[a-z0-9]+", alternative.replace("_", " ")) if token not in {"or", "and", "the", "a", "an"}}
            if tokens:
                groups.append(tokens)
    return groups


def validate_environment_projection(package: dict, lock: dict) -> None:
    geography = package["scene_geography"]
    texts: list[tuple[str, str]] = []
    for index, landmark in enumerate(geography.get("landmarks", [])):
        if landmark.get("confidence") != "unknown":
            texts.append((f"scene_geography.landmarks[{index}]", _normalise_environment_text({"kind": landmark.get("kind"), "description": landmark.get("description")})))
    for index, zone in enumerate(geography.get("zones", [])):
        texts.append((f"scene_geography.zones[{index}]", _normalise_environment_text({key: zone.get(key) for key in ("zone_id", "kind", "description", "entrances", "exits", "obstacles")})))
    for index, relation in enumerate(geography.get("relations", [])):
        texts.append((f"scene_geography.relations[{index}]", _normalise_environment_text(relation)))
    for shot in package.get("shots", []):
        shot_id = shot.get("shot_id", "unknown-shot")
        staging = shot.get("staging", {})
        texts.append((f"{shot_id}.staging", _normalise_environment_text({key: staging.get(key) for key in ("subject_positions", "action_path", "eyelines", "entry_exit")})))
        camera = shot.get("camera", {}).get("setup", {})
        texts.append((f"{shot_id}.camera", _normalise_environment_text({key: camera.get(key) for key in ("position", "orientation", "composition")})))
    for label, text in texts:
        for tokens in _forbidden_term_groups(lock):
            if all(re.search(rf"\b{re.escape(token)}\b", text) for token in tokens):
                require(False, "ENVIRONMENT_FEATURE_FORBIDDEN", f"{label} describes forbidden environment feature: {' '.join(sorted(tokens))}")
    views = geography.get("reference_views", [])
    require(any(isinstance(view, dict) and view.get("asset_id") == lock["source_asset_id"] for view in views), "ENVIRONMENT_LOCK_MISSING", "scene geography must retain the environment profile source view")


def validate_v1(package: dict) -> None:
    required = {"artifact", "director_treatment", "shots", "generation_segments", "handoffs", "creative_acceptance_tests"}
    require(required <= set(package), "V1_FIELD_MISSING", f"missing {sorted(required - set(package))}")
    segments = require_list(package["generation_segments"], "generation_segments")
    for index, segment in enumerate(segments):
        require(isinstance(segment, dict), "V1_SEGMENT_INVALID", f"segment {index} is not an object")
        duration = finite_number(segment.get("duration_seconds"), f"generation_segments[{index}].duration_seconds")
        require(0 < duration <= 10, "SEGMENT_DURATION_INVALID", f"segment {index} duration must be >0 and <=10")
        timeline = require_list(segment.get("four_track_timeline"), f"segment {index}.four_track_timeline")
        previous = -1.0
        for row_index, row in enumerate(timeline):
            start = finite_number(row.get("start_seconds"), f"segment {index}.timeline[{row_index}].start_seconds")
            end = finite_number(row.get("end_seconds"), f"segment {index}.timeline[{row_index}].end_seconds")
            require(start >= previous and end >= start, "TIMELINE_NONMONOTONIC", f"segment {index} timeline is not monotonic")
            previous = end
    print("PASS: v1 storyboard package is historically valid")


def validate_state(state: object, field: str) -> None:
    require(isinstance(state, dict), "CONTINUITY_STATE_INVALID", f"{field} must be an object")
    required = {"snapshot_id", "character_states", "environment_state", "prop_states", "limb_states", "sound_state", "invariants", "expected_deltas", "forbidden_deltas"}
    require(required <= set(state), "CONTINUITY_STATE_INCOMPLETE", f"{field} missing {sorted(required - set(state))}")
    require(isinstance(state["snapshot_id"], str) and state["snapshot_id"], "CONTINUITY_STATE_INVALID", f"{field}.snapshot_id is required")
    require(isinstance(state["character_states"], list), "CONTINUITY_STATE_INVALID", f"{field}.character_states must be a list")
    for index, character in enumerate(state["character_states"]):
        require(isinstance(character, dict), "CONTINUITY_STATE_INVALID", f"{field}.character_states[{index}] must be an object")
        for key in ("canon_id", "visibility", "pose", "gaze", "wardrobe_state"):
            require(character.get(key), "CONTINUITY_STATE_INVALID", f"{field}.character_states[{index}].{key} is required")
    require(isinstance(state["environment_state"], dict), "CONTINUITY_STATE_INVALID", f"{field}.environment_state must be an object")
    require(isinstance(state["prop_states"], list), "CONTINUITY_STATE_INVALID", f"{field}.prop_states must be a list")
    limbs = state["limb_states"]
    require(isinstance(limbs, list) and len(limbs) >= 2, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states must contain both sides")
    limb_ids: set[str] = set()
    sides: set[str] = set()
    for index, limb in enumerate(limbs):
        require(isinstance(limb, dict), "LIMB_CONTINUITY_MISSING", f"{field}.limb_states[{index}] must be an object")
        for key in ("limb_id", "side", "state", "holding_prop_id", "contact_target"):
            require(key in limb, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states[{index}].{key} is required")
        require(isinstance(limb["limb_id"], str) and limb["limb_id"] and limb["limb_id"] not in limb_ids, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states has a missing or duplicate limb_id")
        require(limb["side"] in LIMB_SIDES, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states[{index}].side is invalid")
        require(limb["state"] in LIMB_STATES, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states[{index}].state is invalid")
        limb_ids.add(limb["limb_id"])
        sides.add(limb["side"])
    require(sides == LIMB_SIDES, "LIMB_CONTINUITY_MISSING", f"{field}.limb_states must cover left and right")
    require(isinstance(state["sound_state"], dict), "CONTINUITY_STATE_INVALID", f"{field}.sound_state must be an object")
    require_list(state["invariants"], f"{field}.invariants", minimum=1)
    require(isinstance(state["expected_deltas"], list), "CONTINUITY_STATE_INVALID", f"{field}.expected_deltas must be a list")
    require(isinstance(state["forbidden_deltas"], list), "CONTINUITY_STATE_INVALID", f"{field}.forbidden_deltas must be a list")


def validate_limb_interactions(package: dict, registry: list[dict], external_targets: list[dict] | None = None) -> None:
    """Validate semantic hand/target ownership, not only field presence.

    A bilateral limb snapshot is executable continuity data.  A target may not
    be invented at prompt time: props are declared by the snapshot prop
    ledger, while body zones/landmarks/surfaces must be declared in the
    package-level interaction target registry.
    """
    prop_ids = {
        prop.get("prop_id")
        for state in registry
        for prop in state.get("prop_states", [])
        if isinstance(prop, dict) and isinstance(prop.get("prop_id"), str) and prop.get("prop_id")
    }
    references = {
        reference
        for state in registry
        for limb in state.get("limb_states", [])
        for reference in (limb.get("holding_prop_id"), limb.get("contact_target"))
        if reference
    }
    target_rows = package.get("interaction_targets") or external_targets
    if references:
        require(isinstance(target_rows, list) and target_rows, "INTERACTION_TARGET_REGISTRY_MISSING", "interactive limb references require interaction_targets")
    target_by_id: dict[str, dict] = {}
    for index, target in enumerate(target_rows or []):
        require(isinstance(target, dict), "INTERACTION_TARGET_REGISTRY_INVALID", f"interaction_targets[{index}] must be an object")
        target_id = target.get("target_id")
        require(isinstance(target_id, str) and target_id and target_id not in target_by_id, "INTERACTION_TARGET_REGISTRY_INVALID", f"interaction_targets[{index}] has a missing or duplicate target_id")
        require(target.get("target_type") in INTERACTION_TARGET_TYPES, "INTERACTION_TARGET_REGISTRY_INVALID", f"{target_id} has an invalid target_type")
        require(isinstance(target.get("description"), str) and target["description"].strip(), "INTERACTION_TARGET_REGISTRY_INVALID", f"{target_id} needs a description")
        if target["target_type"] == "body_zone":
            require(isinstance(target.get("subject_id"), str) and target["subject_id"], "INTERACTION_TARGET_REGISTRY_INVALID", f"{target_id} body_zone needs subject_id")
        target_by_id[target_id] = target

    for reference in references:
        require(reference in target_by_id, "INTERACTION_TARGET_UNDECLARED", f"limb reference {reference} is not declared in interaction_targets")
    for target_id, target in target_by_id.items():
        if target["target_type"] == "prop":
            require(target_id in prop_ids, "INTERACTION_TARGET_PROP_UNKNOWN", f"interaction target {target_id} is not present in any prop ledger")

    snapshot_character_ids = {
        character.get("canon_id")
        for state in registry
        for character in state.get("character_states", [])
        if isinstance(character, dict) and character.get("canon_id")
    }
    for target_id, target in target_by_id.items():
        if target["target_type"] == "body_zone":
            require(target["subject_id"] in snapshot_character_ids, "INTERACTION_TARGET_SUBJECT_UNKNOWN", f"{target_id} references an unknown subject")

    for state in registry:
        state_id = state["snapshot_id"]
        snapshot_props = {
            prop.get("prop_id")
            for prop in state.get("prop_states", [])
            if isinstance(prop, dict) and prop.get("prop_id")
        }
        held_props: dict[str, str] = {}
        for limb in state["limb_states"]:
            limb_id = limb["limb_id"]
            limb_state = limb["state"]
            holding = limb.get("holding_prop_id")
            contact = limb.get("contact_target")
            if limb_state in {"free", "unknown"}:
                require(holding is None and contact is None, "LIMB_STATE_SEMANTICS_INVALID", f"{state_id}.{limb_id} {limb_state} cannot hold or contact a target")
            elif limb_state == "contact":
                require(holding is None and contact is not None, "LIMB_STATE_SEMANTICS_INVALID", f"{state_id}.{limb_id} contact requires only contact_target")
            elif limb_state == "occupied":
                require(holding is not None and contact is None, "LIMB_STATE_SEMANTICS_INVALID", f"{state_id}.{limb_id} occupied requires only holding_prop_id")
            elif limb_state == "transferring":
                require(holding is not None and contact is not None, "LIMB_STATE_SEMANTICS_INVALID", f"{state_id}.{limb_id} transferring requires holding_prop_id and contact_target")
            if holding is not None:
                require(target_by_id[holding]["target_type"] == "prop", "LIMB_HOLD_TARGET_INVALID", f"{state_id}.{limb_id} cannot hold non-prop target {holding}")
                require(holding in snapshot_props, "LIMB_HOLD_PROP_MISSING", f"{state_id}.{limb_id} holds {holding}, absent from the snapshot prop ledger")
                require(holding not in held_props, "LIMB_PROP_DOUBLE_HELD", f"{state_id} assigns {holding} to both {held_props.get(holding)} and {limb_id}")
                held_props[holding] = limb_id
            if contact is not None and target_by_id[contact]["target_type"] == "prop":
                require(contact in snapshot_props, "LIMB_CONTACT_PROP_MISSING", f"{state_id}.{limb_id} contacts {contact}, absent from the snapshot prop ledger")

    # A prop cannot jump directly between two hands while remaining occupied;
    # the intermediate transfer/free snapshot must be represented explicitly.
    for previous, current in zip(registry, registry[1:]):
        previous_by_id = {limb["limb_id"]: limb for limb in previous["limb_states"]}
        current_by_id = {limb["limb_id"]: limb for limb in current["limb_states"]}
        for limb_id in set(previous_by_id) & set(current_by_id):
            old = previous_by_id[limb_id]
            new = current_by_id[limb_id]
            if old.get("holding_prop_id") and new.get("holding_prop_id") and old["holding_prop_id"] != new["holding_prop_id"]:
                require(new["state"] == "transferring" or old["state"] == "transferring", "LIMB_PROP_HANDOFF_UNEXPLAINED", f"{previous['snapshot_id']} -> {current['snapshot_id']} changes {limb_id} from {old['holding_prop_id']} to {new['holding_prop_id']} without a transfer state")


def validate_geography(geography: object) -> dict:
    require(isinstance(geography, dict), "SCENE_GEOGRAPHY_MISSING", "scene_geography is required")
    for field in ("geography_id", "coordinate_system"):
        require(geography.get(field), "SCENE_GEOGRAPHY_MISSING", f"scene geography needs {field}")
    landmarks = geography.get("landmarks")
    require(isinstance(landmarks, list), "GEOGRAPHY_LANDMARKS_INVALID", "scene geography landmarks must be a list")
    landmark_ids: set[str] = set()
    for index, landmark in enumerate(landmarks):
        require(isinstance(landmark, dict), "GEOGRAPHY_LANDMARK_INVALID", f"landmark {index} must be an object")
        landmark_id = landmark.get("landmark_id")
        require(isinstance(landmark_id, str) and landmark_id and landmark_id not in landmark_ids, "GEOGRAPHY_LANDMARK_INVALID", f"landmark {index} id is missing or duplicated")
        landmark_ids.add(landmark_id)
        for field in ("kind", "description", "confidence"):
            require(landmark.get(field), "GEOGRAPHY_LANDMARK_INVALID", f"{landmark_id} needs {field}")
    axes = geography.get("axes")
    require(isinstance(axes, list), "GEOGRAPHY_AXES_INVALID", "scene geography axes must be a list")
    axis_ids: set[str] = set()
    for index, axis in enumerate(axes):
        require(isinstance(axis, dict), "GEOGRAPHY_AXIS_INVALID", f"axis {index} must be an object")
        axis_id = axis.get("axis_id")
        require(isinstance(axis_id, str) and axis_id and axis_id not in axis_ids, "GEOGRAPHY_AXIS_INVALID", f"axis {index} id is missing or duplicated")
        axis_ids.add(axis_id)
        require_list(axis.get("subject_ids"), f"{axis_id}.subject_ids", minimum=2)
        require(axis.get("description"), "GEOGRAPHY_AXIS_INVALID", f"{axis_id} needs a description")
    zones = geography.get("zones")
    require(isinstance(zones, list) and zones, "GEOGRAPHY_ZONES_INVALID", "scene geography needs typed camera zones")
    zone_ids: set[str] = set()
    for index, zone in enumerate(zones):
        require(isinstance(zone, dict), "GEOGRAPHY_ZONE_INVALID", f"zone {index} must be an object")
        zone_id = zone.get("zone_id")
        require(isinstance(zone_id, str) and zone_id and zone_id not in zone_ids, "GEOGRAPHY_ZONE_INVALID", f"zone {index} id is missing or duplicated")
        zone_ids.add(zone_id)
        for field in ("kind", "description", "visibility"):
            require(zone.get(field), "GEOGRAPHY_ZONE_INVALID", f"{zone_id} needs {field}")
        require(isinstance(zone.get("adjacent_zone_ids"), list), "GEOGRAPHY_ZONE_INVALID", f"{zone_id}.adjacent_zone_ids must be a list")
        require(set(zone["adjacent_zone_ids"]) <= zone_ids | {item.get("zone_id") for item in zones if isinstance(item, dict)}, "GEOGRAPHY_ZONE_UNKNOWN", f"{zone_id} references an unknown adjacent zone")
    allowed = geography.get("allowed_camera_zones")
    require(isinstance(allowed, list) and allowed, "GEOGRAPHY_ZONES_INVALID", "allowed_camera_zones must be a non-empty list")
    require(set(allowed) <= zone_ids, "GEOGRAPHY_ZONE_UNKNOWN", "allowed_camera_zones contains an undeclared zone")
    relations = geography.get("relations")
    require(isinstance(relations, list), "GEOGRAPHY_RELATIONS_INVALID", "scene geography relations must be a list")
    relation_ids: set[str] = set()
    for index, relation in enumerate(relations):
        require(isinstance(relation, dict), "GEOGRAPHY_RELATION_INVALID", f"relation {index} must be an object")
        relation_id = relation.get("relation_id")
        require(isinstance(relation_id, str) and relation_id and relation_id not in relation_ids, "GEOGRAPHY_RELATION_INVALID", f"relation {index} id is missing or duplicated")
        relation_ids.add(relation_id)
        require(relation.get("type"), "GEOGRAPHY_RELATION_INVALID", f"{relation_id} needs a type")
        require(relation.get("from_id") and relation.get("to_id"), "GEOGRAPHY_RELATION_INVALID", f"{relation_id} needs from_id and to_id")
    reference_views = geography.get("reference_views")
    require(isinstance(reference_views, list), "GEOGRAPHY_REFERENCE_VIEWS_INVALID", "reference_views must be a list")
    for index, view in enumerate(reference_views):
        require(isinstance(view, dict), "GEOGRAPHY_REFERENCE_VIEW_INVALID", f"reference view {index} must be an object")
        for field in ("view_id", "asset_id", "purpose"):
            require(view.get(field), "GEOGRAPHY_REFERENCE_VIEW_INVALID", f"reference view {index} needs {field}")
    require(isinstance(geography.get("unknown_regions"), list), "GEOGRAPHY_UNKNOWN_REGIONS_INVALID", "unknown_regions must be a list")
    return {
        "geography_id": geography["geography_id"],
        "landmark_ids": landmark_ids,
        "axis_ids": axis_ids,
        "zone_ids": zone_ids,
    }


def validate_staging(staging: object, shot_id: str, geography: dict) -> None:
    require(isinstance(staging, dict), "STAGING_MISSING", f"{shot_id} staging is required")
    for field in ("geography_id", "action_path", "entry_exit"):
        require(staging.get(field), "STAGING_INCOMPLETE", f"{shot_id}.staging.{field} is required")
    require(staging["geography_id"] == geography["geography_id"], "STAGING_GEOGRAPHY_MISMATCH", f"{shot_id} staging uses a different geography")
    positions = staging.get("subject_positions")
    require(isinstance(positions, list) and positions, "STAGING_INCOMPLETE", f"{shot_id}.staging.subject_positions must be non-empty")
    for index, position in enumerate(positions):
        require(isinstance(position, dict), "STAGING_INCOMPLETE", f"{shot_id}.staging.subject_positions[{index}] must be an object")
        require(position.get("subject_id") and position.get("zone") in geography["zone_ids"], "STAGING_GEOGRAPHY_UNKNOWN", f"{shot_id} staging position {index} uses an unknown subject or zone")
        require(isinstance(position.get("relation_to_landmarks"), list) and position["relation_to_landmarks"], "STAGING_INCOMPLETE", f"{shot_id} staging position {index} needs landmark relations")
        for relation in position["relation_to_landmarks"]:
            base_id = str(relation).split("-", 1)[0]
            require(base_id in geography["landmark_ids"], "STAGING_LANDMARK_UNKNOWN", f"{shot_id} references unknown landmark {relation}")
    entry_exit = staging["entry_exit"]
    require(isinstance(entry_exit, dict) and entry_exit.get("entry") and entry_exit.get("exit"), "STAGING_INCOMPLETE", f"{shot_id}.staging.entry_exit is incomplete")


def validate_reference_bindings(bindings: object, shot_id: str) -> None:
    if bindings is None:
        return
    require(isinstance(bindings, list) and bindings, "REFERENCE_BINDINGS_INVALID", f"{shot_id} reference_bindings must be a non-empty list")
    seen: set[str] = set()
    for index, binding in enumerate(bindings):
        require(isinstance(binding, dict), "REFERENCE_BINDINGS_INVALID", f"{shot_id}.reference_bindings[{index}] must be an object")
        binding_id = binding.get("binding_id")
        require(isinstance(binding_id, str) and binding_id and binding_id not in seen, "REFERENCE_BINDINGS_INVALID", f"{shot_id} binding {index} id is missing or duplicated")
        seen.add(binding_id)
        require(binding.get("asset_id"), "REFERENCE_BINDINGS_INVALID", f"{shot_id}.{binding_id} needs asset_id")
        require(isinstance(binding.get("property_scope"), list) and binding["property_scope"], "REFERENCE_BINDINGS_INVALID", f"{shot_id}.{binding_id} needs property_scope")
        require(binding.get("timeline_scope"), "REFERENCE_BINDINGS_INVALID", f"{shot_id}.{binding_id} needs timeline_scope")
        require(binding.get("strength") in {"canonical", "strong", "soft", "informational"}, "REFERENCE_BINDINGS_INVALID", f"{shot_id}.{binding_id} has invalid strength")


def validate_camera(camera: object, shot_id: str, geography: dict | None = None) -> None:
    require(isinstance(camera, dict), "CAMERA_MODEL_OPAQUE", f"{shot_id} camera must be structured")
    required = {"setup", "in_shot_motion", "setup_change_from_previous"}
    require(required <= set(camera), "CAMERA_FIELDS_MISSING", f"{shot_id} camera missing {sorted(required - set(camera))}")
    setup = camera["setup"]
    require(isinstance(setup, dict), "CAMERA_SETUP_INVALID", f"{shot_id} setup must be an object")
    require(setup.get("setup_id"), "CAMERA_SETUP_INVALID", f"{shot_id} setup_id is required")
    for field in ("position", "orientation", "optics", "composition", "axis"):
        require(isinstance(setup.get(field), dict), "CAMERA_SETUP_INVALID", f"{shot_id} setup.{field} must be an object")
    position = setup["position"]
    for field in ("reference_frame", "zone", "height", "depth", "lateral", "relation_to_subject"):
        require(position.get(field), "CAMERA_POSITION_MISSING", f"{shot_id} setup.position.{field} is required")
    if geography is not None:
        require(position["zone"] in geography["zone_ids"], "CAMERA_GEOGRAPHY_UNKNOWN", f"{shot_id} camera uses unknown zone {position['zone']}")
    orientation = setup["orientation"]
    for field in ("viewpoint", "aim", "horizon"):
        require(orientation.get(field), "CAMERA_ORIENTATION_MISSING", f"{shot_id} setup.orientation.{field} is required")
    optics = setup["optics"]
    for field in ("lens_appearance", "focus_behavior", "depth_of_field"):
        require(optics.get(field), "CAMERA_OPTICS_MISSING", f"{shot_id} setup.optics.{field} is required")
    composition = setup["composition"]
    for field in ("shot_size", "subject_priority", "screen_direction", "headroom", "eyeline"):
        require(composition.get(field) not in (None, "", []), "CAMERA_COMPOSITION_MISSING", f"{shot_id} setup.composition.{field} is required")
    axis = setup["axis"]
    require(axis.get("status") in {"held", "crossed_with_reset", "not_applicable", "unknown"}, "AXIS_STATUS_INVALID", f"{shot_id} axis status is invalid")
    look_at = setup.get("look_at")
    require(isinstance(look_at, dict) and look_at.get("target") and look_at.get("mode"), "CAMERA_LOOK_AT_MISSING", f"{shot_id} camera needs a structured look_at")
    keyframes = camera.get("keyframes")
    require(isinstance(keyframes, list) and keyframes, "CAMERA_KEYFRAMES_MISSING", f"{shot_id} camera needs planned keyframes")
    previous_keyframe_time = -1.0
    for index, keyframe in enumerate(keyframes):
        require(isinstance(keyframe, dict), "CAMERA_KEYFRAMES_INVALID", f"{shot_id} keyframe {index} must be an object")
        keyframe_time = finite_number(keyframe.get("time_seconds"), f"{shot_id}.keyframes[{index}].time_seconds")
        require(keyframe_time >= previous_keyframe_time and keyframe.get("position") and keyframe.get("viewpoint"), "CAMERA_KEYFRAMES_INVALID", f"{shot_id} keyframes must be ordered and fully specified")
        previous_keyframe_time = keyframe_time
    change = camera["setup_change_from_previous"]
    require(isinstance(change, dict), "CAMERA_SETUP_CHANGE_INVALID", f"{shot_id} setup change must be an object")
    require(isinstance(change.get("position_changed"), bool), "CAMERA_SETUP_CHANGE_INVALID", f"{shot_id} position_changed must be boolean")
    require(change.get("reason"), "CAMERA_SETUP_CHANGE_UNMOTIVATED", f"{shot_id} camera setup change needs a reason")
    require_list(change.get("continuity_strategy"), f"{shot_id}.camera.continuity_strategy")
    require(isinstance(camera.get("risk_controls"), list) and camera["risk_controls"], "CAMERA_RISK_CONTROLS_MISSING", f"{shot_id} camera needs risk controls")
    motion = camera["in_shot_motion"]
    require(isinstance(motion, dict), "CAMERA_MOTION_INVALID", f"{shot_id} in_shot_motion must be an object")
    require(motion.get("type") in CAMERA_MOTION_TYPES, "CAMERA_MOTION_INVALID", f"{shot_id} motion type is invalid")
    for field in ("motivation", "speed_profile", "movement_character"):
        require(motion.get(field), "CAMERA_MOTION_UNMOTIVATED", f"{shot_id} motion.{field} is required")
    if motion.get("type") != "static":
        require(motion.get("path"), "CAMERA_MOTION_PATH_MISSING", f"{shot_id} non-static motion needs a path")


def validate_shots(package: dict, geography: dict) -> tuple[dict[str, dict], list[dict]]:
    shots = require_list(package.get("shots"), "shots")
    by_id: dict[str, dict] = {}
    indexes: list[int] = []
    for index, shot in enumerate(shots):
        require(isinstance(shot, dict), "SHOT_INVALID", f"shots[{index}] is not an object")
        shot_id = shot.get("shot_id")
        require(isinstance(shot_id, str) and SHOT_RE.fullmatch(shot_id), "SHOT_ID_INVALID", f"shots[{index}] has invalid shot_id")
        require(shot_id not in by_id, "SHOT_ID_DUPLICATE", f"duplicate {shot_id}")
        by_id[shot_id] = shot
        shot_index = shot.get("shot_index")
        require(isinstance(shot_index, int) and shot_index >= 1, "SHOT_INDEX_INVALID", f"{shot_id} shot_index is invalid")
        indexes.append(shot_index)
        for field in ("editorial_role", "purpose", "coverage_function"):
            require(shot.get(field), "SHOT_INTENT_MISSING", f"{shot_id} missing {field}")
        require_list(shot.get("plot_beat_ids"), f"{shot_id}.plot_beat_ids")
        require_list(shot.get("performance_beat_ids"), f"{shot_id}.performance_beat_ids")
        validate_range(shot.get("scene_time"), f"{shot_id}.scene_time", positive=True)
        validate_staging(shot.get("staging"), shot_id, geography)
        validate_camera(shot.get("camera"), shot_id, geography)
        validate_state(shot.get("continuity_in"), f"{shot_id}.continuity_in")
        validate_state(shot.get("continuity_out"), f"{shot_id}.continuity_out")
        validate_reference_bindings(shot.get("reference_bindings"), shot_id)
    require(indexes == sorted(indexes) and indexes == list(range(1, len(indexes) + 1)), "SHOT_ORDER_INVALID", "shot_index must be contiguous and ordered")
    roles = {shot["editorial_role"] for shot in shots}
    policy = package.get("director_treatment", {}).get("coverage_policy", {})
    required_roles = policy.get("required_roles", []) if isinstance(policy, dict) else []
    for role in required_roles:
        require(role in roles, "COVERAGE_ROLE_MISSING", f"coverage policy requires a {role} shot")
    if isinstance(policy, dict) and not policy.get("allow_sparse_coverage", True):
        require(roles & {"establishing", "master"}, "COVERAGE_ESTABLISHING_MISSING", "declared feature coverage needs an establishing or master shot")
        require(roles & {"coverage", "insert", "reaction", "subjective"}, "COVERAGE_VARIETY_MISSING", "declared feature coverage needs coverage beyond a single master")
    allow_same_phase_overlap = bool(package.get("director_treatment", {}).get("allow_same_phase_overlap", False))
    for left_index, left in enumerate(shots):
        left_start, left_end = validate_range(left["scene_time"], f"{left['shot_id']}.scene_time", positive=True)
        for right in shots[left_index + 1:]:
            right_start, right_end = validate_range(right["scene_time"], f"{right['shot_id']}.scene_time", positive=True)
            if left.get("coverage_phase") and left.get("coverage_phase") == right.get("coverage_phase") and max(left_start, right_start) < min(left_end, right_end):
                require(allow_same_phase_overlap, "SCENE_COVERAGE_OVERLAP_UNDECLARED", f"{left['shot_id']} and {right['shot_id']} overlap the same declared coverage phase")
    return by_id, shots


def validate_boundaries(package: dict, shots_by_id: dict[str, dict], shots: list[dict]) -> dict[str, dict]:
    boundaries = require_list(package.get("editorial_boundaries"), "editorial_boundaries")
    require(len(boundaries) == len(shots), "EDITORIAL_BOUNDARY_TOPOLOGY_INVALID", "there must be one boundary for every shot, including the end")
    by_id: dict[str, dict] = {}
    previous_record_end = -1.0
    for index, boundary in enumerate(boundaries):
        require(isinstance(boundary, dict), "EDITORIAL_BOUNDARY_INVALID", f"boundary {index} is not an object")
        boundary_id = boundary.get("boundary_id")
        require(isinstance(boundary_id, str) and boundary_id not in by_id, "EDITORIAL_BOUNDARY_ID_INVALID", f"boundary {index} id is missing or duplicated")
        by_id[boundary_id] = boundary
        from_id = boundary.get("from_shot_id")
        to_id = boundary.get("to_shot_id")
        require(from_id in shots_by_id, "EDITORIAL_BOUNDARY_SOURCE_UNKNOWN", f"{boundary_id} references unknown source shot")
        if boundary.get("mechanism") == "end":
            require(to_id is None, "EDITORIAL_END_TARGET_INVALID", f"{boundary_id} end boundary must have no target")
        else:
            require(boundary.get("mechanism") in EDITORIAL_MECHANISMS - {"end"}, "EDITORIAL_MECHANISM_INVALID", f"{boundary_id} mechanism is invalid")
            require(to_id in shots_by_id, "EDITORIAL_BOUNDARY_TARGET_UNKNOWN", f"{boundary_id} references unknown target shot")
        require_list(boundary.get("motivations"), f"{boundary_id}.motivations")
        require(boundary.get("audio_behavior"), "EDITORIAL_AUDIO_BEHAVIOR_MISSING", f"{boundary_id} needs an audio behavior")
        start, end = validate_range(boundary.get("record_time"), f"{boundary_id}.record_time")
        require(start >= previous_record_end, "EDITORIAL_RECORD_TIME_NONMONOTONIC", f"{boundary_id} record time moves backwards")
        previous_record_end = max(previous_record_end, end)
        picture_edit = boundary.get("picture_edit")
        audio_edit = boundary.get("audio_edit")
        require(isinstance(picture_edit, dict) and picture_edit.get("type") in {"cut", "dissolve", "fade", "end"}, "EDITORIAL_PICTURE_EDIT_INVALID", f"{boundary_id} needs a structured picture edit")
        require(isinstance(audio_edit, dict) and audio_edit.get("type") in {"independent", "j_cut", "l_cut", "hard_sync"}, "EDITORIAL_AUDIO_EDIT_INVALID", f"{boundary_id} needs a structured audio edit")
        if audio_edit.get("type") in {"j_cut", "l_cut"}:
            overlap_frames = audio_edit.get("overlap_frames")
            require(isinstance(overlap_frames, int) and overlap_frames > 0, "EDITORIAL_AUDIO_EDIT_INVALID", f"{boundary_id} J/L edit needs positive overlap_frames")
            require(audio_edit.get("room_tone_policy"), "EDITORIAL_AUDIO_EDIT_INVALID", f"{boundary_id} J/L edit needs room_tone_policy")
    for index, shot in enumerate(shots):
        incoming = shot.get("incoming_boundary_id")
        outgoing = shot.get("outgoing_boundary_id")
        expected_incoming = None if index == 0 else boundaries[index - 1]["boundary_id"]
        expected_outgoing = boundaries[index]["boundary_id"]
        require(incoming == expected_incoming, "EDITORIAL_BOUNDARY_BILATERAL_MISMATCH", f"{shot['shot_id']} incoming boundary is not bilateral with the ordered record")
        require(outgoing == expected_outgoing, "EDITORIAL_BOUNDARY_BILATERAL_MISMATCH", f"{shot['shot_id']} outgoing boundary is not bilateral with the ordered record")
        if incoming is not None:
            require(incoming in by_id and by_id[incoming]["to_shot_id"] == shot["shot_id"], "EDITORIAL_BOUNDARY_BILATERAL_MISMATCH", f"{incoming} does not point into {shot['shot_id']}")
        require(outgoing in by_id and by_id[outgoing]["from_shot_id"] == shot["shot_id"], "EDITORIAL_BOUNDARY_BILATERAL_MISMATCH", f"{outgoing} does not leave {shot['shot_id']}")
        if index < len(shots) - 1:
            require(boundaries[index]["to_shot_id"] == shots[index + 1]["shot_id"], "EDITORIAL_BOUNDARY_ORDER_INVALID", f"{boundaries[index]['boundary_id']} does not lead to the next editorial shot")
        else:
            require(boundaries[index]["mechanism"] == "end" and boundaries[index]["to_shot_id"] is None, "EDITORIAL_END_INVALID", "the last shot must terminate with an end boundary")
    require(sum(1 for item in boundaries if item.get("mechanism") == "end") == 1, "EDITORIAL_END_INVALID", "exactly one end boundary is required")
    require(boundaries[-1].get("mechanism") == "end", "EDITORIAL_END_INVALID", "end boundary must be last")
    return by_id


def validate_handoffs(package: dict, shots_by_id: dict[str, dict], segments: list[dict]) -> dict[str, dict]:
    handoffs = package.get("generation_handoffs")
    require(isinstance(handoffs, list), "GENERATION_HANDOFFS_MISSING", "generation_handoffs must be a list separate from editorial boundaries")
    by_id: dict[str, dict] = {}
    segment_ids = {segment["segment_id"] for segment in segments}
    for index, handoff in enumerate(handoffs):
        require(isinstance(handoff, dict), "GENERATION_HANDOFF_INVALID", f"handoff {index} is not an object")
        handoff_id = handoff.get("handoff_id")
        require(isinstance(handoff_id, str) and handoff_id not in by_id, "GENERATION_HANDOFF_ID_INVALID", f"handoff {index} id is missing or duplicated")
        by_id[handoff_id] = handoff
        require(handoff.get("from_segment_id") in segment_ids, "GENERATION_HANDOFF_SOURCE_UNKNOWN", f"{handoff_id} source segment is unknown")
        target = handoff.get("to_segment_id")
        if handoff.get("relationship") == "terminal":
            require(target is None, "GENERATION_HANDOFF_TARGET_INVALID", f"{handoff_id} terminal handoff has a target")
        else:
            require(target in segment_ids, "GENERATION_HANDOFF_TARGET_UNKNOWN", f"{handoff_id} target segment is unknown")
        require(handoff.get("relationship") in GENERATION_RELATIONSHIPS, "GENERATION_RELATIONSHIP_INVALID", f"{handoff_id} relationship is invalid")
        require(handoff.get("endpoint_policy") in ENDPOINT_POLICIES, "GENERATION_ENDPOINT_POLICY_INVALID", f"{handoff_id} endpoint policy is invalid")
        require_list(handoff.get("acceptance_conditions"), f"{handoff_id}.acceptance_conditions")
        require("mechanism" not in handoff, "EDITORIAL_GENERATION_BOUNDARY_CONFLATED", f"{handoff_id} cannot carry an editorial mechanism")
        relationship = handoff.get("relationship")
        if relationship == "same_shot_continue" and target is not None:
            source_shot = next(item["shot_id"] for item in segments if item["segment_id"] == handoff["from_segment_id"])
            target_shot = next(item["shot_id"] for item in segments if item["segment_id"] == target)
            require(source_shot == target_shot, "GENERATION_RELATIONSHIP_INVALID", f"{handoff_id} same_shot_continue crosses editorial shots")
        if handoff.get("endpoint_policy") == "moving_endpoint":
            evidence = handoff.get("motion_endpoint_evidence")
            require(isinstance(evidence, dict), "MOVING_ENDPOINT_EVIDENCE_MISSING", f"{handoff_id} moving endpoint needs evidence")
            for field in ("source_tail", "successor_entry", "comparison_fields"):
                require(evidence.get(field), "MOVING_ENDPOINT_EVIDENCE_MISSING", f"{handoff_id} moving endpoint evidence needs {field}")
        boundary_id = handoff.get("editorial_boundary_id")
        if boundary_id is not None:
            boundaries = {item.get("boundary_id"): item for item in package.get("editorial_boundaries", [])}
            require(boundary_id in boundaries, "GENERATION_EDITORIAL_LINK_INVALID", f"{handoff_id} references an undeclared editorial boundary")
            boundary = boundaries[boundary_id]
            source_shot = next(item["shot_id"] for item in segments if item["segment_id"] == handoff["from_segment_id"])
            require(boundary["from_shot_id"] == source_shot, "GENERATION_EDITORIAL_LINK_INVALID", f"{handoff_id} boundary source does not match segment source")
            if target is None:
                require(boundary["to_shot_id"] is None, "GENERATION_EDITORIAL_LINK_INVALID", f"{handoff_id} terminal boundary must have no target")
            else:
                target_shot = next(item["shot_id"] for item in segments if item["segment_id"] == target)
                require(boundary["to_shot_id"] == target_shot, "GENERATION_EDITORIAL_LINK_INVALID", f"{handoff_id} boundary target does not match segment target")
        elif relationship == "independent":
            require(False, "GENERATION_EDITORIAL_LINK_INVALID", f"{handoff_id} independent handoff must be tied to an editorial boundary")
    return by_id


def validate_segments(package: dict, shots_by_id: dict[str, dict], handoffs: dict[str, dict]) -> list[dict]:
    segments = require_list(package.get("generation_segments"), "generation_segments")
    seen: set[str] = set()
    grouped: defaultdict[str, list[dict]] = defaultdict(list)
    by_id: dict[str, dict] = {}
    for index, segment in enumerate(segments):
        require(isinstance(segment, dict), "SEGMENT_INVALID", f"segments[{index}] is not an object")
        segment_id = segment.get("segment_id")
        shot_id = segment.get("shot_id")
        require(isinstance(segment_id, str) and SEGMENT_RE.fullmatch(segment_id), "SEGMENT_ID_INVALID", f"segments[{index}] has invalid segment_id")
        require(segment_id not in seen, "SEGMENT_ID_DUPLICATE", f"duplicate {segment_id}")
        seen.add(segment_id)
        by_id[segment_id] = segment
        require(shot_id in shots_by_id, "SEGMENT_SHOT_UNKNOWN", f"{segment_id} references unknown shot")
        require(not (LEGACY_SEGMENT_FIELDS & set(segment)), "V2_LEGACY_FIELDS_PRESENT", f"{segment_id} mixes v1 segment fields with v2")
        duration = finite_number(segment.get("duration_seconds"), f"{segment_id}.duration_seconds")
        require(0 < duration <= 10, "SEGMENT_DURATION_INVALID", f"{segment_id} duration must be >0 and <=10")
        shot_scene_start, shot_scene_end = validate_range(shots_by_id[shot_id]["scene_time"], f"{shot_id}.scene_time", positive=True)
        segment_scene_start, segment_scene_end = validate_range(segment.get("scene_time"), f"{segment_id}.scene_time", positive=True)
        require(shot_scene_start <= segment_scene_start <= segment_scene_end <= shot_scene_end, "SEGMENT_SCENE_TIME_OUT_OF_SHOT", f"{segment_id} scene time is outside its editorial shot")
        for domain in ("source_time", "record_time"):
            start, end = validate_range(segment.get(domain), f"{segment_id}.{domain}", positive=True)
            if domain == "source_time":
                require(abs((end - start) - duration) <= 0.02, "SOURCE_TIME_DURATION_MISMATCH", f"{segment_id} source time must match duration")
        validate_state(segment.get("entry_state"), f"{segment_id}.entry_state")
        validate_state(segment.get("exit_state"), f"{segment_id}.exit_state")
        contract = segment.get("continuity_contract")
        require(isinstance(contract, dict), "CONTINUITY_CONTRACT_MISSING", f"{segment_id} continuity contract is required")
        for field in ("invariants", "expected_deltas", "forbidden_deltas"):
            require(isinstance(contract.get(field), list), "CONTINUITY_CONTRACT_INVALID", f"{segment_id}.{field} must be a list")
        require(segment.get("performance_arc_id"), "PERFORMANCE_ARC_MISSING", f"{segment_id} performance arc is required")
        intervals = require_list(segment.get("camera_interval_map"), f"{segment_id}.camera_interval_map")
        previous = 0.0
        shot_setup_id = shots_by_id[shot_id]["camera"]["setup"]["setup_id"]
        for interval_index, interval in enumerate(intervals):
            start = finite_number(interval.get("start_seconds"), f"{segment_id}.camera_interval.start_seconds")
            end = finite_number(interval.get("end_seconds"), f"{segment_id}.camera_interval.end_seconds")
            require(start == previous and end > start, "CAMERA_INTERVAL_NONMONOTONIC", f"{segment_id} camera intervals must be contiguous and positive")
            require(end <= duration + 0.02, "CAMERA_INTERVAL_OUT_OF_RANGE", f"{segment_id} camera interval exceeds segment duration")
            require(interval.get("camera_setup_id") == shot_setup_id, "CAMERA_INTERVAL_SETUP_UNKNOWN", f"{segment_id} interval {interval_index} does not bind to the shot camera setup")
            validate_camera({"setup": {"setup_id": shot_setup_id, "position": {"reference_frame": "interval", "zone": shots_by_id[shot_id]["camera"]["setup"]["position"]["zone"], "height": "interval", "depth": "interval", "lateral": "interval", "relation_to_subject": "interval"}, "orientation": {"viewpoint": "interval", "aim": "interval", "horizon": "interval"}, "optics": {"lens_appearance": "interval", "focus_behavior": "interval", "depth_of_field": "interval"}, "composition": {"shot_size": "interval", "subject_priority": ["interval"], "screen_direction": "interval", "headroom": "interval", "eyeline": "interval"}, "axis": {"axis_id": None, "side": None, "status": "not_applicable"}, "look_at": {"target": "interval", "mode": "interval"}}, "in_shot_motion": interval.get("motion"), "setup_change_from_previous": {"position_changed": False, "reason": "interval map", "continuity_strategy": ["coverage"]}, "keyframes": [{"time_seconds": 0, "position": "interval", "viewpoint": "interval"}], "risk_controls": ["interval"]}, f"{segment_id}.camera_interval")
            previous = end
        require(abs(previous - duration) <= 0.02, "CAMERA_INTERVAL_COVERAGE_GAP", f"{segment_id} camera intervals do not cover the full segment")
        timeline = require_list(segment.get("four_track_timeline"), f"{segment_id}.four_track_timeline")
        previous = 0.0
        for row in timeline:
            start = finite_number(row.get("start_seconds"), f"{segment_id}.timeline.start_seconds")
            end = finite_number(row.get("end_seconds"), f"{segment_id}.timeline.end_seconds")
            require(start >= previous and end > start, "TIMELINE_NONMONOTONIC", f"{segment_id} timeline is not monotonic")
            require(end <= duration + 0.02, "TIMELINE_OUT_OF_RANGE", f"{segment_id} timeline exceeds duration")
            previous = end
        grouped[shot_id].append(segment)
    for shot_id, shot_segments in grouped.items():
        shot_segments.sort(key=lambda item: item["shot_segment_index"])
        indices = [item.get("shot_segment_index") for item in shot_segments]
        require(indices == list(range(1, len(indices) + 1)), "SHOT_SEGMENT_INDEX_INVALID", f"{shot_id} segment indices must be contiguous")
        shot_start, shot_end = validate_range(shots_by_id[shot_id]["scene_time"], f"{shot_id}.scene_time", positive=True)
        require(abs(float(shot_segments[0]["scene_time"]["start_seconds"]) - shot_start) <= 0.02, "SHOT_SEGMENT_SCENE_GAP", f"{shot_id} segment scene time does not start with the shot")
        require(abs(float(shot_segments[-1]["scene_time"]["end_seconds"]) - shot_end) <= 0.02, "SHOT_SEGMENT_SCENE_GAP", f"{shot_id} segment scene time does not end with the shot")
        for left_scene, right_scene in zip(shot_segments, shot_segments[1:]):
            require(abs(float(left_scene["scene_time"]["end_seconds"]) - float(right_scene["scene_time"]["start_seconds"])) <= 0.02, "SHOT_SEGMENT_SCENE_GAP", f"{shot_id} segment scene times are not contiguous")
        for left, right in zip(shot_segments, shot_segments[1:]):
            handoff = left.get("generation_handoff_to_next")
            require(isinstance(handoff, dict), "GENERATION_HANDOFF_LINK_MISSING", f"{left['segment_id']} needs a typed handoff to {right['segment_id']}")
            require(handoff.get("to_segment_id") == right["segment_id"], "GENERATION_HANDOFF_LINK_INVALID", f"{left['segment_id']} handoff does not target the next segment")
            require(handoff.get("relationship") in {"same_shot_continue", "endpoint_bridge", "reference_reestablish"}, "SHOT_SPLIT_RELATIONSHIP_INVALID", f"{shot_id} split is not represented as a generation relationship")
            require(handoff.get("handoff_id") in handoffs, "GENERATION_HANDOFF_LINK_INVALID", f"{left['segment_id']} references an undeclared handoff")
            require(handoffs[handoff["handoff_id"]] == handoff, "GENERATION_HANDOFF_LINK_INVALID", f"{left['segment_id']} handoff differs from top-level declaration")
            require(handoff.get("endpoint_policy") in {"moving_endpoint", "stable_tail", "bridge_endpoints", "approved_entry_reference"}, "MOVING_HANDOFF_POLICY_MISSING", f"{left['segment_id']} split needs a handoff policy")
        terminal = shot_segments[-1].get("generation_handoff_to_next")
        require(isinstance(terminal, dict), "GENERATION_HANDOFF_LINK_MISSING", f"{shot_segments[-1]['segment_id']} needs an explicit outgoing generation handoff")
        require(terminal.get("handoff_id") in handoffs and handoffs[terminal["handoff_id"]] == terminal, "GENERATION_HANDOFF_LINK_INVALID", f"{shot_segments[-1]['segment_id']} terminal handoff is not declared")
    ordered_segments = sorted(segments, key=lambda item: (float(item["record_time"]["start_seconds"]), float(item["record_time"]["end_seconds"])))
    require(ordered_segments == segments, "RECORD_ASSEMBLY_ORDER_INVALID", "generation segments must be listed in record order")
    previous_end = 0.0
    for segment in ordered_segments:
        start = float(segment["record_time"]["start_seconds"])
        end = float(segment["record_time"]["end_seconds"])
        require(abs(start - previous_end) <= 0.02, "RECORD_ASSEMBLY_GAP", f"{segment['segment_id']} leaves a record-time gap or overlap")
        previous_end = end
    require(ordered_segments and abs(previous_end - float(package["editorial_boundaries"][-1]["record_time"]["start_seconds"])) <= 0.02, "RECORD_ASSEMBLY_END_MISMATCH", "record assembly does not end at the editorial end boundary")
    return segments


def state_map(state: dict) -> dict[str, dict]:
    return {item["canon_id"]: item for item in state.get("character_states", []) if isinstance(item, dict) and item.get("canon_id")}


def delta_allows(state: dict, field: str) -> bool:
    terms = " ".join(str(item).lower() for item in state.get("expected_deltas", []))
    return field in terms or (field == "wetness_state" and "wet" in terms)


def compare_states(previous: dict, current: dict, label: str) -> None:
    previous_chars = state_map(previous)
    current_chars = state_map(current)
    require(set(previous_chars) <= set(current_chars), "CONTINUITY_CHARACTER_MISSING", f"{label} drops a canonical character")
    for canon_id, old in previous_chars.items():
        new = current_chars[canon_id]
        for field in ("wardrobe_state", "wetness_state"):
            if old.get(field) != new.get(field):
                require(delta_allows(previous, field) or delta_allows(current, field), "CONTINUITY_STATE_CONTRADICTION", f"{label} changes {canon_id}.{field} without an expected delta")
    for field in ("room", "location", "time_of_day"):
        if previous.get("environment_state", {}).get(field) != current.get("environment_state", {}).get(field):
            require(delta_allows(previous, field) or delta_allows(current, field), "CONTINUITY_ENVIRONMENT_CONTRADICTION", f"{label} changes environment.{field} without an expected delta")


def validate_continuity(package: dict, shots: list[dict], segments: list[dict], external_targets: list[dict] | None = None) -> None:
    registry = package.get("continuity_registry")
    require(isinstance(registry, list), "CONTINUITY_REGISTRY_MISSING", "continuity_registry is required")
    registry_by_id: dict[str, dict] = {}
    for index, state in enumerate(registry):
        validate_state(state, f"continuity_registry[{index}]")
        require(state["snapshot_id"] not in registry_by_id, "CONTINUITY_REGISTRY_INVALID", f"duplicate snapshot {state['snapshot_id']}")
        registry_by_id[state["snapshot_id"]] = state
    validate_limb_interactions(package, registry, external_targets)
    embedded: list[tuple[str, dict]] = []
    for shot in shots:
        embedded.extend([(f"{shot['shot_id']}.continuity_in", shot["continuity_in"]), (f"{shot['shot_id']}.continuity_out", shot["continuity_out"])])
    for segment in segments:
        embedded.extend([(f"{segment['segment_id']}.entry_state", segment["entry_state"]), (f"{segment['segment_id']}.exit_state", segment["exit_state"])])
    for label, state in embedded:
        require(state["snapshot_id"] in registry_by_id, "CONTINUITY_REGISTRY_REFERENCE_MISSING", f"{label} references an unregistered snapshot")
        canonical = registry_by_id[state["snapshot_id"]]
        for field in ("prop_states", "limb_states"):
            require(state.get(field) == canonical.get(field), "CONTINUITY_SNAPSHOT_PAYLOAD_MISMATCH", f"{label}.{field} differs from authoritative snapshot {state['snapshot_id']}")
        if "environment_profile_id" in state.get("environment_state", {}) or "environment_profile_id" in canonical.get("environment_state", {}):
            require(state.get("environment_state", {}).get("environment_profile_id") == canonical.get("environment_state", {}).get("environment_profile_id"), "CONTINUITY_SNAPSHOT_PAYLOAD_MISMATCH", f"{label}.environment_state differs from authoritative snapshot {state['snapshot_id']}")
    ordered_segments = sorted(segments, key=lambda item: float(item["record_time"]["start_seconds"]))
    for previous, current in zip(ordered_segments, ordered_segments[1:]):
        require(previous["exit_state"]["snapshot_id"] == current["entry_state"]["snapshot_id"], "CONTINUITY_SNAPSHOT_LINK_INVALID", f"{previous['segment_id']} does not hand its exit snapshot to {current['segment_id']}")
        compare_states(previous["exit_state"], current["entry_state"], f"{previous['segment_id']} -> {current['segment_id']}")
    for shot in shots:
        shot_segments = sorted([item for item in segments if item["shot_id"] == shot["shot_id"]], key=lambda item: item["shot_segment_index"])
        require(shot_segments, "SHOT_SEGMENTS_MISSING", f"{shot['shot_id']} has no generation segment")
        require(shot["continuity_in"]["snapshot_id"] == shot_segments[0]["entry_state"]["snapshot_id"], "CONTINUITY_SNAPSHOT_LINK_INVALID", f"{shot['shot_id']} continuity_in does not match its first segment")
        require(shot["continuity_out"]["snapshot_id"] == shot_segments[-1]["exit_state"]["snapshot_id"], "CONTINUITY_SNAPSHOT_LINK_INVALID", f"{shot['shot_id']} continuity_out does not match its last segment")
    for previous, current in zip(shots, shots[1:]):
        compare_states(previous["continuity_out"], current["continuity_in"], f"{previous['shot_id']} -> {current['shot_id']}")
def validate_v2(package: dict, external_targets: list[dict] | None = None) -> None:
    require(package.get("planning_model_version") == 2, "V2_VERSION_REQUIRED", "planning_model_version must be 2")
    require("handoffs" not in package, "V2_LEGACY_FIELDS_PRESENT", "use editorial_boundaries and generation_handoffs, not handoffs")
    treatment = package.get("director_treatment")
    require(isinstance(treatment, dict), "DIRECTOR_TREATMENT_MISSING", "director_treatment is required")
    require(treatment.get("camera_position_policy") == "allowed_to_change_between_shots", "CAMERA_POSITION_POLICY_INVALID", "camera position changes must be explicitly allowed by treatment")
    validate_environment_lock(treatment.get("environment_lock"))
    migration = package.get("migration")
    if isinstance(migration, dict):
        require(migration.get("status") == "complete", "MIGRATION_REVIEW_REQUIRED", "migrated v2 packages remain blocked until creative fields are reviewed")
    geography = validate_geography(package.get("scene_geography"))
    validate_environment_projection(package, treatment["environment_lock"])
    shots_by_id, shots = validate_shots(package, geography)
    validate_boundaries(package, shots_by_id, shots)
    segments = require_list(package.get("generation_segments"), "generation_segments")
    handoffs = validate_handoffs(package, shots_by_id, segments)
    validate_segments(package, shots_by_id, handoffs)
    validate_continuity(package, shots, segments, external_targets)
    require(isinstance(package.get("animatic_intent"), dict), "ANIMATIC_INTENT_MISSING", "animatic_intent is required")
    require_list(package.get("creative_acceptance_tests"), "creative_acceptance_tests")
    print("PASS: v2 real-cinematic storyboard package is valid")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storyboard", type=Path, required=True)
    parser.add_argument("--schema-version", choices=("auto", "1", "2"), default="auto")
    parser.add_argument("--interaction-target-registry", type=Path)
    args = parser.parse_args()
    try:
        package = load_document(args.storyboard)
        version = args.schema_version
        if version == "auto":
            version = "2" if package.get("planning_model_version") == 2 else "1"
        if version == "2":
            external_targets = None
            if args.interaction_target_registry:
                target_document = load_document(args.interaction_target_registry)
                external_targets = target_document.get("interaction_targets")
                require(isinstance(external_targets, list), "INTERACTION_TARGET_REGISTRY_INVALID", "interaction target registry must contain interaction_targets list")
            validate_v2(package, external_targets)
        else:
            validate_v1(package)
        return 0
    except (ContractError, OSError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
