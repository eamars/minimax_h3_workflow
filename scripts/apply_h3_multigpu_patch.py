"""Install the strict MiniMax H3 VAE-device routing patch.

The ComfyUI checkout is intentionally ignored by this repository. This
startup patch keeps the local multi-GPU behavior reproducible: an explicit
``SelectVAEDevice gpu:N`` request must succeed, otherwise execution fails
instead of silently decoding on the loader/default device or CPU.
"""

from __future__ import annotations

import argparse
from pathlib import Path


MARKER = "refusing to fall back to the loader/default device"


def patch_file(path: Path) -> bool:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized = text.replace("\r\n", "\n")

    start = normalized.index("class SelectVAEDeviceNode")
    end = normalized.index("class MultiGPUOptionsNode", start)
    section = normalized[start:end]
    if MARKER in section:
        return False

    old = (
        "    When the selected device does not exist on the current machine\n"
        "    (e.g. a workflow built on a 2-GPU box opened on a 1-GPU box),\n"
        "    the node passes the VAE through unchanged and logs a message\n"
        "    instead of failing.\n"
    )
    new = (
        "    An explicit GPU request is fail-closed: if the selected device does not\n"
        "    exist or the VAE cannot be retargeted, the node raises instead of silently\n"
        "    falling back to the loader/default device (which may be CPU).\n"
    )
    if old not in section:
        raise RuntimeError(f"Could not find the VAE selector docstring in {path}")
    section = section.replace(old, new, 1)

    old = (
        "        if resolved is None and device not in (None, \"default\"):\n"
        "            logging.info(f\"Select VAE Device: requested device '{device}' not available, passing through unchanged.\")\n"
        "            return io.NodeOutput(vae)\n"
        "        if resolved is not None and resolved.type == \"cpu\":\n"
        "            logging.info(\"Select VAE Device: CPU is not a supported choice, passing through unchanged.\")\n"
        "            return io.NodeOutput(vae)\n"
    )
    new = (
        "        if resolved is None and device not in (None, \"default\"):\n"
        "            raise RuntimeError(\n"
        "                f\"Select VAE Device: requested device '{device}' is not available; \"\n"
        "                \"refusing to fall back to the loader/default device.\"\n"
        "            )\n"
        "        if resolved is not None and resolved.type == \"cpu\":\n"
        "            raise RuntimeError(\n"
        "                \"Select VAE Device: CPU is not a supported choice for an explicit VAE route.\"\n"
        "            )\n"
    )
    if old not in section:
        raise RuntimeError(f"Could not find the VAE selector device guard in {path}")
    section = section.replace(old, new, 1)

    old = (
        "        except RuntimeError as e:\n"
        "            logging.warning(f\"Select VAE Device: cannot retarget VAE, passing through unchanged. ({e})\")\n"
        "            return io.NodeOutput(vae)\n"
    )
    new = (
        "        except RuntimeError as e:\n"
        "            raise RuntimeError(\n"
        "                f\"Select VAE Device: cannot retarget VAE to {resolved}; \"\n"
        "                \"refusing to fall back to the loader/default device.\"\n"
        "            ) from e\n"
    )
    if old not in section:
        raise RuntimeError(f"Could not find the VAE selector retarget guard in {path}")
    section = section.replace(old, new, 1)

    old = (
        "        vae.first_stage_model = vae.patcher.model\n"
        "        vae.device = vae._select_base_device if resolved is None else resolved\n"
        "        return io.NodeOutput(vae)\n"
    )
    new = (
        "        vae.first_stage_model = vae.patcher.model\n"
        "        vae.device = vae._select_base_device if resolved is None else resolved\n"
        "        if resolved is not None:\n"
        "            if vae.device != resolved or vae.patcher.load_device != resolved:\n"
        "                raise RuntimeError(\n"
        "                    \"Select VAE Device: routing invariant failed; \"\n"
        "                    f\"requested {resolved}, wrapper={vae.device}, \"\n"
        "                    f\"patcher={vae.patcher.load_device}.\"\n"
        "                )\n"
        "            logging.info(\n"
        "                \"Select VAE Device: routed VAE compute to %s (offload=%s).\",\n"
        "                vae.patcher.load_device,\n"
        "                vae.patcher.offload_device,\n"
        "            )\n"
        "        return io.NodeOutput(vae)\n"
    )
    if old not in section:
        raise RuntimeError(f"Could not find the VAE selector postcondition in {path}")
    section = section.replace(old, new, 1)

    patched = normalized[:start] + section + normalized[end:]
    path.write_bytes(patched.replace("\n", newline).encode("utf-8"))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--comfy-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "ComfyUI",
    )
    args = parser.parse_args()
    target = args.comfy_root / "comfy_extras" / "nodes_multigpu.py"
    if not target.is_file():
        raise FileNotFoundError(f"ComfyUI multi-GPU source was not found at {target}")

    changed = patch_file(target)
    print(f"H3 strict VAE routing patch {'applied' if changed else 'already present'}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
