"""Migrate a v1 storyboard into a schema-shaped, completion-blocked v2 revision.

The migration carries stable IDs and measurable timing forward, but every camera,
geography, continuity, and editorial decision that v1 did not contain is marked
for editorial completion. The output is structurally valid v2, receives a new
revision, and is intentionally rejected by the cinematic admission validator
until a later planning pass changes the migration status to ``complete``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import yaml


SHOT_RE = __import__("re").compile(r"^SEQ[0-9]{2,}_SC[0-9]{2,}_SH[0-9]{2,}$")


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def state(snapshot_id: str, pose: str = "MIGRATION_REVIEW_REQUIRED") -> dict:
    return {
        "snapshot_id": snapshot_id,
        "character_states": [{
            "canon_id": "MIGRATED_CHARACTER_REQUIRES_REVIEW",
            "visibility": "MIGRATION_REVIEW_REQUIRED",
            "pose": pose,
            "gaze": "MIGRATION_REVIEW_REQUIRED",
            "wardrobe_state": "MIGRATION_REVIEW_REQUIRED",
            "wetness_state": "MIGRATION_REVIEW_REQUIRED",
        }],
        "environment_state": {"location": "MIGRATION_REVIEW_REQUIRED"},
        "prop_states": [],
        "limb_states": [
            {"limb_id": "HAND_L", "side": "left", "state": "unknown", "holding_prop_id": None, "contact_target": None},
            {"limb_id": "HAND_R", "side": "right", "state": "unknown", "holding_prop_id": None, "contact_target": None},
        ],
        "sound_state": {"ambience": "MIGRATION_REVIEW_REQUIRED"},
        "invariants": [{"invariant_id": "MIGRATION_INVARIANT", "owner": "migration", "value": "creative review required"}],
        "expected_deltas": ["MIGRATION_REVIEW_REQUIRED"],
        "forbidden_deltas": ["unreviewed continuity change"],
    }


def camera(setup_id: str, previous_shot_id: str | None) -> dict:
    return {
        "setup": {
            "setup_id": setup_id,
            "position": {
                "reference_frame": "MIGRATION_REVIEW_REQUIRED",
                "zone": "unknown_zone",
                "height": "MIGRATION_REVIEW_REQUIRED",
                "depth": "MIGRATION_REVIEW_REQUIRED",
                "lateral": "MIGRATION_REVIEW_REQUIRED",
                "relation_to_subject": "MIGRATION_REVIEW_REQUIRED",
            },
            "orientation": {"viewpoint": "MIGRATION_REVIEW_REQUIRED", "aim": "MIGRATION_REVIEW_REQUIRED", "horizon": "MIGRATION_REVIEW_REQUIRED", "roll": "MIGRATION_REVIEW_REQUIRED"},
            "optics": {"lens_appearance": "MIGRATION_REVIEW_REQUIRED", "focus_behavior": "MIGRATION_REVIEW_REQUIRED", "depth_of_field": "MIGRATION_REVIEW_REQUIRED"},
            "composition": {"shot_size": "MIGRATION_REVIEW_REQUIRED", "subject_priority": ["MIGRATION_REVIEW_REQUIRED"], "screen_direction": "MIGRATION_REVIEW_REQUIRED", "headroom": "MIGRATION_REVIEW_REQUIRED", "eyeline": "MIGRATION_REVIEW_REQUIRED"},
            "axis": {"axis_id": None, "side": None, "status": "unknown", "crossing_justification": "MIGRATION_REVIEW_REQUIRED"},
            "look_at": {"target": "MIGRATION_REVIEW_REQUIRED", "mode": "MIGRATION_REVIEW_REQUIRED"},
        },
        "in_shot_motion": {"type": "static", "motivation": "MIGRATION_REVIEW_REQUIRED", "path": "MIGRATION_REVIEW_REQUIRED", "speed_profile": "MIGRATION_REVIEW_REQUIRED", "movement_character": "MIGRATION_REVIEW_REQUIRED"},
        "setup_change_from_previous": {"position_changed": previous_shot_id is not None, "from_shot_id": previous_shot_id, "reason": "MIGRATION_REVIEW_REQUIRED", "continuity_strategy": ["unknown_geometry"]},
        "keyframes": [{"time_seconds": 0, "position": "MIGRATION_REVIEW_REQUIRED", "viewpoint": "MIGRATION_REVIEW_REQUIRED"}],
        "risk_controls": ["MIGRATION_REVIEW_REQUIRED"],
    }


def migrate(source: dict) -> tuple[dict, dict]:
    source_artifact = source.get("artifact", {})
    source_shots = source.get("shots") if isinstance(source.get("shots"), list) else []
    source_segments = source.get("generation_segments") if isinstance(source.get("generation_segments"), list) else []
    source_by_shot: dict[str, list[dict]] = {}
    for item in source_segments:
        if not isinstance(item, dict):
            continue
        source_by_shot.setdefault(item.get("shot_id", ""), []).append(item)

    shot_rows: list[dict] = []
    generated_segments: list[dict] = []
    registry: list[dict] = []
    record_cursor = 0.0
    scene_cursor = 0.0
    stable_shot_ids: list[str] = []
    for shot_index, source_shot in enumerate(source_shots, start=1):
        raw_id = source_shot.get("shot_id") if isinstance(source_shot, dict) else None
        shot_id = raw_id if isinstance(raw_id, str) and SHOT_RE.fullmatch(raw_id) else f"SEQ01_SC01_SH{shot_index:02d}"
        stable_shot_ids.append(shot_id)
        sequence_id = shot_id.split("_SC", 1)[0]
        scene_id = shot_id.rsplit("_SH", 1)[0]
        source_rows = source_by_shot.get(raw_id or shot_id, [])
        if not source_rows:
            source_rows = [{"duration_seconds": 1.0, "primary_performance_arc": "MIGRATION_REVIEW_REQUIRED"}]
        shot_start = scene_cursor
        first_entry_id = f"MIGRATED_{shot_index:02d}_IN"
        last_exit_id = f"MIGRATED_{shot_index:02d}_OUT"
        shot_states: list[tuple[str, str, dict, dict]] = []
        shot_segments: list[dict] = []
        for segment_index, source_segment in enumerate(source_rows, start=1):
            raw_duration = source_segment.get("duration_seconds", 1.0)
            try:
                duration = float(raw_duration)
            except (TypeError, ValueError):
                duration = 1.0
            duration = min(max(duration, 0.1), 10.0)
            entry_id = first_entry_id if segment_index == 1 else f"MIGRATED_{shot_index:02d}_SEG{segment_index:02d}_IN"
            exit_id = last_exit_id if segment_index == len(source_rows) else f"MIGRATED_{shot_index:02d}_SEG{segment_index:02d}_OUT"
            entry = state(entry_id, "MIGRATION_REVIEW_REQUIRED")
            exit_state = state(exit_id, "MIGRATION_REVIEW_REQUIRED")
            registry.extend([entry, exit_state])
            scene_start = scene_cursor
            scene_cursor += duration
            record_start = record_cursor
            record_cursor += duration
            segment_id = f"{shot_id}_SEG{segment_index:02d}"
            shot_segments.append({
                "segment_id": segment_id,
                "shot_id": shot_id,
                "shot_segment_index": segment_index,
                "duration_seconds": duration,
                "scene_time": {"start_seconds": scene_start, "end_seconds": scene_cursor},
                "source_time": {"start_seconds": 0, "end_seconds": duration},
                "record_time": {"start_seconds": record_start, "end_seconds": record_cursor},
                "entry_state": entry,
                "exit_state": exit_state,
                "continuity_contract": {"invariants": ["MIGRATION_REVIEW_REQUIRED"], "expected_deltas": ["MIGRATION_REVIEW_REQUIRED"], "forbidden_deltas": ["unreviewed continuity change"]},
                "camera_interval_map": [{"start_seconds": 0, "end_seconds": duration, "camera_setup_id": f"MIGRATED_{shot_index:02d}_SETUP", "motion": {"type": "static", "motivation": "MIGRATION_REVIEW_REQUIRED", "path": "MIGRATION_REVIEW_REQUIRED", "speed_profile": "MIGRATION_REVIEW_REQUIRED", "movement_character": "MIGRATION_REVIEW_REQUIRED"}}],
                "performance_arc_id": str(source_segment.get("primary_performance_arc", "MIGRATION_REVIEW_REQUIRED")),
                "four_track_timeline": [{"start_seconds": 0, "end_seconds": duration, "performance": "MIGRATION_REVIEW_REQUIRED", "camera": "MIGRATION_REVIEW_REQUIRED", "sound": "MIGRATION_REVIEW_REQUIRED", "edit_handoff": "MIGRATION_REVIEW_REQUIRED"}],
                "generation_handoff_to_next": None,
                "traceability": {"plot_beat_ids": source_shot.get("plot_beat_ids", []) or ["MIGRATION_REVIEW_REQUIRED"], "performance_beat_id": "MIGRATION_REVIEW_REQUIRED", "canon_reference_ids": [], "shot_id": shot_id, "acceptance_test_ids": ["MIGRATION_REVIEW_REQUIRED"]},
                "acceptance_criteria": ["MIGRATION_REVIEW_REQUIRED"],
            })
        shot_rows.append({
            "shot_id": shot_id,
            "sequence_id": sequence_id,
            "scene_id": scene_id,
            "shot_index": shot_index,
            "editorial_role": "establishing" if shot_index == 1 else ("terminal" if shot_index == len(source_shots) else "coverage"),
            "purpose": source_shot.get("purpose", "MIGRATION_REVIEW_REQUIRED"),
            "coverage_function": "MIGRATION_REVIEW_REQUIRED",
            "plot_beat_ids": source_shot.get("plot_beat_ids", []) or ["MIGRATION_REVIEW_REQUIRED"],
            "performance_beat_ids": ["MIGRATION_REVIEW_REQUIRED"],
            "staging": {"geography_id": "MIGRATED_GEOGRAPHY", "subject_positions": [{"subject_id": "MIGRATED_CHARACTER_REQUIRES_REVIEW", "zone": "unknown_zone", "relation_to_landmarks": ["unknown_landmark"]}], "action_path": "MIGRATION_REVIEW_REQUIRED", "eyelines": ["MIGRATION_REVIEW_REQUIRED"], "entry_exit": {"entry": "MIGRATION_REVIEW_REQUIRED", "exit": "MIGRATION_REVIEW_REQUIRED"}},
            "camera": camera(f"MIGRATED_{shot_index:02d}_SETUP", stable_shot_ids[-2] if shot_index > 1 else None),
            "scene_time": {"start_seconds": shot_start, "end_seconds": scene_cursor},
            "continuity_in": shot_segments[0]["entry_state"],
            "continuity_out": shot_segments[-1]["exit_state"],
            "incoming_boundary_id": None if shot_index == 1 else f"MIGRATED_BOUNDARY_{shot_index - 1:02d}",
            "outgoing_boundary_id": f"MIGRATED_BOUNDARY_{shot_index:02d}",
            "reference_bindings": [{"binding_id": "MIGRATION_REFERENCE", "asset_id": "MIGRATION_REVIEW_REQUIRED", "property_scope": ["identity", "geography", "camera"], "timeline_scope": "scene", "strength": "informational"}],
        })
        generated_segments.extend(shot_segments)

    boundaries: list[dict] = []
    handoffs: list[dict] = []
    for index, segment in enumerate(generated_segments):
        next_segment = generated_segments[index + 1] if index + 1 < len(generated_segments) else None
        if next_segment is None:
            relationship, endpoint_policy, boundary_id = "terminal", "none", f"MIGRATED_BOUNDARY_{len(shot_rows):02d}"
        elif next_segment["shot_id"] == segment["shot_id"]:
            relationship, endpoint_policy, boundary_id = "same_shot_continue", "stable_tail", None
        else:
            relationship, endpoint_policy, boundary_id = "independent", "none", f"MIGRATED_BOUNDARY_{next(i for i, row in enumerate(shot_rows, start=1) if row['shot_id'] == segment['shot_id']):02d}"
        handoff = {"handoff_id": f"MIGRATED_HANDOFF_{index + 1:02d}", "from_segment_id": segment["segment_id"], "to_segment_id": next_segment["segment_id"] if next_segment else None, "relationship": relationship, "endpoint_policy": endpoint_policy, "acceptance_conditions": ["MIGRATION_REVIEW_REQUIRED"], "editorial_boundary_id": boundary_id}
        segment["generation_handoff_to_next"] = handoff
        handoffs.append(handoff)
    for index, shot in enumerate(shot_rows):
        boundary_id = f"MIGRATED_BOUNDARY_{index + 1:02d}"
        boundaries.append({"boundary_id": boundary_id, "from_shot_id": shot["shot_id"], "to_shot_id": shot_rows[index + 1]["shot_id"] if index + 1 < len(shot_rows) else None, "mechanism": "end" if index + 1 == len(shot_rows) else "cut", "motivations": ["MIGRATION_REVIEW_REQUIRED"], "audio_behavior": "MIGRATION_REVIEW_REQUIRED", "picture_edit": {"type": "end" if index + 1 == len(shot_rows) else "cut"}, "audio_edit": {"type": "independent", "overlap_frames": 0, "room_tone_policy": "MIGRATION_REVIEW_REQUIRED"}, "record_time": {"start_seconds": 0, "end_seconds": 0}})
    # Boundary times are mechanical record cut positions; no editorial timing is invented.
    record_positions = [0.0]
    for shot in shot_rows:
        shot_segments = [item for item in generated_segments if item["shot_id"] == shot["shot_id"]]
        record_positions.append(float(shot_segments[-1]["record_time"]["end_seconds"]))
    for index, boundary in enumerate(boundaries):
        position = record_positions[index + 1]
        boundary["record_time"] = {"start_seconds": position, "end_seconds": position}
    for shot in shot_rows:
        shot["outgoing_boundary_id"] = boundaries[shot["shot_index"] - 1]["boundary_id"]
        shot["incoming_boundary_id"] = None if shot["shot_index"] == 1 else boundaries[shot["shot_index"] - 2]["boundary_id"]
    for handoff in handoffs:
        if handoff["editorial_boundary_id"]:
            source = next(item for item in generated_segments if item["segment_id"] == handoff["from_segment_id"])
            source_shot_index = next(item["shot_index"] for item in shot_rows if item["shot_id"] == source["shot_id"])
            handoff["editorial_boundary_id"] = boundaries[source_shot_index - 1]["boundary_id"]

    migrated = {
        "artifact": {
            "artifact_id": str(source_artifact.get("artifact_id", "storyboard_PRJ00_v01")).replace("_v01", "_v02") + "_migrated",
            "artifact_type": "storyboard-package-v2",
            "project_id": source_artifact.get("project_id", "PRJ00"),
            "version": int(source_artifact.get("version", 1)) + 1,
            "revision_id": str(source_artifact.get("revision_id", "storyboard_migrated@v01")).rsplit("@v", 1)[0] + "@v02",
            "created_from": [source_artifact.get("artifact_id", "unknown-source")],
            "source_versions": [{"artifact_id": source_artifact.get("artifact_id", "unknown-source"), "version": int(source_artifact.get("version", 1)), "revision_id": source_artifact.get("revision_id", "unknown-source@v01")}],
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "migrate_storyboard_v1_to_v2",
            "provenance": {"user_inputs": [], "source_assets": [], "upstream_artifacts": [source_artifact.get("artifact_id", "unknown-source")]},
        },
        "planning_model_version": 2,
        "migration": {"source_model_version": 1, "status": "needs_editorial_completion", "creative_fields_not_invented": ["scene_geography", "environment_lock", "camera.setup.position", "camera.setup.orientation", "camera.setup.optics", "camera.setup.composition", "camera.setup.axis", "camera.in_shot_motion", "continuity_in", "continuity_out", "limb_states", "editorial_boundaries", "generation_handoffs", "reference_bindings"], "source_artifact_revision": source_artifact.get("revision_id", ""), "migration_tool_version": "2.1"},
        "director_treatment": {"dramatic_engine": "MIGRATION_REVIEW_REQUIRED", "visual_grammar": "MIGRATION_REVIEW_REQUIRED", "coverage_strategy": "MIGRATION_REVIEW_REQUIRED", "camera_position_policy": "allowed_to_change_between_shots", "environment_lock": {"environment_profile_id": "MIGRATED_ENVIRONMENT", "source_asset_id": "MIGRATION_REVIEW_REQUIRED", "enforcement": "hard_reference_no_expansion", "required_landmarks": ["MIGRATION_REVIEW_REQUIRED"], "allowed_features": ["MIGRATION_ALLOWED_FEATURE_REQUIRES_REVIEW"], "forbidden_inventions": ["MIGRATION_FORBIDDEN_FEATURE_REQUIRES_REVIEW"], "unknown_regions": ["all-v1-geometry"], "negative_space_rule": "MIGRATION_REVIEW_REQUIRED", "camera_position_policy": "storyboard_owned_within_environment_lock"}},
        "scene_geography": {"geography_id": "MIGRATED_GEOGRAPHY", "coordinate_system": "MIGRATION_REVIEW_REQUIRED", "landmarks": [{"landmark_id": "unknown_landmark", "kind": "unknown", "description": "MIGRATION_REVIEW_REQUIRED", "confidence": "unknown", "reference_ids": []}], "axes": [], "unknown_regions": ["all-v1-geometry"], "allowed_camera_zones": ["unknown_zone"], "zones": [{"zone_id": "unknown_zone", "kind": "unknown", "description": "MIGRATION_REVIEW_REQUIRED", "adjacent_zone_ids": [], "visibility": "unknown"}], "relations": [], "reference_views": [{"view_id": "MIGRATION_VIEW", "asset_id": "MIGRATION_REVIEW_REQUIRED", "purpose": "MIGRATION_REVIEW_REQUIRED"}]},
        "shots": shot_rows,
        "generation_segments": generated_segments,
        "editorial_boundaries": boundaries,
        "generation_handoffs": handoffs,
        "continuity_registry": registry,
        "animatic_intent": {"scene_time_policy": "MIGRATION_REVIEW_REQUIRED", "record_time_policy": "mechanically carried from v1 durations", "pacing_notes": ["MIGRATION_REVIEW_REQUIRED"]},
        "creative_acceptance_tests": [{"test_id": "MIGRATION_REVIEW_REQUIRED", "scope": "all", "assertion": "MIGRATION_REVIEW_REQUIRED"}],
    }
    report = {"source_model_version": 1, "target_model_version": 2, "status": "needs_editorial_completion", "source_revision": source_artifact.get("revision_id"), "new_revision": migrated["artifact"]["revision_id"], "stable_ids_preserved": stable_shot_ids, "blocking_fields": migrated["migration"]["creative_fields_not_invented"], "next_owner": "storyboard-director", "upstream_revision_required": True}
    return migrated, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and (args.output is None or args.report is None):
        parser.error("--output and --report are required unless --dry-run is used")
    migrated, report = migrate(load(args.input))
    if args.dry_run:
        print(yaml.safe_dump(report, sort_keys=False))
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(migrated, sort_keys=False), encoding="utf-8")
    args.report.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    print(f"Wrote completion-blocked v2 migration to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
