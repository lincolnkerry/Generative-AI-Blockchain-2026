#!/usr/bin/env python3
"""Create a SHA-256 hash manifest for project evidence files.

Usage:
    python code/scripts/hash_manifest.py usage-log/ hash_manifest.jsonl

This script does not upload anything to a blockchain by itself. It creates a
local tamper-evident manifest that can later be anchored on-chain if needed.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            yield path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python hash_manifest.py <target_path> <manifest_jsonl>", file=sys.stderr)
        return 2

    target = Path(sys.argv[1]).resolve()
    manifest = Path(sys.argv[2]).resolve()

    if not target.exists():
        print(f"Target does not exist: {target}", file=sys.stderr)
        return 1

    files = []
    for file_path in iter_files(target):
        files.append({
            "path": str(file_path.relative_to(target if target.is_dir() else target.parent)),
            "sha256": sha256_file(file_path),
            "size_bytes": file_path.stat().st_size,
        })

    entry = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": str(target),
        "file_count": len(files),
        "files": files,
    }

    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Manifest appended: {manifest}")
    print(f"Files hashed: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
