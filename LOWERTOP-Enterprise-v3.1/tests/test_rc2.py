from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
KERNEL_SCRIPTS = ROOT.parent / "LOWERTOP-Enterprise-v3.0-RC3" / "scripts"
sys.path.insert(0, str(KERNEL_SCRIPTS))
sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


behavior_lock = load("behavior_lock")
module_config = load("module_config")
rule_conflicts = load("rule_conflicts")


class BehaviorLockTests(unittest.TestCase):
    def test_comments_and_release_labels_do_not_change_contract(self):
        a = "# Version RC1\n[General]\nipv6 = false\n[Proxy Group]\nAI = select,PROXY\n[Rule]\nFINAL,PROXY\n[Host]\nlocalhost = 127.0.0.1\n"
        b = "# Version RC2\n# another comment\n[General]\nipv6 = false\n[Proxy Group]\nAI = select,PROXY\n[Rule]\nFINAL,PROXY\n[Host]\nlocalhost = 127.0.0.1\n"
        self.assertEqual(behavior_lock.behavior_contract(a), behavior_lock.behavior_contract(b))
        self.assertEqual(behavior_lock.normalize_config(a), behavior_lock.normalize_config(b))

    def test_rule_order_change_is_detected(self):
        expected = {"rules": ["DOMAIN,a.example,DIRECT", "FINAL,PROXY"]}
        actual = {"rules": ["FINAL,PROXY", "DOMAIN,a.example,DIRECT"]}
        self.assertTrue(behavior_lock.compare(expected, actual))


class ModuleTests(unittest.TestCase):
    def test_module_assembly_preserves_source_items(self):
        manifest = {
            "local_rulesets": [{"name": "A", "policy": "DIRECT", "stage": 10}],
            "remote_rulesets": [{"name": "B", "policy": "PROXY", "stage": 20}],
        }
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "all.yaml"
            p.write_text(yaml.safe_dump({"module": {"id": "all", "enabled": True, "rulesets": [
                {"kind": "local", "name": "A", "policy": "DIRECT", "stage": 10},
                {"kind": "remote", "name": "B", "policy": "PROXY", "stage": 20},
            ]}}), encoding="utf-8")
            merged, _ = module_config.apply_modules(manifest, Path(temp))
        self.assertEqual(merged["local_rulesets"][0]["name"], "A")
        self.assertEqual(merged["remote_rulesets"][0]["name"], "B")

    def test_module_policy_drift_fails(self):
        manifest = {"local_rulesets": [{"name": "A", "policy": "DIRECT", "stage": 10}], "remote_rulesets": []}
        with tempfile.TemporaryDirectory() as temp:
            Path(temp, "a.yaml").write_text(yaml.safe_dump({"module": {"id": "a", "enabled": True, "rulesets": [
                {"kind": "local", "name": "A", "policy": "PROXY", "stage": 10}
            ]}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                module_config.apply_modules(manifest, Path(temp))


class ConflictTests(unittest.TestCase):
    def test_domain_is_shadowed_by_suffix(self):
        hit, reason = rule_conflicts.overlap(["DOMAIN-SUFFIX", "apple.com"], ["DOMAIN", "news.apple.com"])
        self.assertTrue(hit)
        self.assertEqual(reason, "domain-in-suffix")

    def test_lexical_impostor_is_not_suffix_overlap(self):
        hit, _ = rule_conflicts.overlap(["DOMAIN-SUFFIX", "apple.com"], ["DOMAIN", "notapple.com"])
        self.assertFalse(hit)

    def test_cidr_scan_finds_cross_policy_overlap(self):
        rules = [
            {"parts": ["IP-CIDR", "10.0.0.0/8"], "policy": "DIRECT", "order": 1},
            {"parts": ["IP-CIDR", "10.1.0.0/16"], "policy": "PROXY", "order": 2},
            {"parts": ["IP-CIDR", "192.168.0.0/16"], "policy": "DIRECT", "order": 3},
        ]
        hits = list(rule_conflicts.candidate_overlaps(rules))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][2], "cidr-overlap")


if __name__ == "__main__":
    unittest.main()
