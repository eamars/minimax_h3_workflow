"""Decode a media file with PyAV and emit deterministic technical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import av


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def as_float(value):
    return float(value) if value is not None else None


def inspect(path: Path) -> dict:
    with av.open(str(path)) as container:
        video_streams = [stream for stream in container.streams if stream.type == "video"]
        audio_streams = [stream for stream in container.streams if stream.type == "audio"]
        if not video_streams:
            raise AssertionError("QC_MEDIA_DECODE_FAILURE: no video stream")
        video = video_streams[0]
        frame_pts = []
        frame_times = []
        for frame in container.decode(video):
            frame_pts.append(frame.pts)
            frame_times.append(as_float(frame.time))
        if not frame_pts:
            raise AssertionError("QC_MEDIA_DECODE_FAILURE: no decoded frames")
        ordered = all(a is None or b is None or b > a for a, b in zip(frame_pts, frame_pts[1:]))
        rate = video.average_rate or video.base_rate or video.guessed_rate
        fps = as_float(rate)
        duration = as_float(video.duration * video.time_base) if video.duration is not None else None
        if duration is None and fps:
            duration = len(frame_pts) / fps

    audio = []
    for stream in audio_streams:
        audio.append({
            "index": stream.index,
            "sample_rate": getattr(stream.codec_context, "sample_rate", None),
            "channels": getattr(stream.codec_context, "channels", None),
            "duration_seconds": as_float(stream.duration * stream.time_base) if stream.duration is not None else None,
        })
    return {
        "path": path.as_posix(),
        "sha256": sha256(path),
        "decoder": {"name": "PyAV", "version": av.__version__},
        "video": {
            "width": video.width,
            "height": video.height,
            "fps": fps,
            "frame_count": len(frame_pts),
            "duration_seconds": duration,
            "timestamps_strictly_ordered": ordered,
            "first_timestamp_seconds": frame_times[0],
            "last_timestamp_seconds": frame_times[-1],
            "time_base": str(Fraction(video.time_base)),
        },
        "audio": audio,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-fps", type=float)
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--max-seconds", type=float, default=10.0)
    args = parser.parse_args()
    if not args.media.is_file():
        raise AssertionError("QC_INPUT_INVALID: media does not exist")
    result = inspect(args.media.resolve())
    video = result["video"]
    failures = []
    if not video["timestamps_strictly_ordered"]:
        failures.append("nonmonotonic_timestamps")
    if not video["duration_seconds"] or video["duration_seconds"] > args.max_seconds:
        failures.append("duration_out_of_range")
    if args.expected_fps is not None and abs(video["fps"] - args.expected_fps) > 1e-6:
        failures.append("fps_mismatch")
    if args.expected_width is not None and video["width"] != args.expected_width:
        failures.append("width_mismatch")
    if args.expected_height is not None and video["height"] != args.expected_height:
        failures.append("height_mismatch")
    result["technical_failures"] = failures
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            raise AssertionError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if failures:
        raise AssertionError("QC_MEDIA_SPEC_FAILURE: " + ", ".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
