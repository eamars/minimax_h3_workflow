from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

import yaml


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", type=Path, required=True)
    ap.add_argument("--asset-manifest", type=Path, required=True)
    ap.add_argument("--canon-lock", type=Path, required=True)
    ap.add_argument("--conflicts", type=Path, required=True)
    ap.add_argument("--order", type=Path, required=True)
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
    canon_ids = {e["canon_id"] for e in canon.get("canon_entities", canon.get("entities", []))}
    for binding in canon.get("role_bindings", []):
        if binding["asset_id"] not in by_id or binding["canon_id"] not in canon_ids: raise AssertionError("unresolved canon binding")
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
