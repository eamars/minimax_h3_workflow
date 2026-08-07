"""Convert a ComfyUI UI-format workflow JSON to the /prompt API format and run it.

Workspace-local helper for the MiniMax H3 demo:
  1. Reads a UI-format workflow export (*.json with "nodes"/"links").
  2. Converts it to the API prompt format (node id -> class_type/inputs),
     resolving widget parameter names from the live server's /object_info.
  3. Applies optional overrides (prompt text, resolution, seconds, steps, seed).
  4. POSTs to ComfyUI /prompt, polls /history, and reports output files.

Usage:
  python scripts/comfy_api_runner.py --workflow workflows/minimax_h3_t2v-gguf.json \
      --port 8188 --prompt "..." --width 864 --height 480 --seconds 5 --steps 20
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# Fallback widget-name order used only if /object_info is unavailable.
FALLBACK_WIDGET_ORDER: dict[str, list[str]] = {
    "BasicScheduler": ["scheduler", "steps", "denoise"],
    "BasicGuider": ["cfg"],
    "CLIPLoader": ["clip_name", "type", "device"],
    "ComfyMathExpression": ["expression"],
    "CreateVideo": ["fps", "quality"],
    "KSamplerSelect": ["sampler_name"],
    "LoadAudio": ["audio"],
    "LoadImage": ["image"],
    "LoadVideo": ["video", "frame_load_cap"],
    "MiniMaxH3ImageToVideo": ["prompt", "width", "height", "length"],
    "MiniMaxH3ReferenceToVideo": ["prompt", "width", "height", "length", "ref_image_size"],
    "PrimitiveFloat": ["float"],
    "RandomNoise": ["noise_seed", "noise_mode"],
    "ResolutionSelector": ["aspect", "megapixels", "multiple"],
    "SaveVideo": ["filename_prefix", "format", "quality"],
    "UnetLoaderGGUFDynamicVRAM": ["unet_name", "dynamic", "keep_in_ram"],
    "UNETLoader": ["unet_name", "weight_dtype"],
    "VAEDecode": [],
    "VAEDecodeAudio": [],
    "VAELoader": ["vae_name"],
}

# Inputs that carry tensor data (or model handles) must never receive a stale
# scalar widget value. File-picker widgets for these inputs are strings; if the
# workflow JSON was saved against a different widget order, leftover ints/floats
# (e.g. an old resolution) would otherwise be injected into inputs like
# first_frame/last_frame, crashing the node with "'int' object is not
# subscriptable".
NON_SCALAR_INPUT_TYPES = {
    "AUDIO", "CLIP", "CLIP_VISION", "CONDITIONING", "CONTROL_NET", "GUIDER",
    "IMAGE", "LATENT", "MASK", "MODEL", "NOISE", "SAMPLER", "SIGMAS", "VAE",
    "VIDEO",
}


def http_json(url: str, payload: dict | None = None, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def get_widget_orders(base: str, node_types: set[str]) -> dict[str, list[str]]:
    """Fetch widget input order per node class from the live server."""
    try:
        info = http_json(base + "/object_info", timeout=60)
    except Exception as exc:
        print(f"WARNING: /object_info unavailable ({exc}); using fallback names")
        return {}
    orders: dict[str, list[str]] = {}
    for ntype in node_types:
        cls = info.get(ntype)
        if cls is None:
            continue
        names: list[str] = []
        for section in ("required", "optional"):
            for name, spec in cls.get("input", {}).get(section, {}).items():
                # Widget inputs are either [default/type, options-dict] (older
                # ComfyUI) or [[...option list...]] (ComfyUI 0.30+ model pickers).
                if (
                    isinstance(spec, list)
                    and len(spec) >= 1
                    and (
                        isinstance(spec[0], list)
                        or (len(spec) >= 2 and isinstance(spec[1], dict))
                    )
                    and not (
                        isinstance(spec[0], str)
                        and (
                            spec[0] in NON_SCALAR_INPUT_TYPES
                            or spec[0] == "COMFY_AUTOGROW_V3"
                        )
                    )
                ):
                    names.append(name)
        orders[ntype] = names
    return orders


def convert_workflow(workflow: dict, widget_orders: dict[str, list[str]]) -> dict:
    """Convert a UI-format workflow graph to the API prompt format."""
    prompt: dict[str, dict] = {}
    link_sources: dict[int, tuple[int, int]] = {}
    for link in workflow.get("links", []):
        # link = [id, source_node, source_slot, target_node, target_slot, type]
        link_sources[link[0]] = (link[1], link[2])

    for node in workflow["nodes"]:
        nid = str(node["id"])
        ntype = node["type"]
        if ntype.startswith("MarkdownNote") or ntype in ("Note", "PrimitiveNode"):
            continue
        prompt[nid] = {"class_type": ntype, "inputs": {}}

        node_inputs = {i["name"]: i for i in node.get("inputs", [])}

        # 1) Linked inputs become connections.
        for name, inp in node_inputs.items():
            if inp.get("link") is not None:
                src_id, src_slot = link_sources[inp["link"]]
                prompt[nid]["inputs"][name] = [str(src_id), src_slot]

        # 2) Widget values align with the class widget order (server truth);
        #    converted-but-unlinked widgets keep their value in widgets_values.
        values = list(node.get("widgets_values", []))
        order = widget_orders.get(ntype) or FALLBACK_WIDGET_ORDER.get(ntype, [])
        vi = 0
        for name in order:
            inp = node_inputs.get(name)
            if inp is not None and inp.get("link") is not None:
                # Already set as a connection, but the widget still occupies a
                # slot in widgets_values when the JSON was saved with all
                # widgets expanded (e.g. MiniMaxH3ReferenceToVideo exports
                # prompt/width/height/length/ref_image_size even when the dims
                # are linked). Consume the slot so later unlinked widgets
                # (ref_image_size) align correctly.
                vi += 1
                continue
            if vi < len(values):
                value = values[vi]
                if isinstance(value, (int, float)) and inp is not None and inp.get("type") in NON_SCALAR_INPUT_TYPES:
                    continue  # stale scalar in a tensor-typed slot; do not consume
                prompt[nid]["inputs"][name] = value
                vi += 1
        # Any leftover values (e.g., widget removed from class) are ignored.
    return prompt


def apply_overrides(workflow: dict, prompt: dict, args) -> dict:
    for node in workflow["nodes"]:
        nid = str(node["id"])
        ntype = node["type"]
        if nid not in prompt:
            continue
        if ntype in ("MiniMaxH3ImageToVideo", "MiniMaxH3ReferenceToVideo"):
            if args.prompt:
                prompt[nid]["inputs"]["prompt"] = args.prompt
            if args.width and args.height:
                # Pin explicit resolution (replaces the ResolutionSelector link).
                prompt[nid]["inputs"]["width"] = args.width
                prompt[nid]["inputs"]["height"] = args.height
        elif ntype == "PrimitiveFloat" and args.seconds:
            prompt[nid]["inputs"]["float"] = args.seconds
        elif ntype == "BasicScheduler" and args.steps:
            prompt[nid]["inputs"]["steps"] = args.steps
        elif ntype == "RandomNoise" and args.seed is not None:
            prompt[nid]["inputs"]["noise_seed"] = args.seed
            prompt[nid]["inputs"]["noise_mode"] = "fixed"
    return prompt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", required=True, type=Path)
    ap.add_argument("--port", type=int, default=8188)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--prompt", default=None, help="Text prompt override")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--poll-interval", type=float, default=5.0)
    ap.add_argument("--max-wait", type=float, default=7200.0)
    ap.add_argument("--output-dir", type=Path, default=None)
    args = ap.parse_args()

    workflow = json.loads(args.workflow.read_text(encoding="utf-8"))
    base = f"http://{args.host}:{args.port}"
    node_types = {
        n["type"]
        for n in workflow["nodes"]
        if not n["type"].startswith("MarkdownNote")
        and n["type"] not in ("Note", "PrimitiveNode")
    }
    widget_orders = get_widget_orders(base, node_types)

    prompt_api = convert_workflow(workflow, widget_orders)
    prompt_api = apply_overrides(workflow, prompt_api, args)

    print(f"Submitting {len(prompt_api)} nodes to {base}/prompt ...")
    try:
        resp = http_json(base + "/prompt", {"prompt": prompt_api, "client_id": "codex-demo"})
    except urllib.error.HTTPError as e:
        print(f"ERROR: /prompt returned HTTP {e.code}")
        print(e.read().decode())
        return 1
    prompt_id = resp.get("prompt_id")
    if not prompt_id:
        print(f"ERROR: no prompt_id in response: {resp}")
        return 1
    print(f"prompt_id={prompt_id}")

    deadline = time.time() + args.max_wait
    entry = None
    while time.time() < deadline:
        time.sleep(args.poll_interval)
        try:
            hist = http_json(base + f"/history/{prompt_id}")
        except Exception as exc:  # server may still be starting
            print(f"  poll error (retrying): {exc}")
            continue
        if prompt_id in hist:
            entry = hist[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                print("ERROR: execution failed")
                for msg in status.get("messages", []):
                    print(" ", msg)
                return 1
            if status.get("completed") or status.get("status_str") == "success":
                break
    else:
        print(f"ERROR: timed out after {args.max_wait}s")
        return 1

    outputs = entry.get("outputs", {})
    files = []
    for node_id, out in outputs.items():
        for key, items in out.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "filename" in item:
                    files.append((node_id, key, item))

    print("\nOutputs:")
    for node_id, key, item in files:
        fname = item["filename"]
        sub = item.get("subfolder", "")
        print(f"  node {node_id} [{key}]: {sub}/{fname}  ({item.get('type', '')})")
        if args.output_dir:
            path = args.output_dir / sub / fname
            print(f"    abs: {path}  exists={path.exists()}")

    if not files:
        print("WARNING: no output files found in history")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
