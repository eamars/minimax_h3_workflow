from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_environment_profile(manifest: dict, canon: dict, external_profile: dict | None, by_id: dict) -> None:
    environment_assets = [
        asset for asset in manifest.get("assets", [])
        if "environment_architecture" in asset.get("role", [])
    ]
    if not environment_assets:
        return

    profile = external_profile or canon.get("environment_profile") or manifest.get("environment_profile")
    if isinstance(profile, dict) and isinstance(profile.get("environment_profile"), dict):
        profile = profile["environment_profile"]
    if not isinstance(profile, dict):
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: environment architecture has no hard projection")
    required = {
        "profile_id",
        "source_asset_id",
        "enforcement",
        "required_landmarks",
        "allowed_features",
        "forbidden_inventions",
        "unknown_features",
        "negative_space_rule",
    }
    missing = sorted(required - set(profile))
    if missing:
        raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: missing {missing}")
    if profile["enforcement"] != "hard_reference_no_expansion":
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: environment enforcement must be hard_reference_no_expansion")
    source_asset_id = profile["source_asset_id"]
    if source_asset_id not in by_id or "environment_architecture" not in by_id[source_asset_id].get("role", []):
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: profile source_asset_id is not an environment asset")
    for field in ("required_landmarks", "allowed_features", "forbidden_inventions", "unknown_features"):
        value = profile[field]
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: {field} must be a list of non-empty strings")
    if not isinstance(profile["negative_space_rule"], str) or not profile["negative_space_rule"].strip():
        raise AssertionError("ENVIRONMENT_PROFILE_MISSING: negative_space_rule is required")
    positive = {item.strip().lower() for field in ("required_landmarks", "allowed_features") for item in profile[field]}
    forbidden = {item.strip().lower() for item in profile["forbidden_inventions"]}
    overlap = sorted(positive & forbidden)
    if overlap:
        raise AssertionError(f"ENVIRONMENT_FEATURE_FORBIDDEN: positive and forbidden features overlap {overlap}")

    for container_name, container in (("manifest", manifest.get("environment_profile")), ("canon", canon.get("environment_profile"))):
        if isinstance(container, dict):
            candidate = container.get("environment_profile") if isinstance(container.get("environment_profile"), dict) else container
            if candidate.get("profile_id") and candidate["profile_id"] != profile["profile_id"]:
                raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: {container_name} profile id does not match")
            if candidate.get("source_asset_id") and candidate["source_asset_id"] != source_asset_id:
                raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: {container_name} source asset does not match")
    for asset in environment_assets:
        if asset.get("environment_profile_id") and asset["environment_profile_id"] != profile["profile_id"]:
            raise AssertionError(f"ENVIRONMENT_PROFILE_MISSING: asset {asset['asset_id']} references a different environment profile")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--asset-manifest", type=Path, required=True)
    ap.add_argument("--canon-lock", type=Path, required=True)
    ap.add_argument("--conflicts", type=Path, required=True)
    ap.add_argument("--order", type=Path, required=True)
    ap.add_argument("--environment-profile", type=Path)
    args = ap.parse_args()
    manifest, canon, conflicts, order = map(load, (args.asset_manifest, args.canon_lock, args.conflicts, args.order))
    assets = manifest.get("assets", [])
    ids, by_id = set(), {}
    for asset in assets:
        aid, rel = asset["asset_id"], asset["path"]
        if aid in ids: raise AssertionError(f"duplicate asset id {aid}")
        ids.add(aid); by_id[aid] = asset
        pure = PurePosixPath(rel)
        if pure.is_absolute() or ".." in pure.parts or "latest" in pure.parts: raise AssertionError(f"unsafe asset path {rel}")
        source = (args.project_root / Path(*pure.parts)).resolve()
        if not source.is_file(): raise AssertionError(f"missing asset {rel}")
        digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != asset["sha256"]: raise AssertionError(f"asset hash mismatch {aid}")
        if asset.get("media_type") == "audio" and asset.get("endpoint_role", "none") != "none": raise AssertionError("audio cannot be an endpoint")
    validate_environment_profile(manifest, canon, load(args.environment_profile) if args.environment_profile else None, by_id)
    canon_ids = {e["canon_id"] for e in canon.get("canon_entities", canon.get("entities", []))}
    for binding in canon.get("role_bindings", []):
        if binding["asset_id"] not in by_id or binding["canon_id"] not in canon_ids: raise AssertionError("unresolved canon binding")
        if not isinstance(binding.get("property_scope"), list) or not binding["property_scope"]: raise AssertionError("canon binding property scope missing")
        if binding.get("strength") not in {"canonical", "strong", "soft", "informational"}: raise AssertionError("canon binding strength invalid")
        if not binding.get("timeline_scope"): raise AssertionError("canon binding timeline scope missing")
    blocking = [c for c in conflicts.get("conflicts", []) if c.get("blocking") and not c.get("resolution")]
    ready = canon.get("plot_handoff", {}).get("ready", True)
    if blocking and ready:
        print("Blocking canon conflict", file=sys.stderr)
        return 2
    ordered = [aid for item in order.get("orders", []) for aid in item.get("ordered_asset_ids", [])]
    if any(aid not in by_id for aid in ordered): raise AssertionError("reference order contains missing asset")
    print("Validated reference-canon-manager outputs")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
