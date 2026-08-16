import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / ".agents/skills/comfyui/scripts/build_h3_seamless_chain.py"
RUNTIME_PATH = (
    ROOT
    / "ComfyUI/custom_nodes/ComfyUI-H3-Multishot/h3_multishot_utils.py"
)
TEMPLATE = (
    ROOT
    / "ComfyUI/custom_nodes/ComfyUI-H3-Multishot/workflows/H3_Seamless_Chain_CORE.json"
)

LOCKS = {
    "style": "Natural cinematic realism with restrained motion.",
    "identity": "The same adult subject in the same wardrobe.",
    "environment": "The same quiet room with the same furniture and layout.",
    "lighting": "The same soft window light from camera left.",
}

IDENTITY_REFERENCE = {
    "mode": "persistent_reference",
    "subject_id": "subject",
    "source_path": "canonical.png",
    "input_name": "canonical.png",
    "prompt_tokens": ["<Picture 1>"],
    "use_as_start_image": False,
}


def write_test_png(directory: Path) -> None:
    (directory / "canonical.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"contract-test"
    )


def continuity_shot(
    prompt,
    duration,
    opening_state,
    closing_state,
    opening_camera,
    closing_camera,
    opening_audio,
    closing_audio,
    *,
    first=False,
    opening_scene="The same quiet room.",
    closing_scene="The same quiet room.",
    transition_kind=None,
):
    shot = {
        "prompt": prompt,
        "duration_seconds": duration,
        "quality_controls": {
            "subject_instances": [
                {"subject_id": "subject", "max_visible_instances": 1}
            ],
            "dialogue_cues": [],
            "motion": {
                "mode": "static",
                "subject_id": "subject",
                "zone": opening_scene,
            },
            "visual_reset": {"mode": "no_reset"},
        },
        "continuity": {
            "opening_scene": opening_scene,
            "opening_state": opening_state,
            "opening_camera": opening_camera,
            "opening_audio": opening_audio,
            "opening_hold_seconds": 0 if first else 2,
            "closing_scene": closing_scene,
            "closing_state": closing_state,
            "closing_camera": closing_camera,
            "closing_audio": closing_audio,
            "closing_hold_seconds": 2,
        },
    }
    if opening_scene != closing_scene or opening_camera != closing_camera:
        shot["transition"] = {
            "kind": transition_kind or (
                "scene_change" if opening_scene != closing_scene
                else "continuous_camera_move"
            ),
            "at_seconds": duration / 2,
            "description": "make the declared visual-context change once, cleanly.",
        }
    return shot


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
            write_test_png(temp_path)
            shot_input.write_text(
                json.dumps(
                    {
                        "continuity_locks": LOCKS,
                        "identity_control": IDENTITY_REFERENCE,
                        "shots": [
                            continuity_shot(
                                "The subject crosses to the table.", 4,
                                "The subject stands beside the closed door.",
                                "The subject rests both hands on the table.",
                                "A locked waist-high wide frame faces the door.",
                                "A locked medium frame faces the table.",
                                "Quiet room tone with faint rain.",
                                "Quiet room tone with faint rain and one chair creak.",
                                first=True,
                            ),
                            continuity_shot(
                                "The subject opens a small notebook.", 7,
                                "The subject rests both hands on the table.",
                                "The subject holds the open notebook flat on the table.",
                                "A locked medium frame faces the table.",
                                "A locked close medium frame faces the notebook.",
                                "Quiet room tone with faint rain and one chair creak.",
                                "Quiet room tone with faint rain and soft paper settling.",
                            ),
                            continuity_shot(
                                "The subject reads, then closes the notebook.", 8,
                                "The subject holds the open notebook flat on the table.",
                                "The subject rests both hands on the closed notebook.",
                                "A locked close medium frame faces the notebook.",
                                "A locked close medium frame faces the notebook.",
                                "Quiet room tone with faint rain and soft paper settling.",
                                "Quiet room tone with faint rain.",
                            ),
                        ]
                    }
                ),
                encoding="utf-8",
            )

            builder.build(
                TEMPLATE, shot_input, output, manifest, "tests/exact-master",
                temp_path / "comfy-input",
            )

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
            self.assertIn("OPENING AIRLOCK — first 2.0 seconds", embedded["shots"][1]["prompt"])
            self.assertIn("MID-SEGMENT TRANSITION — at 3.5 seconds", embedded["shots"][1]["prompt"])
            self.assertIn("Never perform this transition at frame zero", embedded["shots"][1]["prompt"])
            self.assertIn("SETTLED LANDING — final 2.0 seconds", embedded["shots"][1]["prompt"])
            self.assertIn("主体数量锁", embedded["shots"][1]["prompt"])
            self.assertIn("对白门控", embedded["shots"][1]["prompt"])
            for value in LOCKS.values():
                self.assertIn(value, embedded["shots"][1]["prompt"])
            self.assertEqual(
                sampler["widgets_values"][0],
                sampler["properties"]["h3_widget_values"]["script"],
            )
            self.assertEqual(sampler["widgets_values"][1], 0)
            self.assertTrue(
                sampler["properties"]["h3_widget_values"]["save_every_shot"]
            )
            self.assertEqual(model["widgets_values"], [builder.LOCKED_REFERENCE_MODEL])
            self.assertIn("Final duration: 19.000s", ready_note["widgets_values"][0])
            self.assertEqual(report["status"], "READY_TO_LOAD_AND_QUEUE")
            self.assertEqual(
                report["continuity"]["status"], "STRICT_BOUNDARY_VALIDATED"
            )
            self.assertEqual(
                report["pre_generation"]["status"], "PRE_GENERATION_VALIDATED"
            )
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
            self.assertNotIn("validation", json.dumps(report).lower())

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
            write_test_png(temp_path)
            shot_input.write_text(
                json.dumps(
                    {
                        "continuity_locks": LOCKS,
                        "identity_control": IDENTITY_REFERENCE,
                        "shots": [
                            continuity_shot(
                                f"The subject performs action {i}.", 7,
                                f"The subject holds settled pose {i}.",
                                f"The subject holds settled pose {i + 1}.",
                                f"The camera holds position {i}.",
                                f"The camera holds position {i + 1}.",
                                f"The room carries audio state {i}.",
                                f"The room carries audio state {i + 1}.",
                                first=i == 1,
                            )
                            for i in range(1, 10)
                        ]
                    }
                ),
                encoding="utf-8",
            )

            builder.build(
                TEMPLATE, shot_input, output, manifest, "tests/long-master",
                temp_path / "comfy-input",
            )

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
            self.assertEqual(report["timing"]["final_frames"], 1512)

    def test_builder_rejects_phrase_only_multishot_handoffs(self):
        builder = load_module("h3_seamless_builder_reject_test", BUILDER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            shot_input = temp_path / "shots.json"
            shot_input.write_text(
                json.dumps(
                    {
                        "shots": [
                            {"prompt": "The action begins.", "duration_seconds": 7},
                            {
                                "prompt": "Continue from the exact final frame; "
                                "the next action begins immediately.",
                                "duration_seconds": 7,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                builder.WorkflowError, "Phrase-only handoffs are not sufficient"
            ):
                builder.build(
                    TEMPLATE,
                    shot_input,
                    temp_path / "invalid.ui.json",
                    temp_path / "invalid.manifest.json",
                    "tests/invalid",
                )

    def test_builder_rejects_multishot_without_persistent_identity_reference(self):
        builder = load_module("h3_seamless_builder_identity_gate_test", BUILDER_PATH)
        first = continuity_shot(
            "The subject waits.", 7,
            "The subject stands at center.",
            "The subject stands at center.",
            "A fixed medium frame faces the subject.",
            "A fixed medium frame faces the subject.",
            "Quiet room tone.",
            "Quiet room tone.",
            first=True,
        )
        second = continuity_shot(
            "The subject continues waiting.", 7,
            "The subject stands at center.",
            "The subject stands at center.",
            "A fixed medium frame faces the subject.",
            "A fixed medium frame faces the subject.",
            "Quiet room tone.",
            "Quiet room tone.",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unanchored-identity.json"
            path.write_text(
                json.dumps({
                    "continuity_locks": LOCKS,
                    "identity_control": {
                        "mode": "not_applicable",
                        "reason": "No reference was supplied.",
                    },
                    "shots": [first, second],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "CANON_IDENTITY_BINDING_MISSING"):
                builder.load_shots(path)

    def test_builder_rejects_boundary_mismatch_and_short_action_budget(self):
        builder = load_module("h3_seamless_builder_boundary_test", BUILDER_PATH)
        first = continuity_shot(
            "The subject crosses to the table.", 7,
            "The subject stands beside the door.",
            "The subject rests both hands on the table.",
            "A fixed wide frame faces the door.",
            "A fixed medium frame faces the table.",
            "Quiet room tone.",
            "Quiet room tone with rain.",
            first=True,
        )
        valid_second = continuity_shot(
            "The subject opens a notebook.", 7,
            "The subject rests both hands on the table.",
            "The subject holds the open notebook.",
            "A fixed medium frame faces the table.",
            "A fixed medium frame faces the table.",
            "Quiet room tone with rain.",
            "Quiet room tone with rain.",
        )
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)

            mismatch = json.loads(json.dumps(valid_second))
            mismatch["continuity"]["opening_camera"] = "An unrelated close-up."
            mismatch_input = temp_path / "mismatch.json"
            mismatch_input.write_text(
                json.dumps({"continuity_locks": LOCKS, "identity_control": IDENTITY_REFERENCE, "shots": [first, mismatch]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "camera mismatch"):
                builder.load_shots(mismatch_input)

            too_short = json.loads(json.dumps(valid_second))
            too_short["duration_seconds"] = 5
            short_input = temp_path / "short.json"
            short_input.write_text(
                json.dumps({"continuity_locks": LOCKS, "identity_control": IDENTITY_REFERENCE, "shots": [first, too_short]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "only 1.00s"):
                builder.load_shots(short_input)

    def test_builder_rejects_text_only_scene_reset_and_camera_transition_at_boundary(self):
        builder = load_module("h3_seamless_builder_transition_test", BUILDER_PATH)
        first = continuity_shot(
            "The subject crosses to the table.", 8,
            "The subject stands beside the door.",
            "The subject rests both hands on the table.",
            "A fixed wide frame faces the door.",
            "A fixed medium frame faces the table.",
            "Quiet room tone.",
            "Quiet room tone.",
            first=True,
        )
        second = continuity_shot(
            "The subject enters the garden.", 8,
            "The subject rests both hands on the table.",
            "The subject stands beside the garden gate.",
            "A fixed medium frame faces the table.",
            "A fixed wide frame faces the garden gate.",
            "Quiet room tone.",
            "Quiet garden ambience.",
            opening_scene="The same quiet room.",
            closing_scene="The enclosed garden at dusk.",
            transition_kind="scene_change",
        )
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            missing = json.loads(json.dumps(second))
            missing.pop("transition")
            missing_path = temp_path / "missing-transition.json"
            missing_path.write_text(
                json.dumps({"continuity_locks": LOCKS, "identity_control": IDENTITY_REFERENCE, "shots": [first, missing]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "TEXT_ONLY_SCENE_RESET_UNSAFE"):
                builder.load_shots(missing_path)

            boundary = json.loads(json.dumps(second))
            boundary["continuity"]["closing_scene"] = boundary["continuity"]["opening_scene"]
            boundary["transition"]["kind"] = "continuous_camera_move"
            boundary["quality_controls"]["visual_reset"] = {"mode": "no_reset"}
            boundary["transition"]["at_seconds"] = 0
            boundary_path = temp_path / "boundary-transition.json"
            boundary_path.write_text(
                json.dumps({"continuity_locks": LOCKS, "identity_control": IDENTITY_REFERENCE, "shots": [first, boundary]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "protected middle window"):
                builder.load_shots(boundary_path)

    def test_builder_rejects_untimed_and_previsibility_dialogue(self):
        builder = load_module("h3_seamless_builder_dialogue_test", BUILDER_PATH)
        first = continuity_shot(
            "The officer says <d>[English]Go now.</d>", 7,
            "The subject waits beside the door.",
            "The subject remains beside the door.",
            "A fixed medium frame faces the door.",
            "A fixed medium frame faces the door.",
            "Quiet room tone.",
            "Quiet room tone.",
            first=True,
        )
        second = continuity_shot(
            "The subject remains still.", 7,
            "The subject remains beside the door.",
            "The subject remains beside the door.",
            "A fixed medium frame faces the door.",
            "A fixed medium frame faces the door.",
            "Quiet room tone.",
            "Quiet room tone.",
        )
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            missing_path = temp_path / "missing-dialogue-cue.json"
            missing_path.write_text(
                json.dumps({
                    "continuity_locks": LOCKS,
                    "identity_control": IDENTITY_REFERENCE,
                    "shots": [first, second],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "DIALOGUE_WINDOW_MISSING"):
                builder.load_shots(missing_path)

            early = json.loads(json.dumps(first))
            early["quality_controls"]["dialogue_cues"] = [{
                "speaker_id": "officer",
                "start_seconds": 1.0,
                "end_seconds": 2.0,
                "visibility": "on_screen",
                "visible_from_seconds": 1.5,
            }]
            early_path = temp_path / "early-dialogue.json"
            early_path.write_text(
                json.dumps({
                    "continuity_locks": LOCKS,
                    "identity_control": IDENTITY_REFERENCE,
                    "shots": [early, second],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "SPEAKER_VISIBILITY_UNBOUND"):
                builder.load_shots(early_path)

    def test_builder_rejects_unsigned_motion_path(self):
        builder = load_module("h3_seamless_builder_motion_test", BUILDER_PATH)
        first = continuity_shot(
            "The subject enters the room.", 7,
            "The subject stands at the doorway.",
            "The subject stands beside the table.",
            "A fixed wide frame faces the doorway.",
            "A fixed wide frame faces the doorway.",
            "Quiet room tone.",
            "Quiet room tone.",
            first=True,
        )
        first["quality_controls"]["motion"] = {
            "mode": "path",
            "subject_id": "subject",
            "from_zone": "doorway",
            "to_zone": "table",
            "direction": "inward",
            "endpoint_state": "standing beside the table",
        }
        second = continuity_shot(
            "The subject remains still.", 7,
            "The subject stands beside the table.",
            "The subject stands beside the table.",
            "A fixed wide frame faces the doorway.",
            "A fixed wide frame faces the doorway.",
            "Quiet room tone.",
            "Quiet room tone.",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unsigned-path.json"
            path.write_text(
                json.dumps({
                    "continuity_locks": LOCKS,
                    "identity_control": IDENTITY_REFERENCE,
                    "shots": [first, second],
                }),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(builder.WorkflowError, "forbidden_directions"):
                builder.load_shots(path)

    def test_builder_wires_and_stages_persistent_identity_reference(self):
        builder = load_module("h3_seamless_builder_identity_test", BUILDER_PATH)
        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory)
            source = temp_path / "canonical.png"
            source.write_bytes(b"\x89PNG\r\n\x1a\n" + b"contract-test")
            input_root = temp_path / "comfy-input"
            shot_input = temp_path / "shots.json"
            output = temp_path / "ready.ui.json"
            manifest = temp_path / "ready.manifest.json"
            first = continuity_shot(
                "The subject raises one hand.", 7,
                "The subject stands at center.",
                "The subject stands at center with one hand raised.",
                "A fixed medium frame faces the subject.",
                "A fixed medium frame faces the subject.",
                "Quiet room tone.",
                "Quiet room tone.",
                first=True,
            )
            second = continuity_shot(
                "The subject lowers the hand.", 7,
                "The subject stands at center with one hand raised.",
                "The subject stands at center with both hands lowered.",
                "A fixed medium frame faces the subject.",
                "A fixed medium frame faces the subject.",
                "Quiet room tone.",
                "Quiet room tone.",
            )
            shot_input.write_text(
                json.dumps({
                    "continuity_locks": LOCKS,
                    "identity_control": {
                        "mode": "persistent_reference",
                        "subject_id": "subject",
                        "source_path": "canonical.png",
                        "input_name": "canonical-staged.png",
                        "prompt_tokens": ["<Picture 1>"],
                        "use_as_start_image": True,
                    },
                    "shots": [first, second],
                }),
                encoding="utf-8",
            )

            builder.build(
                TEMPLATE,
                shot_input,
                output,
                manifest,
                "tests/identity-master",
                input_root,
            )

            workflow = json.loads(output.read_text(encoding="utf-8"))
            report = json.loads(manifest.read_text(encoding="utf-8"))
            sampler = next(node for node in workflow["nodes"] if node["type"] == "H3MultishotSampler")
            model = next(node for node in workflow["nodes"] if node["type"] == "UnetLoaderGGUFDynamicVRAM")
            loader = next(node for node in workflow["nodes"] if node["type"] == "LoadImage")
            inputs = {item["name"]: item for item in sampler["inputs"]}
            embedded = json.loads(sampler["properties"]["h3_widget_values"]["script"])

            self.assertEqual(model["widgets_values"], [builder.LOCKED_REFERENCE_MODEL])
            self.assertIsNotNone(inputs["reference_images"]["link"])
            self.assertIsNotNone(inputs["start_image"]["link"])
            self.assertEqual(loader["widgets_values"][0], "canonical-staged.png")
            self.assertTrue((input_root / "canonical-staged.png").is_file())
            self.assertIn("<Picture 1>", embedded["shots"][1]["prompt"])
            self.assertEqual(
                report["pre_generation"]["identity_binding"]["mode"],
                "persistent_reference",
            )


if __name__ == "__main__":
    unittest.main()
