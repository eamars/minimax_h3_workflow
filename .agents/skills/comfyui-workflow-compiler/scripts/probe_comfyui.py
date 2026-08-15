"""Capture an immutable ComfyUI capability profile without queueing work."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


def fetch(base_url: str, path: str):
    with urlopen(base_url.rstrip("/") + path, timeout=30) as response:
        return json.load(response)


def canonical_hash(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise AssertionError(f"refusing to overwrite {args.output}")

    object_info = fetch(args.base_url, "/object_info")
    model_types = fetch(args.base_url, "/models")
    models = {}
    for model_type in sorted(model_types):
        models[model_type] = fetch(args.base_url, "/models/" + quote(str(model_type), safe=""))
    system_stats = fetch(args.base_url, "/system_stats")
    evidence = {"object_info": object_info, "models": models, "system_stats": system_stats}
    profile = {
        "base_url": args.base_url.rstrip("/"),
        "probed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "object_info_sha256": canonical_hash(object_info),
        "model_listing_sha256": canonical_hash(models),
        "system_stats_sha256": canonical_hash(system_stats),
        "evidence": evidence,
    }
    profile["profile_hash"] = canonical_hash({key: value for key, value in profile.items() if key != "probed_at"})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(profile["profile_hash"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
