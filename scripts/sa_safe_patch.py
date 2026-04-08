#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tempfile
import os


REPO_ROOT = Path("/opt/attendance-system").resolve()
SA_ROOT = (REPO_ROOT / "SA").resolve()
MIN_OUTPUT_BYTES = 32
SHRINK_WARNING_RATIO = 0.6


class SafePatchError(Exception):
    pass


@dataclass
class PatchInput:
    target: Path
    old_text: str
    new_text: str
    dry_run: bool
    allow_missing_backup: bool


@dataclass
class ValidationSnapshot:
    size_bytes: int
    line_count: int
    first_non_empty_line: str


def parse_args() -> PatchInput:
    parser = argparse.ArgumentParser(
        description="Safely patch a single section inside SA/*.md without risking whole-file overwrite."
    )
    parser.add_argument("target", help="Target markdown file under SA/")
    parser.add_argument("--old", dest="old_text", help="Exact old text to replace")
    parser.add_argument("--new", dest="new_text", help="Exact new text")
    parser.add_argument("--old-file", dest="old_file", help="Read exact old text from file")
    parser.add_argument("--new-file", dest="new_file", help="Read new text from file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate patch result but do not write to disk",
    )
    parser.add_argument(
        "--allow-missing-backup",
        action="store_true",
        help="Skip backup write failure blocking (not recommended)",
    )
    args = parser.parse_args()

    old_text = resolve_text_argument(args.old_text, args.old_file, "old")
    new_text = resolve_text_argument(args.new_text, args.new_file, "new")

    if old_text == new_text:
        raise SafePatchError("old/new content cannot be identical")

    return PatchInput(
        target=Path(args.target),
        old_text=old_text,
        new_text=new_text,
        dry_run=args.dry_run,
        allow_missing_backup=args.allow_missing_backup,
    )


def resolve_text_argument(inline_value: str | None, file_value: str | None, label: str) -> str:
    if bool(inline_value) == bool(file_value):
        raise SafePatchError(f"provide exactly one of --{label} or --{label}-file")
    if inline_value is not None:
        return inline_value
    file_path = Path(file_value).resolve()
    ensure_exists(file_path, f"{label} file")
    return file_path.read_text(encoding="utf-8")


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise SafePatchError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise SafePatchError(f"{label} is not a file: {path}")


def resolve_target(target_arg: Path) -> Path:
    target = target_arg
    if not target.is_absolute():
        target = (REPO_ROOT / target).resolve()
    else:
        target = target.resolve()

    ensure_exists(target, "target")

    try:
        target.relative_to(SA_ROOT)
    except ValueError as exc:
        raise SafePatchError(f"target must be inside {SA_ROOT}") from exc

    if target.suffix.lower() != ".md":
        raise SafePatchError("target must be a markdown file (*.md)")

    return target


def snapshot(text: str) -> ValidationSnapshot:
    first_non_empty = next((line for line in text.splitlines() if line.strip()), "")
    return ValidationSnapshot(
        size_bytes=len(text.encode("utf-8")),
        line_count=len(text.splitlines()),
        first_non_empty_line=first_non_empty,
    )


def build_patched_text(original_text: str, old_text: str, new_text: str) -> str:
    occurrences = original_text.count(old_text)
    if occurrences == 0:
        raise SafePatchError("old text not found in target")
    if occurrences > 1:
        raise SafePatchError(f"old text matched {occurrences} times; patch must be unique")
    return original_text.replace(old_text, new_text, 1)


def validate_transition(before: ValidationSnapshot, after: ValidationSnapshot, original_text: str, patched_text: str) -> None:
    if after.size_bytes < MIN_OUTPUT_BYTES:
        raise SafePatchError(f"patched file too small: {after.size_bytes} bytes")
    if not patched_text.strip():
        raise SafePatchError("patched file would be empty")
    if before.first_non_empty_line and before.first_non_empty_line not in patched_text:
        raise SafePatchError("patched file lost the original first non-empty line")
    if after.line_count <= 0:
        raise SafePatchError("patched file line count invalid")

    if before.size_bytes > 0:
        ratio = after.size_bytes / before.size_bytes
        if ratio < SHRINK_WARNING_RATIO:
            raise SafePatchError(
                "patched file shrank too much "
                f"({before.size_bytes} -> {after.size_bytes} bytes, ratio={ratio:.2f})"
            )

    if original_text == patched_text:
        raise SafePatchError("patch produced no change")


def create_backup(target: Path, original_text: str, allow_missing_backup: bool) -> Path | None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = target.with_name(f"{target.name}.bak-{timestamp}")
    try:
        atomic_write_text(backup_path, original_text)
        if backup_path.stat().st_size <= 0:
            raise SafePatchError(f"backup write produced empty file: {backup_path}")
        return backup_path
    except Exception as exc:
        if allow_missing_backup:
            return None
        raise SafePatchError(f"backup failed: {exc}") from exc


def atomic_write_text(destination: Path, text: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(destination.parent),
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_path = Path(handle.name)
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())

    try:
        if tmp_path.stat().st_size <= 0:
            raise SafePatchError(f"temporary file is empty: {tmp_path}")
        tmp_path.replace(destination)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def main() -> int:
    try:
        patch_input = parse_args()
        target = resolve_target(patch_input.target)
        original_text = target.read_text(encoding="utf-8")
        if not original_text.strip():
            raise SafePatchError("target is empty; restore first, do not patch abnormal file")

        patched_text = build_patched_text(original_text, patch_input.old_text, patch_input.new_text)
        before = snapshot(original_text)
        after = snapshot(patched_text)
        validate_transition(before, after, original_text, patched_text)

        backup_path = None
        if not patch_input.dry_run:
            backup_path = create_backup(target, original_text, patch_input.allow_missing_backup)

        if patch_input.dry_run:
            print(f"[dry-run] target: {target}")
            print(f"[dry-run] backup: {backup_path if backup_path else 'skipped'}")
            print(f"[dry-run] size: {before.size_bytes} -> {after.size_bytes} bytes")
            print(f"[dry-run] lines: {before.line_count} -> {after.line_count}")
            return 0

        atomic_write_text(target, patched_text)
        written_text = target.read_text(encoding="utf-8")
        if written_text != patched_text:
            raise SafePatchError("post-write verification failed: disk content mismatch")

        print(f"patched: {target}")
        print(f"backup: {backup_path if backup_path else 'skipped'}")
        print(f"size: {before.size_bytes} -> {after.size_bytes} bytes")
        print(f"lines: {before.line_count} -> {after.line_count}")
        return 0
    except SafePatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
