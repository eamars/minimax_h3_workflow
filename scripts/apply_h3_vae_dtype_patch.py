"""Ensure the local ComfyUI MiniMax H3 CPU-VAE dtype fix is installed.

The ComfyUI checkout is intentionally ignored by this repository because it
contains its own code, virtual environment, custom nodes, and model assets.
This small startup patch keeps the required local compatibility change
reproducible without vendoring that checkout.
"""

from __future__ import annotations

import argparse
from pathlib import Path


PATCH_SNIPPET = '''        # aimdo's lazy state-dict loader can assign checkpoint tensors after the
        # initial dtype conversion above.  MiniMax H3's CPU VAE uses regular
        # Linear layers, so fp16 checkpoint weights would otherwise be paired
        # with the fp32 activations requested by --fp32-vae.
        if self.device.type == "cpu" and self.vae_dtype == torch.float32:
            self.first_stage_model.to(device=self.device, dtype=self.vae_dtype)
            model_management.archive_model_dtypes(self.first_stage_model)
'''


def patch_file(path: Path) -> bool:
    data = path.read_bytes()
    if b'if self.device.type == "cpu" and self.vae_dtype == torch.float32:' in data:
        return False

    newline = b"\r\n" if b"\r\n" in data else b"\n"
    marker = b"        logging.debug(\"Leftover VAE keys {}\".format(u))" + newline
    needle = marker + newline + b"        logging.info"
    replacement = marker + newline + PATCH_SNIPPET.replace("\n", newline.decode()).encode() + b"        logging.info"
    if needle not in data:
        raise RuntimeError(f"Could not find the VAE load boundary in {path}")

    path.write_bytes(data.replace(needle, replacement, 1))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--comfy-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ComfyUI",
    )
    args = parser.parse_args()
    target = args.comfy_root / "comfy" / "sd.py"
    if not target.is_file():
        raise FileNotFoundError(f"ComfyUI VAE source was not found at {target}")

    changed = patch_file(target)
    print(f"H3 CPU-VAE dtype patch {'applied' if changed else 'already present'}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
