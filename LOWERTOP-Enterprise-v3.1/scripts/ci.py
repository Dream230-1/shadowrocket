#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import traceback

import build


def run_tests(project: Path) -> None:
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=project, check=True)
    kernel = project.parent / "LOWERTOP-Enterprise-v3.0-RC3"
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-v"], cwd=kernel, check=True)


try:
    project = Path(__file__).resolve().parents[1]
    run_tests(project)
    build.main()
    subprocess.run([sys.executable, "scripts/validate_field_records.py"], cwd=project, check=True)
    subprocess.run([sys.executable, "scripts/release_report.py"], cwd=project, check=True)
except Exception:
    root = Path(__file__).resolve().parents[1]
    out = root / "build"
    out.mkdir(parents=True, exist_ok=True)
    (out / "build-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    raise
