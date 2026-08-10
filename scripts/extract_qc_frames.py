"""Extract deterministic visual-evidence frames from a QC media file."""

from __future__ import annotations

import argparse
from pathlib import Path

import av


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--indices", nargs="+", type=int, default=[0, 36, 72, 108, 143])
    args = parser.parse_args()
    if not args.media.is_file():
        raise SystemExit(f"media does not exist: {args.media}")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty frame directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    wanted = set(args.indices)
    written = []
    with av.open(str(args.media)) as container:
        video = next(stream for stream in container.streams if stream.type == "video")
        for index, frame in enumerate(container.decode(video)):
            if index in wanted:
                path = args.output_dir / f"frame_{index:04d}.png"
                frame.to_image().save(path)
                written.append(path)
    missing = sorted(wanted - {int(path.stem.split("_")[-1]) for path in written})
    if missing:
        raise SystemExit(f"requested frames were not decoded: {missing}")
    print("\n".join(path.as_posix() for path in written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
