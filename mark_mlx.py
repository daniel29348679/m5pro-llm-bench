#!/usr/bin/env python3
"""Mark every reference to the MLX-tagged model with a 🍎 prefix.

Idempotent: running it multiple times will not stack markers.
Targets all README*.md, REPORT.md, and results/*.md.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "🍎 "
TARGET = "`gemma4:e4b-mlx-bf16`"


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    # Strip any pre-existing marker first so this is idempotent,
    # then apply the marker uniformly.
    cleaned = text.replace(MARK + TARGET, TARGET)
    marked = cleaned.replace(TARGET, MARK + TARGET)
    if marked != text:
        path.write_text(marked, encoding="utf-8")
        return True
    return False


def main() -> int:
    files: list[Path] = []
    files.extend(sorted(ROOT.glob("README*.md")))
    report = ROOT / "REPORT.md"
    if report.exists():
        files.append(report)
    files.extend(sorted((ROOT / "results").glob("*.md")))

    changed = 0
    for f in files:
        if TARGET not in f.read_text(encoding="utf-8"):
            continue
        if process(f):
            changed += 1
            print(f"  marked {f.relative_to(ROOT)}")
        else:
            print(f"  unchanged (already marked) {f.relative_to(ROOT)}")
    print(f"\n{changed} file(s) modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
