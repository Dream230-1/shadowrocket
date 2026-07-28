#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


class ToolkitTests(unittest.TestCase):
    def run_tool(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [PYTHON, str(ROOT / script), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validator_rejects_generic_script_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "bad.sgmodule"
            module.write_text(
                "#!name=bad\n#!desc=test\n[Script]\nrun = type=generic, script-path=https://example.com/test.js\n",
                encoding="utf-8",
            )
            result = self.run_tool("validate_module.py", str(module))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported-script-type", result.stdout)

    def test_mitm_extractor_outputs_unique_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            module = Path(tmp) / "mitm.sgmodule"
            module.write_text(
                "#!name=mitm\n#!desc=test\n[MITM]\nhostname = %APPEND% api.example.com, api.example.com, grpc.example.com\n",
                encoding="utf-8",
            )
            result = self.run_tool("extract_mitm.py", str(module), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hostname_count"], 2)

    def test_log_analyzer_finds_reject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "shadowrocket.log"
            log.write_text(
                "api.bilibili.com:443 DOMAIN-SUFFIX,bilibili.com,DIRECT\n"
                "ads.example.com:443 DOMAIN-SUFFIX,ads.example.com,REJECT\n",
                encoding="utf-8",
            )
            report = Path(tmp) / "report.json"
            result = self.run_tool(
                "analyze_log.py", str(log), "--json-out", str(report), "--fail-on-reject"
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["policies"]["REJECT"], 1)
            self.assertEqual(payload["summary"]["rejected_hosts"]["ads.example.com"], 1)


if __name__ == "__main__":
    unittest.main()
