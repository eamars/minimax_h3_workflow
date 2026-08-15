from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agents/skills/post-editor/scripts/build_concat_graph.py"
SPEC = importlib.util.spec_from_file_location("concat_builder", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PostConcatBuilderContract(unittest.TestCase):
    def test_three_way_graph_keeps_picture_and_audio_chain(self):
        graph = MODULE.build_graph(["a.mp4", "b.mp4", "c.mp4"], 24, "edit/master")
        loaders = [node for node in graph.values() if node["class_type"] == "LoadVideo"]
        images = [node for node in graph.values() if node["class_type"] == "ImageBatch"]
        audios = [node for node in graph.values() if node["class_type"] == "AudioConcat"]
        self.assertEqual(len(loaders), 3)
        self.assertEqual(len(images), 2)
        self.assertEqual(len(audios), 2)
        save = next(node for node in graph.values() if node["class_type"] == "SaveVideo")
        self.assertEqual(save["inputs"]["codec"], "auto")
        self.assertEqual(save["inputs"]["filename_prefix"], "edit/master")

    def test_unsafe_source_and_single_source_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            MODULE.build_graph(["only.mp4"], 24, "out")
        with self.assertRaisesRegex(ValueError, "relative"):
            MODULE.build_graph(["a.mp4", "../b.mp4"], 24, "out")

    def test_three_way_graph_passes_generic_live_profile(self):
        profile = {
            "evidence": {
                "object_info": {
                    "LoadVideo": {"input": {"required": {"file": ["COMBO", {"options": [], "video_upload": True}]}}, "output": ["VIDEO"], "output_node": False},
                    "GetVideoComponents": {"input": {"required": {"video": ["VIDEO", {}]}}, "output": ["IMAGE", "AUDIO", "FLOAT", "INT"], "output_node": False},
                    "ImageBatch": {"input": {"required": {"image1": ["IMAGE", {}], "image2": ["IMAGE", {}]}}, "output": ["IMAGE"], "output_node": False},
                    "AudioConcat": {"input": {"required": {"audio1": ["AUDIO", {}], "audio2": ["AUDIO", {}], "direction": ["COMBO", {"options": ["after", "before"]}]}}, "output": ["AUDIO"], "output_node": False},
                    "CreateVideo": {"input": {"required": {"images": ["IMAGE", {}], "fps": ["FLOAT", {}]}, "optional": {"audio": ["AUDIO", {}], "bit_depth": ["INT", {"min": 8, "max": 10}]}}, "output": ["VIDEO"], "output_node": False},
                    "SaveVideo": {"input": {"required": {"video": ["VIDEO", {}], "filename_prefix": ["STRING", {}], "format": ["COMBO", {"options": ["auto"]}], "codec": ["COMFY_DYNAMICCOMBO_V3", {"options": [{"key": "auto", "inputs": {"required": {}}}]}]}}, "output": ["VIDEO"], "output_node": True},
                }
            }
        }
        graph = MODULE.build_graph(["a.mp4", "b.mp4", "c.mp4"], 24, "edit/master")
        MODULE.validate_graph(graph, profile)


if __name__ == "__main__":
    unittest.main()
