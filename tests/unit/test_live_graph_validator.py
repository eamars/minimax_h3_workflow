from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agents/skills/comfyui-workflow-compiler/scripts"))
from validate_live_graph import validate  # noqa: E402


def profile():
    return {
        "LoadImage": {"input": {"required": {"image": [["reference.png"], {}]}}, "output": ["IMAGE"], "output_node": False},
        "Reference": {
            "input": {
                "required": {},
                "optional": {
                    "ref_images": ["COMFY_AUTOGROW_V3", {"template": {"input": {"required": {"ref_image": ["IMAGE", {}]}}, "prefix": "ref_image_", "min": 0, "max": 9}}]
                },
            },
            "output": ["VIDEO"],
            "output_node": False,
        },
        "SaveVideo": {
            "input": {
                "required": {
                    "video": ["VIDEO", {}],
                    "filename_prefix": ["STRING", {}],
                    "format": ["COMBO", {"options": ["auto"]}],
                    "codec": ["COMFY_DYNAMICCOMBO_V3", {"options": [{"key": "auto", "inputs": {"required": {}}}]}],
                }
            },
            "output": ["VIDEO"],
            "output_node": True,
        },
    }


def graph(index=0, codec=None):
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": "reference.png"}},
        "2": {"class_type": "Reference", "inputs": {f"ref_images.ref_image_{index}": ["1", 0]}},
        "3": {"class_type": "SaveVideo", "inputs": {"video": ["2", 0], "filename_prefix": "video/test", "format": "auto", "codec": "auto" if codec is None else codec}},
    }


class LiveGraphValidator(unittest.TestCase):
    def test_autogrow_and_dynamic_combo_pass(self):
        validate(graph(), profile())

    def test_autogrow_gap_and_bad_dynamic_combo_fail(self):
        with self.assertRaisesRegex(AssertionError, "autogrow ordinals"):
            validate(graph(index=1), profile())
        with self.assertRaisesRegex(AssertionError, "dynamic-combo selector string"):
            validate(graph(codec={"codec": "auto"}), profile())

    def test_catalog_savevideo_dynamic_selectors_are_scalar(self):
        catalog_root = ROOT / "workflow-catalog"
        catalog = yaml.safe_load((catalog_root / "catalog.yaml").read_text(encoding="utf-8"))
        savevideo_templates = []
        for entry in catalog["templates"]:
            graph_data = json.loads((catalog_root / entry["file"]).read_text(encoding="utf-8"))
            for node in graph_data.values():
                if node.get("class_type") == "SaveVideo":
                    savevideo_templates.append((entry["template_id"], node["inputs"].get("codec")))
        self.assertGreaterEqual(len(savevideo_templates), 1)
        for template_id, codec in savevideo_templates:
            self.assertIsInstance(codec, str, template_id)
            self.assertEqual(codec, "auto", template_id)


if __name__ == "__main__":
    unittest.main()
