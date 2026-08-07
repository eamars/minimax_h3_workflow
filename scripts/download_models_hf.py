"""Download the quantized MiniMax H3 model stack into ComfyUI\\models.

Replaces the deprecated `huggingface-cli` calls: huggingface-hub >= 1.0
removed that CLI, so downloads go through the Python API (hf_hub_download)
which supports resumable downloads and progress bars.

Usage:
  python scripts/download_models_hf.py            # Q8_CR + U16G + encoder + VAEs
  python scripts/download_models_hf.py --only Q8_CR
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
COMFY = ROOT / "ComfyUI"
MODELS = COMFY / "models"

# Community encoder fine-tune: ethanfel "Ultra Heretic" H3 conditioning encoder
# (INT8 ConvRot, layers 0-49 + full vision tower in BF16). SHA-256 published on
# the model card: https://huggingface.co/ethanfel/Qwen3-VL-32B-Ultra-Heretic-H3-ComfyUI-INT8-ConvRot
ENCODER_SHA256 = "d84547412144b7c50a6ec77437a889b869d3ace88da77ef1775d3d2a4901c192"

# (repo, file-in-repo, target-dir-under-models)
FILES = {
    "Q8_CR": [
        ("molbal/MiniMax-H3-GGUF", "minimax_h3_fl2va_pruned_fp8_Q8_CR.gguf", "diffusion_models"),
    ],
    "U16G": [
        ("molbal/MiniMax-H3-GGUF", "minimax_h3_fl2va_pruned_fp8_U16G.gguf", "diffusion_models"),
    ],
    "R2V": [
        ("molbal/MiniMax-H3-GGUF", "minimax-h3-ref2va-Q8_CR.gguf", "diffusion_models"),
    ],
    "COMMON": [
        ("ethanfel/Qwen3-VL-32B-Ultra-Heretic-H3-ComfyUI-INT8-ConvRot", "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors", "text_encoders"),
        ("Comfy-Org/MiniMax-H3", "vae/minimax_h3_video_vae_fp16.safetensors", "vae"),
        ("Comfy-Org/MiniMax-H3", "vae/minimax_h3_audio_vae_fp32.safetensors", "vae"),
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["Q8_CR", "U16G", "R2V"], default=None)
    ap.add_argument("--comfy-dir", type=Path, default=COMFY)
    args = ap.parse_args()

    models_dir = args.comfy_dir / "models"
    entries = []
    if args.only is None:
        entries += FILES["Q8_CR"] + FILES["U16G"]
    elif args.only == "R2V":
        entries += FILES["R2V"]
    else:
        entries += FILES[args.only]
    if args.only != "R2V":
        entries += FILES["COMMON"]

    failures = 0
    for repo, filename, subdir in entries:
        target = models_dir / subdir
        target.mkdir(parents=True, exist_ok=True)
        print(f"\n[dl] {repo} :: {filename} -> {target}")
        try:
            out = hf_hub_download(repo_id=repo, filename=filename, local_dir=str(target))
        except Exception as exc:
            print(f"[FAIL] {filename}: {exc}")
            failures += 1
            continue
        size_gb = Path(out).stat().st_size / (1024**3)
        print(f"[ok]  {Path(out).name}  {size_gb:.2f} GB")
        if filename == "qwen3vl_32b_h3_ultra_uncensored_heretic_int8_convrot.safetensors":
            import hashlib
            digest = hashlib.sha256()
            with open(out, "rb") as fh:
                for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != ENCODER_SHA256:
                print("[FAIL] encoder SHA-256 mismatch - do not use this file")
                failures += 1
                continue
            print("[ok]  encoder SHA-256 verified")

    if failures:
        print(f"\n{failures} download(s) failed")
        return 1
    print("\nAll downloads complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
