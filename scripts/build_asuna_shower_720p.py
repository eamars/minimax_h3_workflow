"""Build the native 720p-class MiniMax H3 Asuna shower workflow."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "workflows" / "minimax_h3_ref2v-gguf_kazusa_nude_10s.json"
WORKFLOW_OUT = ROOT / "workflows" / "minimax_h3_ref2v-gguf_asuna_shower_720p_10s.json"
STORYBOARD_OUT = ROOT / "storyboards" / "asuna_shower_720p_10s.json"

CHARACTER_SOURCE = ROOT / "seeding_material" / "characters" / "asuna" / "all_in_one.png"
SETTING_SOURCE = ROOT / "seeding_material" / "settings" / "showerbox" / "shower_box_kazusa_style.png"
COMFY_INPUT = ROOT / "ComfyUI" / "input"
CHARACTER_INPUT_NAME = "all_in_one.png"
SETTING_INPUT_NAME = "shower_box_kazusa_style.png"

WIDTH = 1280
HEIGHT = 736  # H3 requires 32-pixel canvas alignment; this is its 720p-class 16:9 size.
FPS = 24
DURATION_SECONDS = 10.0
MODEL_LENGTH = 243  # H3 temporal alignment: frame_count % 17 == 5 (~10.125 s at 24 fps).
OUTPUT_FRAMES = 240  # Trim the aligned H3 output to exactly 10.0 seconds at 24 fps.

PROMPT = """<Picture 1> <Picture 2>

CHARACTER LOCK: Asuna is a clearly adult woman, the same adult character shown in Picture 1. Preserve her long light-blonde hair, blue eyes, blue hair ribbon, facial identity, natural adult proportions, and calm adult presence. Do not make her look younger.

SETTING LOCK: Picture 2 is the shower-box setting reference. Keep the same dark tiled glass shower enclosure, rainfall shower head, handheld shower, warm recessed ceiling light, wet reflective tiles, pink-red shelf light, dark towels, sakura-patterned towel details, bath products, and intimate evening bathroom atmosphere. Preserve the architecture, prop placement, lighting direction, and camera axis.

STYLE LOCK: cinematic naturalism, elegant fine-art nude study, explicit adult nudity but non-graphic and non-sexual, respectful composition, realistic water and steam, soft film grain, restrained contrast, no text and no logos. Keep the nude setting tasteful and framed by shower water, steam, shadow, and composition.

SCENE / 0-10 seconds: Asuna stands inside the shower box beneath the rainfall shower, already wet from the water. She slowly turns her shoulders three-quarters toward the camera, lifts one hand to sweep wet hair away from her face, then lowers it to rest lightly against the tiled wall. Water streams over her hair and shoulders while steam gathers on the glass and the warm shelf light glows behind her. Keep the shower box and its fixtures legible throughout.

CAMERA: fixed medium shot from outside the glass shower box, gentle five-percent push-in only, no cut, no orbit, no lens change, stable horizon. Preserve the same background geometry and lighting direction from the setting reference.

TIMELINE: 0-2s establish the rainfall shower and Asuna's still adult pose; 2-5s slow shoulder turn and relaxed breath; 5-8s hand brushes wet hair away from her face; 8-10s settle into a quiet three-quarter pose as water and steam continue moving.

AUDIO: continuous rainfall shower, soft water striking tile and glass, subtle bathroom echo, gentle steam hiss, quiet natural breathing; no dialogue, no vocals, no music."""


def node_by_id(workflow: dict, node_id: int) -> dict:
    return next(node for node in workflow["nodes"] if node["id"] == node_id)


def input_by_name(node: dict, name: str) -> dict:
    return next(item for item in node["inputs"] if item["name"] == name)


def add_exact_duration_trim(workflow: dict) -> None:
    """Trim H3's 243 aligned frames/audio samples to an exact 10 seconds."""
    template_workflow = json.loads(
        (ROOT / "workflows" / "minimax_h3_ref2v-gguf_kazusa_bath_2scene_1080p_4090.json").read_text(encoding="utf-8")
    )
    video_trim = copy.deepcopy(node_by_id(template_workflow, 162))
    audio_trim = copy.deepcopy(node_by_id(template_workflow, 164))
    video_trim.update(
        {
            "id": 160,
            "title": "Trim video to exact 10.0 seconds",
            "order": 20,
            "widgets_values": [0, OUTPUT_FRAMES],
        }
    )
    video_trim["inputs"][0]["link"] = 282
    video_trim["outputs"][0]["links"] = [284]
    audio_trim.update(
        {
            "id": 161,
            "title": "Trim audio to exact 10.0 seconds",
            "order": 21,
            "widgets_values": [0.0, DURATION_SECONDS],
        }
    )
    audio_trim["inputs"][0]["link"] = 283
    audio_trim["outputs"][0]["links"] = [285]
    workflow["nodes"].extend([video_trim, audio_trim])

    video_decode = node_by_id(workflow, 126)
    video_decode["outputs"][0]["links"] = []
    audio_decode = node_by_id(workflow, 125)
    audio_decode["outputs"][0]["links"] = []
    create_video = node_by_id(workflow, 132)
    input_by_name(create_video, "images")["link"] = 284
    input_by_name(create_video, "audio")["link"] = 285

    workflow["links"] = [link for link in workflow["links"] if link[0] not in {240, 241}]
    workflow["links"].extend(
        [
            [282, 126, 0, 160, 0, "IMAGE"],
            [283, 125, 0, 161, 0, "AUDIO"],
            [284, 160, 0, 132, 0, "IMAGE"],
            [285, 161, 0, 132, 1, "AUDIO"],
        ]
    )


