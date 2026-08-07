"""Build the two-shot Kazusa bath practice workflow from the ref2v template.

The graph deliberately keeps MiniMax H3's expensive generation canvas at the
safe 864x480 / 24fps setting from the source workflow.  It then concatenates
two exact five-second clips and performs the final 1920x1080 resize on CPU-side
intermediate tensors.  Scene 2 receives Scene 1's frame 119 as its first
keyframe, so the connection is temporal rather than a visual cross-fade.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "workflows" / "minimax_h3_ref2v-gguf_kazusa_nude_10s.json"
OUTPUT = ROOT / "workflows" / "minimax_h3_ref2v-gguf_kazusa_bath_2scene_1080p_4090.json"
MANIFEST = ROOT / "storyboards" / "kazusa_bath_2scene_1080p_4090.json"

FPS = 24
SCENE_SECONDS = 5.0
SCENE_FRAMES = int(FPS * SCENE_SECONDS)
MODEL_FRAMES = 124  # MiniMax H3's 17k+5 frame grid for a five-second request.
WIDTH = 864
HEIGHT = 480
FINAL_WIDTH = 1920
FINAL_HEIGHT = 1080

CLIP_NAME = "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors"
REF2VA_MODEL = "minimax-h3-ref2va-Q8_CR.gguf"
FL2VA_MODEL = "minimax_h3_fl2va_pruned_fp8_U16G.gguf"


SCENE_1_PROMPT = """<Picture 1> <Picture 2> <Picture 3> <Picture 4> <Picture 5>

CONTINUITY LOCK: Kazusa is a clearly adult woman in her mid-twenties, the same person shown in all five reference pictures. Preserve her facial identity, short dark damp hair, natural proportions, skin tone, and calm adult presence. Do not make her look younger.

WORLD LOCK: a single warm, steamy Japanese-inspired bathhouse at dusk; the same dark teal glazed tile, pale stone soaking pool, cedar trim, brass lantern, low amber practical light, wet floor reflections, drifting steam, and soft blue dusk visible through the high window. Keep the architecture, prop placement, lighting direction, color palette, lens, and camera axis fixed for the next shot.

STYLE LOCK: cinematic naturalism, elegant fine-art nude study, explicit adult nudity but non-graphic and non-sexual, respectful composition, realistic water and steam, soft film grain, restrained contrast, no text and no logos. Intimate atmosphere comes from light, steam, breath, and stillness rather than sexual activity.

SCENE 1 / 0-5 seconds: Kazusa is already seated in the stone bath, three-quarter rear medium shot, shoulders and upper back above the water while steam and the pool edge naturally obscure intimate areas. She lowers her shoulders into the hot water, exhales, and rests one hand on the stone rim. A small ripple travels across the water as the steam curls past the lantern.

CAMERA: locked camera axis and framing, gentle five-percent push-in only, no cut, no orbit, no lens change, stable horizon. Keep the bathhouse background legible behind the steam.

TIMELINE: 0-2s settle into the water; 2-4s slow exhale and hand settling on the rim; 4-5s hold a quiet three-quarter rear pose with a slight turn of the head toward screen-left.

EXIT FRAME: at exactly 5 seconds, hold the same seated pose, water level, head angle, lantern position, steam density, and camera framing for the next shot to continue from this frame.

AUDIO: continuous bathhouse room tone, soft steam hiss, gentle hot-water trickle and droplets, subtle tiled-room echo, quiet natural breathing; no dialogue, no vocals, no music."""


SCENE_2_PROMPT = """CONTINUITY HANDOFF: the supplied first frame is the exact final handoff frame from Scene 1. Begin on that same adult Kazusa, same seated pose, same bathhouse pixels, same water level, same lantern, same steam, same camera axis and lens. Do not reset the composition, wardrobe state, anatomy, age, lighting, or background.

CHARACTER LOCK: Kazusa is a clearly adult woman in her mid-twenties with the same face, short dark damp hair, natural proportions, skin tone, and calm adult presence. Preserve identity frame-to-frame; do not make her look younger.

