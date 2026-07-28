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

    def test_coverage_audit_accepts_isolated_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.conf"
            module = Path(tmp) / "safe.sgmodule"
            report = Path(tmp) / "coverage.json"
            base.write_text(
                "[Script]\n"
                "http-request ^https://base\\.example\\.com/v1/ script-path=https://example.com/base.js, tag=Base\n"
                "[MITM]\n"
                "hostname = base.example.com\n",
                encoding="utf-8",
            )
            module.write_text(
                "#!name=safe\n#!desc=test\n"
                "[Script]\n"
                "Safe = type=http-response,pattern=^https://api\\.example\\.com/v1/item,"
                "script-path=https://example.com/safe.js\n"
                "[MITM]\n"
                "hostname = %APPEND% api.example.com\n",
                encoding="utf-8",
            )
            result = self.run_tool(
                "audit_coverage.py",
                "--base-config",
                str(base),
                str(module),
                "--json-out",
                str(report),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["summary"]["errors"], 0)
            self.assertEqual(payload["summary"]["scripts"], 2)
            self.assertEqual(payload["summary"]["coverage_patterns"], 2)

    def test_coverage_audit_rejects_duplicate_script_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.conf"
            module = Path(tmp) / "duplicate.sgmodule"
            base.write_text(
                "[Script]\n"
                "Base = type=http-request,pattern=^https://base\\.example\\.com/v1/,"
                "script-path=https://example.com/base.js\n",
                encoding="utf-8",
            )
            module.write_text(
                "#!name=duplicate\n#!desc=test\n"
                "[Script]\n"
                "Base = type=http-response,pattern=^https://api\\.example\\.com/v1/,"
                "script-path=https://example.com/module.js\n",
                encoding="utf-8",
            )
            result = self.run_tool(
                "audit_coverage.py", "--base-config", str(base), str(module)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate-script-name", result.stdout)

    def test_coverage_audit_rejects_cross_mechanism_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base.conf"
            module = Path(tmp) / "conflict.sgmodule"
            pattern = r"^https://api\.example\.com/v1/item"
            base.write_text(
                f"[URL Rewrite]\n{pattern} - reject\n",
                encoding="utf-8",
            )
            module.write_text(
                "#!name=conflict\n#!desc=test\n"
                "[Script]\n"
                f"Conflict = type=http-response,pattern={pattern},"
                "script-path=https://example.com/module.js\n",
                encoding="utf-8",
            )
            result = self.run_tool(
                "audit_coverage.py", "--base-config", str(base), str(module)
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cross-mechanism-pattern", result.stdout)


if __name__ == "__main__":
    unittest.main()