def sync_seed(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Seed image not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if source.read_bytes() != destination.read_bytes():
            raise RuntimeError(f"Refusing to overwrite a different existing seed: {destination}")
        return
    shutil.copy2(source, destination)


def build_workflow() -> dict:
    workflow = json.loads(SOURCE.read_text(encoding="utf-8"))
    workflow["id"] = "asuna-shower-ref2v-720p-10s"

    resolution = node_by_id(workflow, 115)
    resolution["widgets_values"] = ["16:9 (Widescreen)", 0.9, 32]

    duration = node_by_id(workflow, 135)
    duration["widgets_values"] = [DURATION_SECONDS]

    reference = node_by_id(workflow, 145)
    reference["widgets_values"] = [PROMPT, WIDTH, HEIGHT, MODEL_LENGTH, "match"]

    add_exact_duration_trim(workflow)

    character_seed = node_by_id(workflow, 149)
    character_seed["title"] = "Asuna character seed — all_in_one.png"
    character_seed["widgets_values"][0] = CHARACTER_INPUT_NAME

    setting_seed = node_by_id(workflow, 156)
    setting_seed["title"] = "Shower box setting seed"
    setting_seed["widgets_values"][0] = SETTING_INPUT_NAME

    # The reference node accepts up to nine images. Keep only the requested
    # character and setting references so Picture 1/Picture 2 remain unambiguous.
    removed_node_ids = {157, 158, 159}
    workflow["nodes"] = [node for node in workflow["nodes"] if node["id"] not in removed_node_ids]
    for index in range(2, 5):
        input_by_name(reference, f"ref_images.ref_image_{index}")["link"] = None
    workflow["links"] = [link for link in workflow["links"] if link[1] not in removed_node_ids and link[3] not in removed_node_ids]
    workflow["last_node_id"] = max(node["id"] for node in workflow["nodes"])
    workflow["last_link_id"] = max(link[0] for link in workflow["links"])

    save = node_by_id(workflow, 92)
    save["widgets_values"][0] = "video/MiniMax_H3_Asuna_Shower_720p_10s"

    workflow.setdefault("extra", {})["asuna_shower_720p_10s"] = {
        "source_workflow": SOURCE.name,
        "character_seed": "seeding_material/characters/asuna/all_in_one.png",
        "setting_seed": "seeding_material/settings/showerbox/shower_box_kazusa_style.png",
        "comfy_input_files": [CHARACTER_INPUT_NAME, SETTING_INPUT_NAME],
        "native_resolution": [WIDTH, HEIGHT],
        "resolution_note": "H3 canvas alignment uses 1280x736 as the nearest valid 720p-class 16:9 canvas; native generation, no upscale node.",
        "fps": FPS,
        "duration_seconds_nominal": DURATION_SECONDS,
        "output_frames": OUTPUT_FRAMES,
        "model_length_frames": MODEL_LENGTH,
        "reference_order": ["Picture 1 = Asuna character sheet", "Picture 2 = shower box setting"],
        "nude_settings": "Preserved from the Kazusa nude reference workflow: explicit adult fine-art nude, non-graphic, non-sexual, respectful framing.",
    }
    return workflow


def build_storyboard() -> dict:
    return {
        "workflow": WORKFLOW_OUT.name,
        "source_workflow": SOURCE.name,
        "type": "single_reference_to_video",
        "character": "Asuna — clearly adult fictional character",
        "references": [
            {"tag": "Picture 1", "role": "character identity", "source": "seeding_material/characters/asuna/all_in_one.png", "comfy_input": CHARACTER_INPUT_NAME},
            {"tag": "Picture 2", "role": "shower box setting", "source": "seeding_material/settings/showerbox/shower_box_kazusa_style.png", "comfy_input": SETTING_INPUT_NAME},
        ],
        "generation": {
            "width": WIDTH,
            "height": HEIGHT,
            "resolution_label": "720p-class native H3 canvas",
            "fps": FPS,
            "duration_seconds_nominal": DURATION_SECONDS,
            "output_frames": OUTPUT_FRAMES,
            "model_length_frames": MODEL_LENGTH,
            "ref_image_size": "match",
            "native_no_upscale": True,
        },
        "nude_settings": "Same as the source Kazusa nude workflow: explicit adult fine-art nude, non-graphic, non-sexual, respectful framing.",
        "prompt": PROMPT,
    }


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    sync_seed(CHARACTER_SOURCE, COMFY_INPUT / CHARACTER_INPUT_NAME)
    sync_seed(SETTING_SOURCE, COMFY_INPUT / SETTING_INPUT_NAME)
    workflow = build_workflow()
    write_json(WORKFLOW_OUT, workflow)
    write_json(STORYBOARD_OUT, build_storyboard())
    print(f"wrote {WORKFLOW_OUT}")
    print(f"wrote {STORYBOARD_OUT}")
    print(f"synced {COMFY_INPUT / CHARACTER_INPUT_NAME}")
    print(f"synced {COMFY_INPUT / SETTING_INPUT_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
