#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path("/opt/attendance-system").resolve()
OFFICIAL_DIRS = [
    REPO_ROOT / "SA/modules",
    REPO_ROOT / "SA/architecture",
    REPO_ROOT / "SA/governance",
]
OFFICIAL_FILES = [
    REPO_ROOT / "SA/CHANGELOG.md",
    REPO_ROOT / "SA/README.md",
    REPO_ROOT / "SA/SDD_PROGRESS_TRACKER.md",
]
LEGACY_ROOT = REPO_ROOT / "SA/legacy-import"


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def official_targets() -> list[Path]:
    results: list[Path] = []
    for root in OFFICIAL_DIRS:
        if root.exists():
            results.extend(sorted(root.rglob("*.md")))
    for path in OFFICIAL_FILES:
        if path.exists():
            results.append(path)
    deduped = []
    seen = set()
    for path in results:
        rp = path.resolve()
        if rp not in seen:
            seen.add(rp)
            deduped.append(rp)
    return deduped


def inventory_legacy_zero_files() -> list[Path]:
    if not LEGACY_ROOT.exists():
        return []
    return sorted(
        path for path in LEGACY_ROOT.rglob("*.md")
        if path.is_file() and path.stat().st_size == 0
    )


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def staged_blob_size(repo_rel_path: str) -> int:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-s", f":{repo_rel_path}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return -1
    return int(result.stdout.strip())


def check_worktree() -> list[str]:
    errors: list[str] = []
    for path in official_targets():
        if path.stat().st_size == 0:
            errors.append(f"0KB official SA doc: {rel(path)}")
    return errors


def check_staged() -> list[str]:
    errors: list[str] = []
    official = {rel(path) for path in official_targets()}
    for repo_rel_path in staged_files():
        if repo_rel_path not in official:
            continue
        size = staged_blob_size(repo_rel_path)
        if size == 0:
            errors.append(f"0KB staged SA doc: {repo_rel_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check official SA docs are not 0KB and inventory legacy empty markdown files.")
    parser.add_argument("--inventory-legacy", action="store_true", help="Print 0KB markdown files under SA/legacy-import")
    parser.add_argument("--check-worktree", action="store_true", help="Fail if any official SA doc in working tree is 0KB")
    parser.add_argument("--check-staged", action="store_true", help="Fail if any staged official SA doc is 0KB")
    args = parser.parse_args()

    ran_check = False

    if args.inventory_legacy:
        legacy_zero = inventory_legacy_zero_files()
        if legacy_zero:
            print("LEGACY_ZERO_KB_FILES")
            for path in legacy_zero:
                print(rel(path))
        else:
            print("LEGACY_ZERO_KB_FILES: none")

    if args.check_worktree:
        ran_check = True
        errors = check_worktree()
        if errors:
            print("SA integrity check failed:", file=sys.stderr)
            for item in errors:
                print(f"- {item}", file=sys.stderr)
            return 1

    if args.check_staged:
        ran_check = True
        errors = check_staged()
        if errors:
            print("SA staged integrity check failed:", file=sys.stderr)
            for item in errors:
                print(f"- {item}", file=sys.stderr)
            return 1

    if ran_check:
        print("SA integrity check passed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