WORLD LOCK: continue the same warm, steamy Japanese-inspired bathhouse at dusk with dark teal glazed tile, pale stone soaking pool, cedar trim, brass lantern, low amber practical light, wet floor reflections, drifting steam, and soft blue dusk through the high window. No new room, props, architecture, or lighting direction.

STYLE LOCK: cinematic naturalism, elegant fine-art nude study, explicit adult nudity but non-graphic and non-sexual, respectful composition, realistic water and steam, soft film grain, restrained contrast, no text and no logos. Keep the mood quiet and observational rather than sexual.

SCENE 2 / 5-10 seconds: continue without a cut. Kazusa slowly turns her head a few degrees toward the camera, lifts her wet hand to brush a clear path through condensation on the nearby tile, then lets the hand return to the stone rim. Steam briefly reveals and hides the same shoulder and back contours while small ripples carry the motion through the bath.

CAMERA: identical camera axis, focal length, framing, height, and gentle five-percent push-in established in Scene 1; no jump, no orbit, no reframing. Preserve the background geometry and lantern placement.

TIMELINE: 5-7s slow head turn and breath; 7-9s hand clears condensation and steam shifts; 9-10s settle into a still adult portrait pose that could continue into another shot.

AUDIO: continue the exact Scene 1 atmosphere with no restart: same steam hiss, water trickle, tiled-room echo, quiet breathing, and soft ripples; no dialogue, no vocals, no music."""


OFFLOAD_NOTE = """## Two-scene H3 storyboard practice

**Output:** 2 connected scenes × 5.0 seconds = 240 frames at 24 fps, final 1920×1080 MP4.

**Generation canvas:** both H3 passes run at 864×480. The final `ImageScale` node performs the 1920×1080 resize after the two scene batches are joined, which avoids the memory cost of native 1080p H3 sampling on a 24 GB RTX 4090.

**Transition 1 — visual:** Scene 1 frame 119 is extracted as a one-frame handoff and fed to Scene 2's `first_frame` input. Scene 2's first output frame is removed during assembly, preventing a duplicate frame while preserving the exact five-second boundary.

**Transition 2 — audio:** each generated soundtrack is trimmed to 5.0 seconds and joined with `AudioConcat` in `after` mode. This keeps the two sound beds contiguous instead of restarting an untrimmed 5.1667-second H3 segment.

**RAM/offload guards:** the shared text encoder uses `CLIPLoaderGGUFDynamicVRAM`; `H3FreeTextEncoder` evicts it after each prompt is encoded; Scene 1 uses the ref2va Q8 model and Scene 2 uses the smaller local fl2va U16G model. Run `scripts\\launch_h3_4090_offload.ps1`, which applies `--disable-smart-memory --cpu-vae --fp32-vae --vram-headroom 1 --reserve-vram 0 --async-offload 4`. `--fp32-vae` is required here because the MiniMax video VAE's CPU linear layers reject float32 activations with fp16 weights.

