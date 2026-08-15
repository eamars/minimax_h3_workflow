import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "skills/comfyui/scripts/build_h3_seamless_chain.py"
RUNTIME_PATH = (
    ROOT
    / "ComfyUI/custom_nodes/ComfyUI-H3-Multishot/h3_multishot_utils.py"
)
TEMPLATE = (
    ROOT
    / "ComfyUI/custom_nodes/ComfyUI-H3-Multishot/workflows/H3_Seamless_Chain_CORE.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class H3SeamlessChainBuilderTests(unittest.TestCase):
    def test_timed_script_parser_and_h3_alignment(self):
        runtime = load_module("h3_multishot_utils_test", RUNTIME_PATH)
        payload = json.dumps(
            {
                "shots": [
                    {"prompt": "First shot", "duration_seconds": 4},
                    {"prompt": "Second shot", "duration_seconds": 7},
                    {"prompt": "Third shot", "target_frames": 192},
                ]
            }
        )

        prompts, frames = runtime._parse_script_payload(payload)

        self.assertEqual(prompts, ["First shot", "Second shot", "Third shot"])
        self.assertEqual(frames, [96, 168, 192])
        self.assertEqual(runtime._h3_aligned_frame_count(96), 107)
        self.assertEqual(runtime._h3_aligned_frame_count(169), 175)
        self.assertEqual(runtime._h3_aligned_frame_count(193), 209)

    def test_builder_emits_one_exact_timed_hardware_locked_ui_workflow(self):
        builder = load_module("h3_seamless_builder_test", BUILDER_PATH)
        runner = load_module(
            "comfy_api_runner_test", ROOT / "scripts/comfy_api_runner.py"
        )
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            shot_input = temp_path / "shots.json"
            output = temp_path / "ready.ui.json"
            manifest = temp_path / "ready.manifest.json"
            shot_input.write_text(
                json.dumps(
                    {
                        "shots": [
                            {"prompt": "A quiet wide shot.", "duration_seconds": 4},
                            {"prompt": "The action continues.", "duration_seconds": 7},
                            {"prompt": "The scene resolves.", "duration_seconds": 8},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            builder.build(TEMPLATE, shot_input, output, manifest, "tests/exact-master")

            workflow = json.loads(output.read_text(encoding="utf-8"))
            report = json.loads(manifest.read_text(encoding="utf-8"))
            sampler = next(
                node for node in workflow["nodes"]
                if node["type"] == "H3MultishotSampler"
            )
            embedded = json.loads(
                sampler["properties"]["h3_widget_values"]["script"]
            )
            model = next(
                node for node in workflow["nodes"]
                if node["type"] == "UnetLoaderGGUFDynamicVRAM"
            )
            ready_note = next(
                node for node in workflow["nodes"]
                if node.get("title") == "READY — CLICK QUEUE PROMPT"
            )

            self.assertEqual(embedded["shots"][0]["target_frames"], 96)
            self.assertEqual(embedded["shots"][1]["target_frames"], 168)
            self.assertEqual(embedded["shots"][2]["target_frames"], 192)
            self.assertEqual(
                sampler["widgets_values"][0],
                sampler["properties"]["h3_widget_values"]["script"],
            )
            self.assertEqual(sampler["widgets_values"][1], 0)
            self.assertTrue(
                sampler["properties"]["h3_widget_values"]["save_every_shot"]
            )
            self.assertEqual(model["widgets_values"], [builder.LOCKED_MODEL])
            self.assertIn("Final duration: 19.000s", ready_note["widgets_values"][0])
            self.assertEqual(report["status"], "READY_TO_LOAD_AND_QUEUE")
            self.assertEqual(
                report["timing"],
                {
                    "fps": 24.0,
                    "exact": True,
                    "final_frames": 456,
                    "final_seconds": 19.0,
                    "model_frames_per_shot": [107, 175, 209],
                },
            )
            self.assertNotIn("sha", json.dumps(report).lower())
            self.assertNotIn("approval", json.dumps(report).lower())

            converted = runner.convert_workflow(
                workflow,
                {
                    "H3MultishotSampler": [
                        "script", "shot_count", "width", "height",
                        "frames_per_shot", "seed", "steps", "seed_per_shot",
                        "sampler_name", "scheduler", "self_anchor_voice",
                        "reference_image_size", "preview_first_shot",
                        "chain_gain_control", "save_every_shot", "output_scale",
                    ]
                },
            )
            self.assertEqual(converted["8"]["inputs"]["sampler_name"], "euler")
            self.assertEqual(converted["8"]["inputs"]["scheduler"], "beta")
            self.assertTrue(converted["8"]["inputs"]["preview_first_shot"])

    def test_builder_keeps_all_prompts_and_flattens_a_long_chain(self):
        builder = load_module("h3_seamless_builder_long_test", BUILDER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            shot_input = temp_path / "shots.json"
            output = temp_path / "ready.ui.json"
            manifest = temp_path / "ready.manifest.json"
            shot_input.write_text(
                json.dumps(
                    {
                        "shots": [
                            {"prompt": f"Complete shot prompt {i}.", "target_frames": 4}
                            for i in range(1, 10)
                        ]
                    }
                ),
                encoding="utf-8",
            )

            builder.build(TEMPLATE, shot_input, output, manifest, "tests/long-master")

            workflow = json.loads(output.read_text(encoding="utf-8"))
            report = json.loads(manifest.read_text(encoding="utf-8"))
            sampler = next(
                node for node in workflow["nodes"]
                if node["type"] == "H3MultishotSampler"
            )
            embedded = json.loads(
                sampler["properties"]["h3_widget_values"]["script"]
            )
            self.assertEqual(len(embedded["shots"]), 9)
            self.assertEqual(sampler["widgets_values"][1], 0)
            self.assertEqual(
                sampler["properties"]["h3_widget_values"]["chain_gain_control"],
                "flatten",
            )
            self.assertEqual(report["shot_count"], 9)
            self.assertEqual(report["timing"]["final_frames"], 36)


if __name__ == "__main__":
    unittest.main()
