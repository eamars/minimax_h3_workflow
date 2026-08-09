"""Compare workspace skill packages with the active installed skill registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_files(package: Path) -> set[Path]:
    return {
        path.relative_to(package)
        for path in package.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
    }


def compare(workspace_root: Path, installed_root: Path) -> dict:
    workspace_skills = workspace_root / "skills"
    packages = sorted(path.name for path in workspace_skills.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    mismatches: list[dict] = []
    for name in packages:
        source = workspace_skills / name
        target = installed_root / name
        if not target.is_dir():
            mismatches.append({"skill": name, "reason": "installed_package_missing"})
            continue
        source_files = package_files(source)
        target_files = package_files(target)
        missing = sorted(str(item) for item in source_files - target_files)
        changed = sorted(str(item) for item in source_files & target_files if digest(source / item) != digest(target / item))
        if missing or changed:
            mismatches.append({"skill": name, "missing": missing, "changed": changed})
    return {"workspace_root": str(workspace_root), "installed_root": str(installed_root), "skills_checked": packages, "status": "PASS" if not mismatches else "FAIL", "mismatches": mismatches}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--installed-root", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = compare(args.workspace_root.resolve(), args.installed_root.resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    elif report["status"] == "PASS":
        print(f"PASS: {len(report['skills_checked'])} active skill packages match workspace files")
    else:
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
