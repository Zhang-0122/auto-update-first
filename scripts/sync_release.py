#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy the generated dashboard into the public release directory."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "double" / "ssq_analyzer.html"
RELEASE_DIR = ROOT / "release"
TARGET = RELEASE_DIR / "index.html"


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Dashboard not found: {SOURCE}")
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, TARGET)
    print(f"Synced {SOURCE} -> {TARGET}")


if __name__ == "__main__":
    main()

