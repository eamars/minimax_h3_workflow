from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
COMPILER = ROOT / "skills/comfyui-workflow-compiler/scripts/compile_workflow.py"


def fake_profile(template: dict, bindings: dict) -> dict:
    info = {}
    for node in template.values():
        inputs = {}
        for name in node["inputs"]:
            inputs[name] = ["*", {}]
        info[node["class_type"]] = {
            "input": {"required": inputs},
            "output": ["*", "*", "*", "*"],
            "output_node": node["class_type"] in {"SaveVideo", "SaveImage"},
        }
    return {
        "profile_hash": "sha256:" + "1" * 64,
        "evidence": {
            "object_info": info,
            "models": {
                "diffusion_models": [bindings["diffusion_model"]],
                "text_encoders": [bindings["text_encoder"]],
                "vae": [bindings["video_vae"], bindings["audio_vae"]],
            },
            "system_stats": {"comfyui_version": "fixture"},
        },
    }


class NonRenderingPipeline(unittest.TestCase):
    def test_review_pair_and_approved_compilation(self):
        review_yaml = ROOT / "examples/general-idea/plan/production-plan-v01.yaml"
        review_md = ROOT / "examples/general-idea/plan/production-plan-v01.md"
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_review_document.py"), "--markdown", str(review_md), "--yaml", str(review_yaml)],
            check=True,
            capture_output=True,
            text=True,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            plan = yaml.safe_load(review_yaml.read_text(encoding="utf-8"))
            plan["artifact"]["status"] = "approved"
            plan["approval"].update({"status": "approved", "approved_by": "fixture-human", "approved_at": "2026-08-08T00:01:00Z", "approved_scope": ["compile"]})
            plan_path = temp / "approved-plan.yaml"
            plan_path.write_text(yaml.safe_dump(plan, sort_keys=False), encoding="utf-8")
            approval = dict(plan["approval"])
            approval_path = temp / "approval.yaml"
            approval_path.write_text(yaml.safe_dump(approval, sort_keys=False), encoding="utf-8")
            bindings = yaml.safe_load((ROOT / "tests/fixtures/h3-t2va-bindings.yaml").read_text(encoding="utf-8"))
            bindings_path = temp / "bindings.yaml"
            bindings_path.write_text(yaml.safe_dump(bindings, sort_keys=True), encoding="utf-8")
            template = json.loads((ROOT / "workflow-catalog/templates/h3_t2va_api.json").read_text(encoding="utf-8"))
            profile_path = temp / "profile.json"
            profile_path.write_text(json.dumps(fake_profile(template, bindings)), encoding="utf-8")
            output, report = temp / "workflow.json", temp / "report.yaml"
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--plan", str(plan_path), "--approval", str(approval_path), "--catalog-root", str(ROOT / "workflow-catalog"), "--template-id", "h3-t2va-v1", "--bindings", str(bindings_path), "--capability-profile", str(profile_path), "--output", str(output), "--report", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.is_file())
            self.assertNotIn("${", output.read_text(encoding="utf-8"))
            self.assertEqual(yaml.safe_load(report.read_text(encoding="utf-8"))["status"], "PASS")

    def test_stale_hash_and_over_cap_emit_no_workflow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            plan = yaml.safe_load((ROOT / "examples/general-idea/plan/production-plan-v01.yaml").read_text(encoding="utf-8"))
            plan["artifact"]["status"] = "approved"
            plan["approval"]["status"] = "approved"
            plan_path = temp / "plan.yaml"
            plan_path.write_text(yaml.safe_dump(plan), encoding="utf-8")
            approval = dict(plan["approval"])
            approval["plan_hash"] = "sha256:" + "f" * 64
            approval_path = temp / "approval.yaml"
            approval_path.write_text(yaml.safe_dump(approval), encoding="utf-8")
            bindings = yaml.safe_load((ROOT / "tests/fixtures/h3-t2va-bindings.yaml").read_text(encoding="utf-8"))
            bindings["effective_duration_seconds"] = 11
            bindings_path = temp / "bindings.yaml"
            bindings_path.write_text(yaml.safe_dump(bindings), encoding="utf-8")
            template = json.loads((ROOT / "workflow-catalog/templates/h3_t2va_api.json").read_text(encoding="utf-8"))
            profile_path = temp / "profile.json"
            profile_path.write_text(json.dumps(fake_profile(template, bindings)), encoding="utf-8")
            output, report = temp / "workflow.json", temp / "report.yaml"
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--plan", str(plan_path), "--approval", str(approval_path), "--catalog-root", str(ROOT / "workflow-catalog"), "--template-id", "h3-t2va-v1", "--bindings", str(bindings_path), "--capability-profile", str(profile_path), "--output", str(output), "--report", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PLAN_HASH_MISMATCH", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(report.exists())
            approval["plan_hash"] = plan["artifact"]["content_hash"]
            approval_path.write_text(yaml.safe_dump(approval), encoding="utf-8")
            output2, report2 = temp / "workflow-over-cap.json", temp / "report-over-cap.yaml"
            result2 = subprocess.run(
                [sys.executable, str(COMPILER), "--plan", str(plan_path), "--approval", str(approval_path), "--catalog-root", str(ROOT / "workflow-catalog"), "--template-id", "h3-t2va-v1", "--bindings", str(bindings_path), "--capability-profile", str(profile_path), "--output", str(output2), "--report", str(report2)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result2.returncode, 0)
            self.assertIn("SEGMENT_TOO_LONG", result2.stderr)
            self.assertFalse(output2.exists())
            self.assertFalse(report2.exists())


if __name__ == "__main__":
    unittest.main()
