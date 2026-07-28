#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RC4ValidationContractTests(unittest.TestCase):
    def test_only_apple_weather_is_a_required_mainline_module(self) -> None:
        validator = load_script("validate_field_records")
        self.assertEqual(validator.REQUIRED_MODULES, {"apple-weather-qweather"})

    def test_release_report_does_not_restore_frozen_module_gates(self) -> None:
        source = (ROOT / "scripts" / "release_report.py").read_text(encoding="utf-8")
        self.assertNotIn('"bilibili_module"', source)
        self.assertNotIn('"baidu_netdisk_module"', source)
        self.assertNotIn('"ip_quality_module"', source)
        self.assertIn('"apple_weather_module"', source)


if __name__ == "__main__":
    unittest.main()
