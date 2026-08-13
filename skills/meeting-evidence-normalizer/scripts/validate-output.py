#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED = [
    "manifest.json",
    "transcription.raw.json",
    "transcription.analysis.json",
    "transcription.normalized.json",
    "evidence.json",
    "uncertainties.json",
    "meeting.md",
]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: validate-output.py <output-dir>", file=sys.stderr)
        return 2
    output_dir = Path(argv[0])
    missing = [name for name in REQUIRED if not (output_dir / name).exists()]
    if missing:
        print(json.dumps({"status": "INVALID", "missing": missing}, indent=2))
        return 1
    for name in REQUIRED:
        if name.endswith(".json"):
            json.loads((output_dir / name).read_text(encoding="utf-8"))
    print(json.dumps({"status": "OK", "output": str(output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

