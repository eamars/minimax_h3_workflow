from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/comfyui-workflow-compiler/scripts"))
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
        "3": {"class_type": "SaveVideo", "inputs": {"video": ["2", 0], "filename_prefix": "video/test", "format": "auto", "codec": {"codec": "auto"} if codec is None else codec}},
    }


class LiveGraphValidator(unittest.TestCase):
    def test_autogrow_and_dynamic_combo_pass(self):
        validate(graph(), profile())

    def test_autogrow_gap_and_bad_dynamic_combo_fail(self):
        with self.assertRaisesRegex(AssertionError, "autogrow ordinals"):
            validate(graph(index=1), profile())
        with self.assertRaisesRegex(AssertionError, "dynamic-combo object"):
            validate(graph(codec="auto"), profile())


if __name__ == "__main__":
    unittest.main()
