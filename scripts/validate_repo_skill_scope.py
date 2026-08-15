"""Validate that repository skills are local and not duplicated in user scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = (
    "animatic-previs-planner",
    "comfyui",
    "comfyui-workflow-compiler",
    "continuity-qc-supervisor",
    "keyframe-handoff-builder",
    "minimax-h3-adapter",
    "plot-architect",
    "post-editor",
    "production-orchestrator",
    "production-preflight-reviewer",
    "reference-canon-manager",
    "render-orchestrator",
    "repair-director",
    "request-normalizer",
    "scene-performance-writer",
    "sound-dialogue-planner",
    "storyboard-director",
)
DEFAULT_USER_ROOTS = (
    Path.home() / ".agents" / "skills",
    Path.home() / ".codex" / "skills",
)


def validate(workspace_root: Path, user_roots: tuple[Path, ...]) -> dict:
    repo_root = workspace_root / ".agents" / "skills"
    packages = sorted(
        path.name
        for path in repo_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )
    accidental_copies = []
    for user_root in user_roots:
        for name in packages:
            candidate = user_root / name
            if candidate.is_dir():
                accidental_copies.append(str(candidate))
    unexpected_skills = sorted(set(packages) - set(EXPECTED_SKILLS))
    missing_skills = sorted(set(EXPECTED_SKILLS) - set(packages))
    return {
        "repo_skill_root": str(repo_root),
        "skills_checked": packages,
        "expected_skills": list(EXPECTED_SKILLS),
        "unexpected_skills": unexpected_skills,
        "missing_skills": missing_skills,
        "user_roots_checked": [str(path) for path in user_roots],
        "accidental_user_copies": accidental_copies,
        "status": "PASS" if not unexpected_skills and not missing_skills and not accidental_copies else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=ROOT)
    parser.add_argument("--user-root", action="append", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    user_roots = tuple(args.user_root) if args.user_root else DEFAULT_USER_ROOTS
    report = validate(args.workspace_root.resolve(), tuple(path.resolve() for path in user_roots))
    if args.json or report["status"] != "PASS":
        print(json.dumps(report, indent=2))
    else:
        print(f"PASS: {len(report['skills_checked'])} skills are repository-scoped only")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
