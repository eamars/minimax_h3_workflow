"""Build the Kazusa reference-to-video workflow from the GGUF R2V template.

Reads ``workflows/minimax_h3_ref2v-gguf.json`` and writes
``workflows/minimax_h3_ref2v-gguf_kazusa_sfw_uncensored.json`` with:

  * ref2va GGUF diffusion model + the workspace's uncensored Qwen3-VL encoder
  * the five Kazusa seeding images wired to ref_images.ref_image_0..4
  * 5 s duration (124 frames), 16:9 864x480, SFW prompt with Kazusa primary

Usage:
  python scripts/build_kazusa_workflow.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workflows" / "minimax_h3_ref2v-gguf.json"
DST = ROOT / "workflows" / "minimax_h3_ref2v-gguf_kazusa_sfw_uncensored.json"

REF2VA_GGUF = "minimax-h3-ref2va-Q8_CR.gguf"
UNCENSORED_ENCODER = "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors"
SEED_IMAGES = [f"kazusa_seed_{i}.png" for i in range(1, 6)]
WIDTH, HEIGHT, LENGTH = 864, 480, 124

PROMPT = (
    "<Picture 1> <Picture 2> <Picture 3> <Picture 4> <Picture 5> "
    "Kazusa, the cheerful anime schoolgirl shown in the reference pictures, is the main character. "
    "She stands in a bright school courtyard at golden hour, wearing her tidy blue school uniform, "
    "smiling warmly and waving hello with one hand. Her long dark hair sways gently in the breeze "
    "and cherry blossom petals drift past. Slow, steady tracking shot around her, soft warm "
    "sunlight, clean animation style matching the reference pictures. Wholesome, family-friendly, "
    "PG-rated, fully clothed, friendly mood, no text, no logos, no dialogue.\n\n"
    "Audio: gentle breeze, soft birdsong, and a light cheerful acoustic melody that fades out at "
    "the end. No vocals, no dialogue."
)


def main() -> int:
    wf = json.loads(SRC.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in wf["nodes"]}

    # 1) Models: ref2va GGUF loader (uncensored CLIP loader is already set in the template).
    nodes[136]["widgets_values"][0] = REF2VA_GGUF
    assert nodes[137]["widgets_values"][0] == UNCENSORED_ENCODER

    # 2) Resolution selector: 16:9 0.4 MP (~864x480), duration 5 s.
    nodes[115]["widgets_values"] = ["16:9 (Widescreen)", 0.4, 32]
    nodes[135]["widgets_values"] = [5]

    # 3) Reference node widgets: prompt, width, height, length, ref_image_size.
    nodes[145]["widgets_values"] = [PROMPT, WIDTH, HEIGHT, LENGTH, "match"]

    # 4) Drop video/audio reference nodes (image references only) and their links.
    dropped_nodes = {152, 153, 156}  # GetVideoComponents, LoadAudio, LoadVideo
    wf["nodes"] = [n for n in wf["nodes"] if n["id"] not in dropped_nodes]
    dropped_links = {279, 281, 282, 283}
    wf["links"] = [lk for lk in wf["links"] if lk[0] not in dropped_links]

    # 5) Rewire the five Kazusa seeding images into ref_images.ref_image_0..4.
    nodes = {n["id"]: n for n in wf["nodes"]}
    ref_node = nodes[145]
    image_node_0 = nodes[149]
    image_node_0["title"] = "Kazusa Reference 1"
    image_node_0["widgets_values"] = [SEED_IMAGES[0], "image"]

    # Rebuild the reference node input list: models, then image refs, then dims.
    ref_inputs = [i for i in ref_node["inputs"] if i["name"] in ("clip", "vae", "audio_vae")]
    original_ref0_link = next(
        i for i in ref_node["inputs"] if i["name"] == "ref_images.ref_image_0"
    )["link"]
    ref_image_inputs = []
    for idx in range(5):
        ref_image_inputs.append(
            {
                "label": f"ref_image_{idx}",
                "name": f"ref_images.ref_image_{idx}",
                "shape": 7,
                "type": "IMAGE",
                "link": None,
            }
        )
    ref_inputs += ref_image_inputs
    ref_image_inputs[0]["link"] = original_ref0_link
    for name in ("width", "height", "length"):
        ref_inputs.append(next(i for i in ref_node["inputs"] if i["name"] == name))
    ref_node["inputs"] = ref_inputs
    # The rebuilt input list shortened the array: width/height/length now sit at
    # slots 8/9/10, so the UI-format link records must follow (the API runner
    # maps by input name and is unaffected, but the ComfyUI UI reads slots).
    for link_id, new_slot in ((267, 8), (268, 9), (269, 10)):
        for lk in wf["links"]:
            if lk[0] == link_id:
                lk[4] = new_slot

    max_link = max(lk[0] for lk in wf["links"])
    next_id = max(nodes) + 1
    for idx in range(1, 5):
        nid = next_id + idx - 1
        new_node = json.loads(json.dumps(image_node_0))
        new_node["id"] = nid
        new_node["title"] = f"Kazusa Reference {idx + 1}"
        new_node["pos"] = [image_node_0["pos"][0], image_node_0["pos"][1] + idx * 360]
        new_node["widgets_values"] = [SEED_IMAGES[idx], "image"]
        for output in new_node["outputs"]:
            output["links"] = None if output["name"] == "MASK" else [max_link + idx]
        nodes[nid] = new_node
        # input slot: 0 clip, 1 vae, 2 audio_vae, 3..7 ref_image_0..4
        ref_image_inputs[idx]["link"] = max_link + idx
        wf["links"].append(
            [max_link + idx, nid, 0, 145, 3 + idx, "IMAGE"]
        )

    wf["nodes"] = list(nodes.values())
    wf["last_node_id"] = max(nodes)
    wf["last_link_id"] = max_link + 4
    wf["id"] = "kazusa-ref2v-gguf-sfw-uncensored"

    # 6) Distinct output prefix so the generated clip is easy to find.
    save = next(n for n in wf["nodes"] if n["type"] == "SaveVideo")
    save["widgets_values"] = ["video/MiniMax_H3_Kazusa", "auto", "auto"]

    DST.write_text(json.dumps(wf, indent=2), encoding="utf-8")
    print(f"wrote {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
