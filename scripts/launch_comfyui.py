r"""Launch ComfyUI with a selected primary GPU, optionally hiding all others.

Python replacement for the retired ``scripts\launch_comfyui.ps1``. Behavior
is preserved:

  * ``--single-gpu`` passes only the selected primary GPU to ComfyUI, hiding
    every other GPU.
  * CUDA's device order can differ from ``nvidia-smi -L``, so hardcoding an
    index silently picks the wrong card. This launcher probes the real CUDA
    order and lists the primary GPU first so it becomes cuda:0.

Usage:
  python scripts\launch_comfyui.py --single-gpu                         # first/selected GPU only
  python scripts\launch_comfyui.py --primary-gpu "GPU name" --single-gpu
  python scripts\launch_comfyui.py -- --vram-headroom 1 --cpu-vae       # pass flags to ComfyUI
  python scripts\launch_comfyui.py --print-devices                      # show CUDA order only
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMFY = ROOT / "ComfyUI"
VENV_PY = COMFY / ".venv" / "Scripts" / "python.exe"


def probe_cuda(python: Path) -> list[str]:
    """Return CUDA device names in real CUDA order (cuda index == list index)."""
    code = (
        "import json, torch; "
        "print(json.dumps([torch.cuda.get_device_name(i) "
        "for i in range(torch.cuda.device_count())]))"
    )
    proc = subprocess.run(
        [str(python), "-c", code],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"CUDA probe failed: {proc.stderr.strip() or proc.stdout.strip()}")
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith("["):
            names = json.loads(line)
            if names:
                return names
    raise RuntimeError(f"No CUDA devices detected by {python}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Launch ComfyUI with a selected primary GPU")
    ap.add_argument("--port", type=int, default=8188)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument(
        "--primary-gpu",
        default=None,
        help="GPU name substring to select; defaults to the first detected device",
    )
    ap.add_argument(
        "--single-gpu",
        action="store_true",
        help="expose only the selected primary GPU to ComfyUI",
    )
    ap.add_argument("--print-devices", action="store_true")
    ap.add_argument("extra_args", nargs=argparse.REMAINDER, help="extra args passed to ComfyUI main.py")
    args = ap.parse_args()

    python = VENV_PY if VENV_PY.exists() else Path(shutil.which("python") or sys.executable)
    if not python.exists():
        raise SystemExit(
            f"venv python not found at {VENV_PY} - run scripts\\setup_comfyui.ps1 first"
        )

    names = probe_cuda(python)
    if args.primary_gpu:
        primary_idx = next(
            (i for i, name in enumerate(names) if args.primary_gpu.lower() in name.lower()), -1
        )
        if primary_idx < 0:
            raise SystemExit(
                f"Primary GPU '{args.primary_gpu}' not found among CUDA devices: {', '.join(names)}"
            )
    else:
        primary_idx = 0
    primary_name = names[primary_idx]

    # Order the visible list with the primary first -> it becomes cuda:0.
    # In single-GPU mode, do not expose any other card to ComfyUI.
    if args.single_gpu:
        cuda_list = str(primary_idx)
    else:
        ordered = [primary_idx] + [i for i in range(len(names)) if i != primary_idx]
        cuda_list = ",".join(str(i) for i in ordered)

    if args.print_devices:
        for i, name in enumerate(names):
            print(f"{i} -> {name}")
        print(f"launch list: {cuda_list}")
        return 0

    # argparse.REMAINDER preserves the conventional `--` delimiter. It is a
    # launcher-only delimiter and must not be forwarded to ComfyUI itself.
    extra_args = list(args.extra_args)
    if extra_args and extra_args[0] == "--":
        extra_args = extra_args[1:]

    print(f"CUDA devices: {', '.join(names)}")
    visibility = "selected GPU only" if args.single_gpu else "all detected GPUs"
    print(
        f"Primary: {primary_name} (CUDA index {primary_idx}; {visibility}) "
        f"-> --cuda-device {cuda_list}"
    )
    cmd = [
        str(python),
        str(COMFY / "main.py"),
        "--listen",
        args.host,
        "--port",
        str(args.port),
        "--cuda-device",
        cuda_list,
    ] + extra_args
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
