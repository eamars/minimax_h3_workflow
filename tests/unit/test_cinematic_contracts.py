from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STORYBOARD_VALIDATOR = ROOT / "skills/storyboard-director/scripts/validate_storyboard.py"
sys.path.insert(0, str(ROOT / "skills/comfyui-workflow-compiler/scripts"))
import compile_workflow  # noqa: E402
from scripts.validate_review_document import canonical_hash  # noqa: E402


def load_validator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("storyboard_validator_for_tests", STORYBOARD_VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class CinematicContracts(unittest.TestCase):
    def run_validator(self, fixture: str, version: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(STORYBOARD_VALIDATOR), "--storyboard", str(ROOT / "tests/fixtures" / fixture), "--schema-version", version],
            capture_output=True,
            text=True,
        )

    def test_historical_v1_remains_readable(self):
        result = self.run_validator("storyboard-v1-historical.yaml", "1")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_cinematic_v2_fixture_passes(self):
        result = self.run_validator("storyboard-v2-real-cinematic.yaml", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        package = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        shot2 = next(item for item in package["shots"] if item["shot_id"].endswith("SH02"))
        self.assertTrue(shot2["camera"]["setup_change_from_previous"]["position_changed"])
        self.assertEqual(shot2["camera"]["setup"]["position"]["zone"], "basin")

    def test_v2_negative_cases_reject_false_positive_topology(self):
        validator = load_validator()
        fixture = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        cases = [
            ("camera zone", lambda p: p["shots"][0]["camera"]["setup"]["position"].update(zone="not-a-zone"), "CAMERA_GEOGRAPHY_UNKNOWN"),
            ("empty staging", lambda p: p["shots"][0].update(staging={}), "STAGING_INCOMPLETE"),
            ("wardrobe contradiction", lambda p: p["shots"][1]["continuity_in"]["character_states"][0].update(wardrobe_state="wet-red-shirt"), "CONTINUITY_STATE_CONTRADICTION"),
            ("camera interval setup", lambda p: p["generation_segments"][0]["camera_interval_map"][0].update(camera_setup_id="REMOVED_SETUP"), "CAMERA_INTERVAL_SETUP_UNKNOWN"),
            ("camera interval gap", lambda p: p["generation_segments"][0]["camera_interval_map"][0].update(start_seconds=1), "CAMERA_INTERVAL_NONMONOTONIC"),
            ("missing bilateral boundary", lambda p: p["shots"][1].update(incoming_boundary_id=None), "EDITORIAL_BOUNDARY_BILATERAL_MISMATCH"),
            ("removed handoff boundary", lambda p: p["generation_handoffs"][2].update(editorial_boundary_id="REMOVED_BOUNDARY"), "GENERATION_EDITORIAL_LINK_INVALID"),
            ("zero-length segment", lambda p: p["generation_segments"][0]["scene_time"].update(end_seconds=0), "TIME_RANGE_NONPOSITIVE"),
            ("segment outside shot", lambda p: p["generation_segments"][0]["scene_time"].update(start_seconds=5, end_seconds=6), "SEGMENT_SCENE_TIME_OUT_OF_SHOT"),
            ("same phase overlap", lambda p: p["shots"][1].update(coverage_phase="opening_arrival"), "SCENE_COVERAGE_OVERLAP_UNDECLARED"),
        ]
        for label, mutate, code in cases:
            package = copy.deepcopy(fixture)
            mutate(package)
            with self.subTest(label=label):
                with self.assertRaises(validator.ContractError) as context:
                    validator.validate_v2(package)
                self.assertIn(code, str(context.exception))

    def test_environment_and_limb_guards_reject_silent_expansion(self):
        validator = load_validator()
        fixture = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        forbidden_room = copy.deepcopy(fixture)
        forbidden_room["director_treatment"]["environment_lock"]["forbidden_inventions"] += ["bathtub", "full vanity", "corridor"]
        forbidden_room["scene_geography"]["zones"][0]["description"] = "full vanity, bathtub, and corridor"
        with self.assertRaises(validator.ContractError) as environment_failure:
            validator.validate_v2(forbidden_room)
        self.assertIn("ENVIRONMENT_FEATURE_FORBIDDEN", str(environment_failure.exception))

        divergent_limb = copy.deepcopy(fixture)
        divergent_limb["shots"][0]["continuity_in"]["limb_states"] = copy.deepcopy(divergent_limb["shots"][0]["continuity_in"]["limb_states"])
        divergent_limb["shots"][0]["continuity_in"]["limb_states"][0]["state"] = "contact"
        with self.assertRaises(validator.ContractError) as limb_failure:
            validator.validate_v2(divergent_limb)
        self.assertIn("CONTINUITY_SNAPSHOT_PAYLOAD_MISMATCH", str(limb_failure.exception))

        missing_limb = copy.deepcopy(fixture)
        missing_limb["shots"][0]["continuity_in"].pop("limb_states")
        with self.assertRaises(validator.ContractError) as missing_failure:
            validator.validate_v2(missing_limb)
        self.assertIn("CONTINUITY_STATE_INCOMPLETE", str(missing_failure.exception))

    def test_sparse_single_take_is_allowed_when_treatment_declares_it(self):
        validator = load_validator()
        package = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        package["director_treatment"]["coverage_policy"] = {"allow_sparse_coverage": True, "required_roles": []}
        package["shots"] = [copy.deepcopy(package["shots"][0])]
        shot = package["shots"][0]
        shot["editorial_role"] = "master"
        shot["outgoing_boundary_id"] = "BOUNDARY_SINGLE_END"
        shot["scene_time"] = {"start_seconds": 0, "end_seconds": 4}
        package["generation_segments"] = [copy.deepcopy(package["generation_segments"][0])]
        segment = package["generation_segments"][0]
        segment["scene_time"] = {"start_seconds": 0, "end_seconds": 4}
        segment["record_time"] = {"start_seconds": 0, "end_seconds": 4}
        segment["generation_handoff_to_next"] = {"handoff_id": "HANDOFF_SINGLE_END", "from_segment_id": segment["segment_id"], "to_segment_id": None, "relationship": "terminal", "endpoint_policy": "none", "acceptance_conditions": ["single take holds"], "editorial_boundary_id": "BOUNDARY_SINGLE_END"}
        package["editorial_boundaries"] = [{"boundary_id": "BOUNDARY_SINGLE_END", "from_shot_id": shot["shot_id"], "to_shot_id": None, "mechanism": "end", "motivations": ["single take terminates on the action"], "audio_behavior": "room tone resolves", "picture_edit": {"type": "end"}, "audio_edit": {"type": "independent", "overlap_frames": 0, "room_tone_policy": "resolve"}, "record_time": {"start_seconds": 4, "end_seconds": 4}}]
        package["generation_handoffs"] = [copy.deepcopy(segment["generation_handoff_to_next"])]
        validator.validate_v2(package)

    def test_prj01_bad_topology_is_rejected(self):
        result = self.run_validator("prj01-bad-storyboard-v2.yaml", "2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("V2_LEGACY_FIELDS_PRESENT", result.stderr)

    def test_compiler_guard_preserves_v2_topology(self):
        plan = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        plan["request_summary"] = {}
        plan["asset_reference_map"] = {}
        plan["canon"] = {}
        plan["plot"] = {}
        plan["scene_performance"] = {}
        plan["sound"] = {}
        plan["timelines"] = {}
        plan["pacing"] = {}
        plan["risks"] = []
        plan["dependencies"] = []
        plan["provisional_h3_modes"] = []
        plan["provisional_workflow_classes"] = []
        plan["acceptance_criteria"] = []
        plan["open_decisions"] = []
        plan["preflight"] = {}
        plan["rerender_exposure"] = {}
        plan["continuity_registry"] = copy.deepcopy(plan["continuity_registry"])
        plan["animatic_intent"] = copy.deepcopy(plan["animatic_intent"])
        plan["creative_acceptance_tests"] = copy.deepcopy(plan["creative_acceptance_tests"])
        plan["approval"] = {"plan_id": "x", "plan_version": 2, "plan_hash": "sha256:" + "a" * 64, "status": "pending", "approved_by": None, "approved_at": None, "approved_scope": [], "conditions": []}
        segment_id = plan["generation_segments"][0]["segment_id"]
        selected = plan["generation_segments"][0]
        bindings = {
            "segment_id": segment_id,
            "generation_relationship": selected["generation_handoff_to_next"]["relationship"],
            "endpoint_policy": selected["generation_handoff_to_next"]["endpoint_policy"],
            "camera_interval_map_hash": compile_workflow.canonical_hash(selected["camera_interval_map"]),
            "continuity_contract_hash": compile_workflow.canonical_hash(selected["continuity_contract"]),
        }
        segment = compile_workflow.validate_cinematic_plan(plan, bindings)
        self.assertEqual(segment["shot_id"], "SEQ01_SC01_SH01")
        broken = copy.deepcopy(plan)
        broken["generation_segments"][0]["transition_to_next"] = "cut"
        with self.assertRaises(AssertionError) as context:
            compile_workflow.validate_cinematic_plan(broken, bindings)
        self.assertIn("EDITORIAL_GENERATION_BOUNDARY_CONFLATED", str(context.exception))
        moving = plan["generation_segments"][1]
        moving_bindings = {
            "segment_id": moving["segment_id"],
            "generation_relationship": moving["generation_handoff_to_next"]["relationship"],
            "endpoint_policy": moving["generation_handoff_to_next"]["endpoint_policy"],
            "camera_interval_map_hash": compile_workflow.canonical_hash(moving["camera_interval_map"]),
            "continuity_contract_hash": compile_workflow.canonical_hash(moving["continuity_contract"]),
        }
        with self.assertRaises(AssertionError) as capability_failure:
            compile_workflow.validate_cinematic_plan(plan, moving_bindings, {"capabilities": {"moving_endpoint_continuation": False}})
        self.assertIn("MOVING_ENDPOINT_CAPABILITY_UNPROVEN", str(capability_failure.exception))
        compile_workflow.validate_cinematic_plan(plan, moving_bindings, {"capabilities": {"moving_endpoint_continuation": True}})

    def test_v1_to_v2_migration_is_explicitly_blocked_for_creative_completion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output = temp / "migrated.yaml"
            report = temp / "report.yaml"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate_storyboard_v1_to_v2.py"), "--input", str(ROOT / "tests/fixtures/storyboard-v1-historical.yaml"), "--output", str(output), "--report", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = yaml.safe_load(output.read_text(encoding="utf-8"))
            migration_report = yaml.safe_load(report.read_text(encoding="utf-8"))
            self.assertEqual(migrated["planning_model_version"], 2)
            self.assertEqual(migration_report["status"], "needs_editorial_completion")
            self.assertIn("camera.setup.position", migration_report["blocking_fields"])
            self.assertTrue(migrated["generation_segments"])
            self.assertNotEqual(migrated["artifact"]["revision_id"], "storyboard_PRJ99@v01")
            self.assertRegex(migrated["artifact"]["content_hash"], r"^sha256:[0-9a-f]{64}$")
            validator = load_validator()
            migrated_for_shape_check = copy.deepcopy(migrated)
            migrated_for_shape_check["migration"]["status"] = "complete"
            validator.validate_v2(migrated_for_shape_check)
            with self.assertRaises(validator.ContractError) as blocked:
                validator.validate_v2(migrated)
            self.assertIn("MIGRATION_REVIEW_REQUIRED", str(blocked.exception))
            dry_run = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate_storyboard_v1_to_v2.py"), "--input", str(ROOT / "tests/fixtures/storyboard-v1-historical.yaml"), "--dry-run"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stderr)

    def test_v2_review_pair_uses_v2_headings_and_hash_gate(self):
        storyboard = yaml.safe_load((ROOT / "tests/fixtures/storyboard-v2-real-cinematic.yaml").read_text(encoding="utf-8"))
        plan = {
            "artifact": dict(storyboard["artifact"], artifact_id="production_plan_PRJ99_v02", artifact_type="production-plan-v2", revision_id="production_plan_PRJ99@v02", status="review_ready"),
            "planning_model_version": 2,
            "request_summary": {},
            "asset_reference_map": {},
            "canon": {},
            "plot": {},
            "scene_performance": {},
            "sound": {},
            "director_treatment": storyboard["director_treatment"],
            "scene_geography": storyboard["scene_geography"],
            "shots": storyboard["shots"],
            "generation_segments": storyboard["generation_segments"],
            "editorial_boundaries": storyboard["editorial_boundaries"],
            "generation_handoffs": storyboard["generation_handoffs"],
            "continuity_registry": storyboard["continuity_registry"],
            "animatic_intent": storyboard["animatic_intent"],
            "creative_acceptance_tests": storyboard["creative_acceptance_tests"],
            "timelines": {},
            "pacing": {},
            "risks": [],
            "dependencies": [],
            "provisional_h3_modes": [],
            "provisional_workflow_classes": [],
            "acceptance_criteria": ["cinematic topology is traceable"],
            "open_decisions": [],
            "preflight": {},
            "rerender_exposure": {},
            "approval": {"plan_id": "production_plan_PRJ99", "plan_version": 2, "plan_hash": "", "status": "pending", "approved_by": None, "approved_at": None, "approved_scope": [], "conditions": []},
        }
        expected = canonical_hash(plan)
        plan["artifact"]["content_hash"] = expected
        plan["approval"]["plan_hash"] = expected
        headings = yaml.safe_load((ROOT / "skills/production-orchestrator/references/review-document-contract-v2.yaml").read_text(encoding="utf-8"))["required_sections"]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            yaml_path = temp / "production-plan-v02.yaml"
            markdown_path = temp / "production-plan-v02.md"
            yaml_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            markdown_path.write_text("\n".join(f"## {heading}" for heading in headings) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_review_document.py"), "--markdown", str(markdown_path), "--yaml", str(yaml_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            topology = subprocess.run(
                [sys.executable, str(ROOT / "scripts/validate_cinematic_package.py"), "--plan", str(yaml_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(topology.returncode, 0, topology.stderr)

    def test_contract_matrix_is_loaded_and_covers_v2_reader_cases(self):
        contract = yaml.safe_load((ROOT / "tests/contract/storyboard-director-contract.yaml").read_text(encoding="utf-8"))
        case_ids = {item["id"] for item in contract["cases"]}
        self.assertTrue({"cinematic_v2_reader", "camera_position_change", "boundary_split", "unknown_geometry", "moving_endpoint"} <= case_ids)
        result = self.run_validator("storyboard-v2-real-cinematic.yaml", "2")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_downstream_v2_contracts_are_strictly_separated(self):
        schema_dir = ROOT / "schemas"
        job = json.loads((schema_dir / "comfyui-job-v2.schema.json").read_text(encoding="utf-8"))
        dag = json.loads((schema_dir / "production-dag-v2.schema.json").read_text(encoding="utf-8"))
        qc = json.loads((schema_dir / "qc-report-v2.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(job["properties"]["planning_model_version"]["const"], 2)
        self.assertIn("camera_interval_map", job["required"])
        self.assertNotIn("edges", dag["properties"])
        self.assertNotIn("continue", dag["properties"]["generation_edges"]["items"]["properties"]["relation"]["enum"])
        self.assertIn("camera_path", qc["properties"]["mode"]["enum"])


if __name__ == "__main__":
    unittest.main()
