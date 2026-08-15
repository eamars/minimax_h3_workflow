from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.compile_workflow import replace, validate


ROOT = Path(__file__).resolve().parents[2]


class SystemContracts(unittest.TestCase):
    def test_t2va_template_compiles_without_placeholders(self):
        template = json.loads((ROOT / "workflow-catalog/templates/h3_t2va_api.json").read_text(encoding="utf-8"))
        bindings = yaml.safe_load((ROOT / "tests/fixtures/h3-t2va-bindings.yaml").read_text(encoding="utf-8"))
        graph = replace(template, bindings)
        validate(graph)
        self.assertNotIn("${", json.dumps(graph))
        self.assertEqual(graph["20"]["inputs"]["length"], 243)
        self.assertEqual(graph["42"]["inputs"]["length"], 240)

    def test_storyboard_cap_is_exact(self):
        common = json.loads((ROOT / "schemas/common-defs.schema.json").read_text(encoding="utf-8"))
        rule = common["$defs"]["generationSegment"]["properties"]["duration_seconds"]
        self.assertEqual(rule, {"type": "number", "exclusiveMinimum": 0, "maximum": 10})

    def test_planning_order(self):
        routing = yaml.safe_load((ROOT / ".agents/skills/production-orchestrator/references/routing-policy.yaml").read_text(encoding="utf-8"))
        order = [item["skill"] for item in routing["planning_dispatch"] if item.get("type") == "skill"]
        self.assertEqual(order, [
            "request-normalizer", "reference-canon-manager", "plot-architect",
            "scene-performance-writer", "sound-dialogue-planner", "storyboard-director",
            "animatic-previs-planner", "production-preflight-reviewer",
        ])


if __name__ == "__main__":
    unittest.main()