The prompt is adult and non-graphic: it permits explicit adult nudity as a fine-art bath study and excludes sexual activity."""


def _port(name: str, type_name: str, link: int | None = None, shape: int | None = None) -> dict:
    value = {"name": name, "type": type_name, "link": link}
    if shape is not None:
        value["shape"] = shape
    return value


def _node(
    node_id: int,
    type_name: str,
    title: str,
    pos: tuple[float, float],
    size: tuple[float, float],
    inputs: list[dict],
    outputs: list[dict],
    widgets: list | None = None,
    order: int = 0,
    properties: dict | None = None,
) -> dict:
    return {
        "id": node_id,
        "type": type_name,
        "pos": list(pos),
        "size": list(size),
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "title": title,
        "properties": properties or {"Node name for S&R": type_name},
        "widgets_values": [] if widgets is None else widgets,
    }


def _output(name: str, type_name: str, links: list[int] | None = None) -> dict:
    return {"name": name, "type": type_name, "links": links or []}


def _node_map(workflow: dict) -> dict[int, dict]:
    return {int(item["id"]): item for item in workflow["nodes"]}


def _remove_link(workflow: dict, link_id: int) -> None:
    workflow["links"] = [link for link in workflow["links"] if int(link[0]) != link_id]
    for item in workflow["nodes"]:
        for port in item.get("inputs", []):
            if port.get("link") == link_id:
                port["link"] = None
        for port in item.get("outputs", []):
            links = port.get("links")
            if isinstance(links, list):
                port["links"] = [value for value in links if value != link_id]


def _add_link(
    workflow: dict,
    nodes: dict[int, dict],
    link_id: int,
    source_id: int,
    source_slot: int,
    target_id: int,
    target_slot: int,
    type_name: str,
) -> None:
    target_inputs = nodes[target_id].setdefault("inputs", [])
    target_inputs[target_slot]["link"] = link_id
    source_outputs = nodes[source_id].setdefault("outputs", [])
    links = source_outputs[source_slot].get("links")
    if not isinstance(links, list):
        links = []
        source_outputs[source_slot]["links"] = links
    links.append(link_id)
    workflow["links"].append([link_id, source_id, source_slot, target_id, target_slot, type_name])


def _add_node(workflow: dict, item: dict) -> None:
    workflow["nodes"].append(item)


def build_workflow() -> dict:
    with SOURCE.open("r", encoding="utf-8") as handle:
        workflow = json.load(handle)
    workflow = copy.deepcopy(workflow)
    nodes = _node_map(workflow)

    # Keep the source's safe generation canvas, but switch the shared text
    # encoder to the dynamic GGUF loader. The stock CLIP loader exposes a
    # `device` widget that this custom dynamic loader does not have.
    nodes[135]["widgets_values"] = [SCENE_SECONDS]
    nodes[136]["title"] = "Scene 1 DiT — ref2va Q8 / Dynamic VRAM"
    nodes[137]["type"] = "CLIPLoaderGGUFDynamicVRAM"
    nodes[137]["title"] = "Shared Qwen3-VL — Dynamic VRAM"
    nodes[137]["properties"] = {"Node name for S&R": "CLIPLoaderGGUFDynamicVRAM"}
    nodes[137]["widgets_values"] = [CLIP_NAME, "minimax"]
    nodes[145]["title"] = "Scene 1 — Reference-to-Video / 5s"
    nodes[145]["widgets_values"] = [SCENE_1_PROMPT, WIDTH, HEIGHT, MODEL_FRAMES, "match"]
    nodes[132]["title"] = "Scene 1 Preview — 5.0s"
    nodes[92]["title"] = "Final Output — 1080p / 10.0s"
    nodes[92]["widgets_values"] = ["video/MiniMax_H3_Kazusa_Bath_2Scene_1080p_4090", "auto", "auto"]

    # Replace links that formerly sent the untrimmed single scene directly to
    # CreateVideo and the old conditioning directly to the guider.
    for link_id in (240, 241, 243, 266):
        _remove_link(workflow, link_id)

    _add_node(
        workflow,
        _node(
            160,
            "H3ConditionStrength",
            "Scene 1 Anchor Strength",
            (760, 4630),
            (330, 150),
            [_port("conditioning", "CONDITIONING")],
            [_output("CONDITIONING", "CONDITIONING")],
            [1.0, 1.0],
            19,
        ),
    )
    _add_node(
        workflow,
        _node(
            161,
            "H3FreeTextEncoder",
            "Scene 1 — Evict Text Encoder",
            (1120, 4630),
            (340, 100),
            [_port("conditioning", "CONDITIONING"), _port("clip", "CLIP")],
            [_output("CONDITIONING", "CONDITIONING")],
            [],
            20,
        ),
    )
    _add_node(
        workflow,
        _node(
            162,
            "ImageFromBatch",
            "Scene 1 Frames 0–119 (5.0s)",
            (1820, 4620),
            (260, 120),
            [_port("image", "IMAGE")],
            [_output("IMAGE", "IMAGE")],
            [0, SCENE_FRAMES],
            25,
        ),
    )
    _add_node(
        workflow,
        _node(
            163,
            "ImageFromBatch",
            "Transition 1 — Scene 1 Frame 119",
            (1820, 4770),
            (300, 120),
            [_port("image", "IMAGE")],
            [_output("IMAGE", "IMAGE")],
            [SCENE_FRAMES - 1, 1],
            26,
        ),
    )
    _add_node(
        workflow,
        _node(
            164,
            "TrimAudioDuration",
            "Scene 1 Audio — 5.0s",
            (1820, 4920),
            (270, 130),
            [_port("audio", "AUDIO", shape=7)],
            [_output("AUDIO", "AUDIO")],
            [0.0, SCENE_SECONDS],
            27,
        ),
    )

    _add_node(
        workflow,
        _node(
            165,
            "UnetLoaderGGUFDynamicVRAM",
            "Scene 2 DiT — fl2va U16G / Dynamic VRAM",
            (2600, 4620),
            (650, 90),
            [],
            [_output("MODEL", "MODEL")],
            [FL2VA_MODEL],
            28,
        ),
    )
    _add_node(
        workflow,
        _node(
            166,
            "MiniMaxH3ImageToVideo",
            "Scene 2 — First-frame continuation / 5s",
            (2600, 4780),
            (470, 360),
            [
                _port("clip", "CLIP"),
                _port("vae", "VAE"),
                _port("width", "INT"),
                _port("height", "INT"),
                _port("length", "INT"),
                _port("first_frame", "IMAGE", shape=7),
                _port("last_frame", "IMAGE", shape=7),
            ],
            [_output("positive", "CONDITIONING"), _output("LATENT", "LATENT")],
            [SCENE_2_PROMPT, WIDTH, HEIGHT, MODEL_FRAMES],
            29,
        ),
    )
    _add_node(
        workflow,
        _node(
            167,
            "H3ConditionStrength",
            "Scene 2 Keyframe Strength",
            (3140, 4780),
            (330, 150),
            [_port("conditioning", "CONDITIONING")],
            [_output("CONDITIONING", "CONDITIONING")],
            [1.0, 1.0],
            30,
        ),
    )
    _add_node(
        workflow,
        _node(
            168,
            "H3FreeTextEncoder",
            "Scene 2 — Evict Text Encoder",
            (3500, 4780),
            (340, 100),
            [_port("conditioning", "CONDITIONING"), _port("clip", "CLIP")],
            [_output("CONDITIONING", "CONDITIONING")],
            [],
            31,
        ),
    )
    _add_node(
        workflow,
        _node(
            169,
            "BasicGuider",
            "Scene 2 Guider",
            (3900, 4780),
            (360, 70),
            [_port("model", "MODEL"), _port("conditioning", "CONDITIONING")],
            [_output("GUIDER", "GUIDER")],
            [],
            32,
        ),
    )
    _add_node(
        workflow,
        _node(
            170,
            "BasicScheduler",
            "Scene 2 Scheduler",
            (3900, 4930),
            (370, 130),
            [_port("model", "MODEL")],
            [_output("SIGMAS", "SIGMAS")],
            ["simple", 20, 1],
            33,
        ),
    )
    _add_node(
        workflow,
        _node(
            171,
            "RandomNoise",
            "Scene 2 Seed",
            (3900, 5130),
            (360, 90),
            [],
            [_output("NOISE", "NOISE")],
            [258027117257534, "fixed"],
            34,
        ),
    )
    _add_node(
        workflow,
        _node(
            172,
            "SamplerCustomAdvanced",
            "Scene 2 Sampler",
            (4320, 4780),
            (240, 330),
            [
                _port("noise", "NOISE"),
                _port("guider", "GUIDER"),
                _port("sampler", "SAMPLER"),
                _port("sigmas", "SIGMAS"),
                _port("latent_image", "LATENT"),
            ],
            [_output("output", "LATENT"), _output("denoised_output", "LATENT")],
            [],
            35,
        ),
    )
    _add_node(
        workflow,
        _node(
            173,
            "VAEDecode",
            "Scene 2 Video Decode",
            (4620, 4780),
            (230, 60),
            [_port("samples", "LATENT"), _port("vae", "VAE")],
            [_output("IMAGE", "IMAGE")],
            [],
            36,
        ),
    )
    _add_node(
        workflow,
        _node(
            174,
            "VAEDecodeAudio",
            "Scene 2 Audio Decode",
            (4620, 4900),
            (230, 60),
            [_port("samples", "LATENT"), _port("vae", "VAE")],
            [_output("AUDIO", "AUDIO")],
            [],
            37,
        ),
    )
    _add_node(
        workflow,
        _node(
            175,
            "ImageFromBatch",
            "Scene 2 Frames 1–120 (skip duplicate handoff)",
            (4940, 4780),
            (330, 120),
            [_port("image", "IMAGE")],
            [_output("IMAGE", "IMAGE")],
            [1, SCENE_FRAMES],
            38,
        ),
    )
    _add_node(
        workflow,
        _node(
            176,
            "TrimAudioDuration",
            "Scene 2 Audio — 5.0s",
            (4940, 4930),
            (270, 130),
            [_port("audio", "AUDIO", shape=7)],
            [_output("AUDIO", "AUDIO")],
            [0.0, SCENE_SECONDS],
            39,
        ),
    )
    _add_node(
        workflow,
        _node(
            177,
            "CreateVideo",
            "Scene 2 Preview — 5.0s",
            (5320, 4780),
            (280, 110),
            [_port("images", "IMAGE"), _port("audio", "AUDIO", shape=7)],
            [_output("VIDEO", "VIDEO")],
            [FPS, 8],
            40,
        ),
    )
    _add_node(
        workflow,
        _node(
            178,
            "SaveVideo",
            "Scene 2 Preview Output",
            (5660, 4780),
            (420, 160),
            [_port("video", "VIDEO")],
            [_output("video", "VIDEO")],
            ["video/MiniMax_H3_Kazusa_Bath_Scene2_5s", "auto", "auto"],
            41,
            {},
        ),
    )
    _add_node(
        workflow,
        _node(
            179,
            "ImageBatch",
            "Transition 1 — Join the two 5s image batches",
            (5320, 5160),
            (300, 90),
            [_port("image1", "IMAGE"), _port("image2", "IMAGE")],
            [_output("IMAGE", "IMAGE")],
            [],
            42,
        ),
    )
    _add_node(
        workflow,
        _node(
            180,
            "ImageScale",
            "Final 1080p Resize (CPU intermediate)",
            (5680, 5160),
            (300, 150),
            [_port("image", "IMAGE")],
            [_output("IMAGE", "IMAGE")],
            ["lanczos", FINAL_WIDTH, FINAL_HEIGHT, "disabled"],
            43,
        ),
    )
    _add_node(
        workflow,
        _node(
            181,
            "AudioConcat",
            "Transition 2 — Append Scene 2 audio",
            (5320, 5360),
            (300, 100),
            [_port("audio1", "AUDIO", shape=7), _port("audio2", "AUDIO", shape=7)],
            [_output("AUDIO", "AUDIO")],
            ["after"],
            44,
        ),
    )
    _add_node(
        workflow,
        _node(
            182,
            "CreateVideo",
            "Final Video — 10.0s / 1920×1080",
            (6060, 5160),
            (300, 110),
            [_port("images", "IMAGE"), _port("audio", "AUDIO", shape=7)],
            [_output("VIDEO", "VIDEO")],
            [FPS, 8],
            45,
        ),
    )
    _add_node(
        workflow,
        _node(
            183,
            "SaveVideo",
            "Scene 1 Preview Output",
            (2180, 4620),
            (420, 160),
            [_port("video", "VIDEO")],
            [_output("video", "VIDEO")],
            ["video/MiniMax_H3_Kazusa_Bath_Scene1_5s", "auto", "auto"],
            46,
            {},
        ),
    )
    _add_node(
        workflow,
        {
            "id": 184,
            "type": "MarkdownNote",
            "pos": [2200, 5360],
            "size": [520, 820],
            "flags": {},
            "order": 47,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "title": "README: 4090 offload and continuity",
            "properties": {},
            "widgets_values": [OFFLOAD_NOTE],
            "color": "#222",
            "bgcolor": "#000",
        },
    )

    nodes = _node_map(workflow)
    _add_link(workflow, nodes, 282, 126, 0, 162, 0, "IMAGE")
    _add_link(workflow, nodes, 283, 126, 0, 163, 0, "IMAGE")
    _add_link(workflow, nodes, 284, 125, 0, 164, 0, "AUDIO")
    _add_link(workflow, nodes, 285, 145, 0, 160, 0, "CONDITIONING")
    _add_link(workflow, nodes, 286, 160, 0, 161, 0, "CONDITIONING")
    _add_link(workflow, nodes, 287, 137, 0, 161, 1, "CLIP")
    _add_link(workflow, nodes, 288, 161, 0, 130, 1, "CONDITIONING")

    _add_link(workflow, nodes, 289, 137, 0, 166, 0, "CLIP")
    _add_link(workflow, nodes, 290, 123, 0, 166, 1, "VAE")
    _add_link(workflow, nodes, 291, 115, 0, 166, 2, "INT")
    _add_link(workflow, nodes, 292, 115, 1, 166, 3, "INT")
    _add_link(workflow, nodes, 293, 134, 1, 166, 4, "INT")
    _add_link(workflow, nodes, 294, 163, 0, 166, 5, "IMAGE")
    _add_link(workflow, nodes, 295, 166, 0, 167, 0, "CONDITIONING")
    _add_link(workflow, nodes, 296, 167, 0, 168, 0, "CONDITIONING")
    _add_link(workflow, nodes, 297, 137, 0, 168, 1, "CLIP")
    _add_link(workflow, nodes, 298, 168, 0, 169, 1, "CONDITIONING")
    _add_link(workflow, nodes, 299, 165, 0, 169, 0, "MODEL")
    _add_link(workflow, nodes, 300, 165, 0, 170, 0, "MODEL")
    _add_link(workflow, nodes, 301, 166, 1, 172, 4, "LATENT")
    _add_link(workflow, nodes, 302, 171, 0, 172, 0, "NOISE")
    _add_link(workflow, nodes, 303, 127, 0, 172, 2, "SAMPLER")
    _add_link(workflow, nodes, 304, 170, 0, 172, 3, "SIGMAS")
    _add_link(workflow, nodes, 305, 172, 0, 173, 0, "LATENT")
    _add_link(workflow, nodes, 306, 123, 0, 173, 1, "VAE")
    _add_link(workflow, nodes, 307, 172, 0, 174, 0, "LATENT")
    _add_link(workflow, nodes, 308, 124, 0, 174, 1, "VAE")
    _add_link(workflow, nodes, 309, 173, 0, 175, 0, "IMAGE")
    _add_link(workflow, nodes, 310, 174, 0, 176, 0, "AUDIO")
    _add_link(workflow, nodes, 311, 175, 0, 177, 0, "IMAGE")
    _add_link(workflow, nodes, 312, 176, 0, 177, 1, "AUDIO")
    _add_link(workflow, nodes, 313, 177, 0, 178, 0, "VIDEO")

    _add_link(workflow, nodes, 314, 162, 0, 132, 0, "IMAGE")
    _add_link(workflow, nodes, 315, 164, 0, 132, 1, "AUDIO")
    _add_link(workflow, nodes, 316, 132, 0, 183, 0, "VIDEO")
    _add_link(workflow, nodes, 317, 162, 0, 179, 0, "IMAGE")
    _add_link(workflow, nodes, 318, 175, 0, 179, 1, "IMAGE")
    _add_link(workflow, nodes, 319, 179, 0, 180, 0, "IMAGE")
    _add_link(workflow, nodes, 320, 164, 0, 181, 0, "AUDIO")
    _add_link(workflow, nodes, 321, 176, 0, 181, 1, "AUDIO")
    _add_link(workflow, nodes, 322, 180, 0, 182, 0, "IMAGE")
    _add_link(workflow, nodes, 323, 181, 0, 182, 1, "AUDIO")
    _add_link(workflow, nodes, 324, 182, 0, 92, 0, "VIDEO")
    _add_link(workflow, nodes, 325, 169, 0, 172, 1, "GUIDER")

    workflow["last_node_id"] = 184
    workflow["last_link_id"] = 325
    workflow["extra"]["kazusa_bath_practice"] = {
        "source_workflow": SOURCE.name,
        "generation_canvas": [WIDTH, HEIGHT],
        "final_canvas": [FINAL_WIDTH, FINAL_HEIGHT],
        "fps": FPS,
        "scene_seconds": SCENE_SECONDS,
        "scene_model_frames": MODEL_FRAMES,
        "final_frames": SCENE_FRAMES * 2,
        "scene_2_handoff_source_frame": SCENE_FRAMES - 1,
        "scene_2_duplicate_frame_removed": True,
        "offload_nodes": ["UnetLoaderGGUFDynamicVRAM", "CLIPLoaderGGUFDynamicVRAM", "H3FreeTextEncoder"],
    }
    assert nodes[172]["inputs"][1]["link"] == 325, "Scene 2 sampler must receive the guider link"
    return workflow


def build_manifest() -> dict:
    return {
        "id": "kazusa_bath_2scene_1080p_4090",
        "source_workflow": "workflows/minimax_h3_ref2v-gguf_kazusa_nude_10s.json",
        "workflow": "workflows/minimax_h3_ref2v-gguf_kazusa_bath_2scene_1080p_4090.json",
        "subject": {"name": "Kazusa", "age": "clearly adult, mid-twenties", "content": "explicit adult nudity, non-graphic fine-art bath study"},
        "format": {"fps": FPS, "scene_seconds": SCENE_SECONDS, "scene_count": 2, "final_seconds": 10.0, "final_frames": SCENE_FRAMES * 2, "final_width": FINAL_WIDTH, "final_height": FINAL_HEIGHT},
        "generation": {"width": WIDTH, "height": HEIGHT, "model_frames_per_scene": MODEL_FRAMES, "ref2va_model": REF2VA_MODEL, "fl2va_model": FL2VA_MODEL, "text_encoder": CLIP_NAME, "sampler_steps": 20},
        "transitions": [
            {"id": "visual_keyframe_handoff", "from": "scene_1.frame_119", "to": "scene_2.first_frame", "assembly": "drop scene_2.frame_0 and append scene_2.frames_1_120"},
            {"id": "audio_continuity", "from": "scene_1.audio_0_5s", "to": "scene_2.audio_0_5s", "assembly": "AudioConcat(direction=after)"},
        ],
        "continuity_locks": ["same adult character identity", "same bathhouse geometry", "same camera axis and lens", "same lantern and dusk lighting", "same water level and steam direction"],
        "offload": {"launcher": "scripts/launch_h3_4090_offload.ps1", "clip_loader": "CLIPLoaderGGUFDynamicVRAM", "text_encoder_eviction": "H3FreeTextEncoder after each conditioning node", "vae_dtype": "fp32 on CPU", "recommended_args": ["--disable-smart-memory", "--cpu-vae", "--fp32-vae", "--vram-headroom", "1", "--reserve-vram", "0", "--async-offload", "4"]},
        "prompts": {"scene_1": SCENE_1_PROMPT, "scene_2": SCENE_2_PROMPT},
    }


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(build_workflow(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with MANIFEST.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(build_manifest(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
