#!/usr/bin/env python3
"""Audit a technical-only render/assembly path test.

This gate intentionally does not judge identity, environment fidelity, hands,
camera quality, or editorial taste.  It proves that the approved inputs,
render outputs, provenance, and non-deliverable technical draft agree without
silently treating a path test as QC or delivery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


FPS = 24
WIDTH = 1344
HEIGHT = 768
AUDIO_RATE = 32_000


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def inspect_media(path: Path) -> dict[str, object]:
    try:
        import av
    except ImportError as error:
        raise RuntimeError("PATH_TEST_PYAV_REQUIRED: run with the ComfyUI runtime Python") from error
    container = av.open(str(path))
    try:
        if not container.streams.video or not container.streams.audio:
            raise RuntimeError(f"MEDIA_STREAMS_MISSING: {path}")
        video = container.streams.video[0]
        audio = container.streams.audio[0]
        if video.average_rate != FPS:
            raise RuntimeError(f"MEDIA_FPS_INVALID: {path}: {video.average_rate}")
        if (video.width, video.height) != (WIDTH, HEIGHT):
            raise RuntimeError(f"MEDIA_DIMENSIONS_INVALID: {path}: {video.width}x{video.height}")
        video_frames = 0
        audio_samples = 0
        for packet in container.demux():
            if packet.stream.type == "video":
                video_frames += sum(1 for _ in packet.decode())
            elif packet.stream.type == "audio":
                audio_samples += sum(frame.samples for frame in packet.decode())
        if audio.sample_rate != AUDIO_RATE or audio.channels != 2:
            raise RuntimeError(f"MEDIA_AUDIO_SPEC_INVALID: {path}: {audio.channels}ch/{audio.sample_rate}Hz")
        return {
            "path": path.as_posix(),
            "video_frames": video_frames,
            "fps": str(video.average_rate),
            "duration_seconds": video_frames / FPS,
            "audio_samples": audio_samples,
            "audio_rate": audio.sample_rate,
            "audio_channels": audio.channels,
        }
    finally:
        container.close()


def validate(args: argparse.Namespace) -> dict[str, object]:
    project_root = args.project_root.resolve()
    run_dir = project_root / "orchestrator" / "runs" / args.run_id
    state_path = run_dir / "run-state.yaml"
    if not state_path.is_file():
        raise RuntimeError(f"PATH_TEST_STATE_MISSING: {state_path}")
    state = load(state_path)
    if state.get("lifecycle_mode") != "path-test":
        raise RuntimeError("PATH_TEST_MODE_REQUIRED")
    if state.get("status") != "PATH_TEST_SEGMENTS_READY":
        raise RuntimeError(f"PATH_TEST_STATUS_INVALID: {state.get('status')}")
    admitted = state.get("admitted_job_ids") or state.get("job_order") or []
    if not admitted:
        raise RuntimeError("PATH_TEST_NO_ADMITTED_JOBS")
    if state.get("failed_job_ids") or state.get("blocked_job_ids"):
        raise RuntimeError("PATH_TEST_NONTERMINAL_JOBS_PRESENT")

    reports = []
    intakes = []
    for job_id in admitted:
        job_state = state.get("jobs", {}).get(job_id, {})
        if job_state.get("state") != "COMPLETE":
            raise RuntimeError(f"PATH_TEST_JOB_NOT_COMPLETE: {job_id}")
        attempts = [item for item in job_state.get("attempts", []) if item.get("state") == "COMPLETE"]
        if len(attempts) != 1:
            raise RuntimeError(f"PATH_TEST_ATTEMPT_PROVENANCE_INVALID: {job_id}")
        report_path = Path(str(attempts[0].get("report_path", ""))).resolve()
        intake_path = Path(str(attempts[0].get("qc_intake_path", ""))).resolve()
        if not within(report_path, run_dir) or not within(intake_path, run_dir):
            raise RuntimeError(f"PATH_TEST_PROVENANCE_PATH_UNSAFE: {job_id}")
        report = load(report_path)
        intake = load(intake_path)
        if report.get("state") != "COMPLETE" or report.get("lifecycle_mode") != "path-test":
            raise RuntimeError(f"PATH_TEST_REPORT_INVALID: {job_id}")
        if report.get("quality_evaluation") != "not_performed_by_user_instruction":
            raise RuntimeError(f"PATH_TEST_QUALITY_GATE_NOT_TRUTHFUL: {job_id}")
        if intake.get("qc_status") != "technical_intake_only" or intake.get("quality_evaluation") != "not_performed_by_user_instruction":
            raise RuntimeError(f"PATH_TEST_INTAKE_INVALID: {job_id}")
        media_path = Path(str(report.get("effective_media", {}).get("path", ""))).resolve()
        if not within(media_path, run_dir) or not media_path.is_file():
            raise RuntimeError(f"PATH_TEST_MEDIA_MISSING: {job_id}")
        media_hash = sha256_file(media_path)
        if media_hash != report.get("effective_media", {}).get("sha256") or media_hash != intake.get("media", {}).get("sha256"):
            raise RuntimeError(f"PATH_TEST_MEDIA_HASH_MISMATCH: {job_id}")
        reports.append(report)
        intakes.append(intake)

    manifest_path = args.manifest.resolve()
    master_path = args.master.resolve()
    if not manifest_path.is_file() or not master_path.is_file():
        raise RuntimeError("PATH_TEST_MASTER_OR_MANIFEST_MISSING")
    manifest = load(manifest_path)
    if manifest.get("delivery_status") != "not_deliverable_without_QC":
        raise RuntimeError("PATH_TEST_DELIVERY_STATUS_INVALID")
    if manifest.get("lifecycle_mode") != "path-test":
        raise RuntimeError("PATH_TEST_MANIFEST_MODE_INVALID")
    if manifest.get("quality_evaluation") != "not_performed_by_user_instruction":
        raise RuntimeError("PATH_TEST_MANIFEST_QUALITY_INVALID")
    output = manifest.get("output", {})
    if output.get("path") != master_path.relative_to(project_root).as_posix():
        raise RuntimeError("PATH_TEST_MASTER_PATH_MISMATCH")
    if output.get("sha256") != sha256_file(master_path):
        raise RuntimeError("PATH_TEST_MASTER_HASH_MISMATCH")
    source_order = manifest.get("source_order") or []
    if len(source_order) != len(admitted):
        raise RuntimeError("PATH_TEST_SOURCE_COUNT_MISMATCH")
    expected_source_order = [
        Path(str(report["effective_media"]["path"])).resolve().relative_to(project_root).as_posix()
        for report in reports
    ]
    if source_order != expected_source_order:
        raise RuntimeError("PATH_TEST_SOURCE_ORDER_MISMATCH")
    for relative, expected_hash in (manifest.get("source_hashes") or {}).items():
        source = (project_root / relative).resolve()
        if not within(source, project_root) or not source.is_file() or sha256_file(source) != expected_hash:
            raise RuntimeError(f"PATH_TEST_SOURCE_HASH_MISMATCH: {relative}")

    media = inspect_media(master_path)
    expected_frames = sum(round(float(report["expected"]["duration_seconds"]) * FPS) for report in reports)
    expected_audio_samples = round(expected_frames * AUDIO_RATE / FPS)
    if media["video_frames"] != expected_frames:
        raise RuntimeError(f"PATH_TEST_MASTER_FRAME_COUNT_MISMATCH: expected {expected_frames}, got {media['video_frames']}")
    if media["audio_samples"] != expected_audio_samples:
        raise RuntimeError(f"PATH_TEST_MASTER_AUDIO_SAMPLE_MISMATCH: expected {expected_audio_samples}, got {media['audio_samples']}")
    if manifest.get("planned_transitions_not_realized") is None:
        raise RuntimeError("PATH_TEST_TRANSITION_DISCLOSURE_MISSING")

    return {
        "status": "PASS",
        "lifecycle_mode": "path-test",
        "run_id": args.run_id,
        "revision": args.revision,
        "job_count": len(admitted),
        "master": media,
        "delivery_status": manifest["delivery_status"],
        "quality_evaluation": manifest["quality_evaluation"],
        "planned_transitions_not_realized": manifest["planned_transitions_not_realized"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--revision", default="v04")
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = validate(args)
    if args.report:
        if args.report.exists():
            raise RuntimeError(f"PATH_TEST_REPORT_OVERWRITE_FORBIDDEN: {args.report}")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(yaml.safe_dump(result, sort_keys=False), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
