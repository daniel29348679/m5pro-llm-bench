#!/usr/bin/env python3
"""Mark every reference to MLX-tagged models with a 🍎 prefix.

Idempotent: running it multiple times will not stack markers.
Targets all README*.md, REPORT.md, and results/*.md.

Add new MLX-tagged model names to MLX_MODELS as needed.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARK = "🍎 "

MLX_MODELS = [
    "gemma4:e4b-mlx-bf16",
    "qwen3.6:27b-coding-mxfp8",
    "qwen3.6:27b-coding-nvfp4",
    "qwen3.6:35b-a3b-coding-mxfp8",
    "qwen3.6:35b-a3b-coding-nvfp4",
]


def process(text: str) -> str:
    for name in MLX_MODELS:
        target = f"`{name}`"
        # Strip any pre-existing marker first so this is idempotent.
        text = text.replace(MARK + target, target)
        text = text.replace(target, MARK + target)
    return text


def main() -> int:
    files: list[Path] = []
    files.extend(sorted(ROOT.glob("README*.md")))
    report = ROOT / "REPORT.md"
    if report.exists():
        files.append(report)
    files.extend(sorted((ROOT / "results").glob("*.md")))

    changed = 0
    for f in files:
        original = f.read_text(encoding="utf-8")
        if not any(name in original for name in MLX_MODELS):
            continue
        new = process(original)
        if new != original:
            f.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  marked {f.relative_to(ROOT)}")
        else:
            print(f"  unchanged {f.relative_to(ROOT)}")
    print(f"\n{changed} file(s) modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
