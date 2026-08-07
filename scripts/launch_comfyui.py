r"""Launch ComfyUI with both GPUs visible, primary GPU first.

Python replacement for the retired ``scripts\launch_comfyui.ps1``. Behavior
is preserved:

  * ``--cuda-device <one id>`` hides every other GPU, so the machine would
    effectively run on a single card.
  * CUDA's device order can differ from ``nvidia-smi -L`` (on this machine
    cuda:0 = RTX 4090 and cuda:1 = RTX 5090 today), so hardcoding an index
    silently picks the wrong card. This launcher probes the real CUDA order
    and lists the primary GPU first so it becomes cuda:0 (the default).

Usage:
  python scripts\launch_comfyui.py                                        # 4090 primary, port 8188
  python scripts\launch_comfyui.py --port 8189 --primary-gpu "RTX 5090"   # 5090 primary
  python scripts\launch_comfyui.py --print-devices                       # show CUDA order only
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
    ap = argparse.ArgumentParser(description="Launch ComfyUI (both GPUs visible, primary first)")
    ap.add_argument("--port", type=int, default=8188)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--primary-gpu", default="RTX 4090")
    ap.add_argument("--print-devices", action="store_true")
    ap.add_argument("extra_args", nargs=argparse.REMAINDER, help="extra args passed to ComfyUI main.py")
    args = ap.parse_args()

    python = VENV_PY if VENV_PY.exists() else Path(shutil.which("python") or sys.executable)
    if not python.exists():
        raise SystemExit(
            f"venv python not found at {VENV_PY} - run scripts\\setup_comfyui.ps1 first"
        )

    names = probe_cuda(python)
    primary_idx = next(
        (i for i, name in enumerate(names) if args.primary_gpu.lower() in name.lower()), -1
    )
    if primary_idx < 0:
        raise SystemExit(
            f"Primary GPU '{args.primary_gpu}' not found among CUDA devices: {', '.join(names)}"
        )

    # Order the visible list with the primary first -> it becomes cuda:0 (default).
    ordered = [primary_idx] + [i for i in range(len(names)) if i != primary_idx]
    cuda_list = ",".join(str(i) for i in ordered)

    if args.print_devices:
        for i, name in enumerate(names):
            print(f"{i} -> {name}")
        print(f"launch list: {cuda_list}")
        return 0

    print(f"CUDA devices: {', '.join(names)}")
    print(f"Primary: {args.primary_gpu} (CUDA index {primary_idx}) -> --cuda-device {cuda_list}")
    cmd = [
        str(python),
        str(COMFY / "main.py"),
        "--listen",
        args.host,
        "--port",
        str(args.port),
        "--cuda-device",
        cuda_list,
    ] + args.extra_args
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
