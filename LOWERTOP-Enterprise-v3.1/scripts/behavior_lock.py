#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import yaml


def normalize_config(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return "\n".join(lines) + "\n"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_config(text: str) -> dict:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    general = {}
    for line in sections.get("[General]", []):
        if "=" in line:
            key, value = line.split("=", 1)
            general[key.strip()] = value.strip()
    groups = {}
    for line in sections.get("[Proxy Group]", []):
        if "=" in line:
            key, value = line.split("=", 1)
            groups[key.strip()] = value.strip()
    return {"sections": sections, "general": general, "proxy_groups": groups}


def behavior_contract(text: str) -> dict:
    parsed = parse_config(text)
    rules = parsed["sections"].get("[Rule]", [])
    return {
        "general": parsed["general"],
        "proxy_groups": parsed["proxy_groups"],
        "rules": rules,
        "host": parsed["sections"].get("[Host]", []),
        "final_rule": next((line for line in reversed(rules) if line.upper().startswith("FINAL,")), None),
    }


def compare(expected, actual, path: str = "") -> list[dict]:
    diffs: list[dict] = []
    if type(expected) is not type(actual):
        return [{"path": path or "$", "expected": expected, "actual": actual}]
    if isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            child = f"{path}.{key}" if path else key
            if key not in expected:
                diffs.append({"path": child, "expected": "<missing>", "actual": actual[key]})
            elif key not in actual:
                diffs.append({"path": child, "expected": expected[key], "actual": "<missing>"})
            else:
                diffs.extend(compare(expected[key], actual[key], child))
    elif isinstance(expected, list):
        if expected != actual:
            max_len = max(len(expected), len(actual))
            for index in range(max_len):
                child = f"{path}[{index}]"
                ev = expected[index] if index < len(expected) else "<missing>"
                av = actual[index] if index < len(actual) else "<missing>"
                if ev != av:
                    diffs.append({"path": child, "expected": ev, "actual": av})
                    if len(diffs) >= 100:
                        break
    elif expected != actual:
        diffs.append({"path": path or "$", "expected": expected, "actual": actual})
    return diffs


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze and verify the RC1 Performance routing contract")
    parser.add_argument("--config", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--json-out", default="reports/behavior-lock.json")
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--source-commit")
    args = parser.parse_args()

    config = Path(args.config).resolve()
    baseline = Path(args.baseline).resolve()
    text = config.read_text(encoding="utf-8")
    normalized = normalize_config(text)
    contract = behavior_contract(text)
    observed = {
        "schema": 1,
        "source_commit": args.source_commit,
        "artifact": config.name,
        "raw_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "semantic_sha256": sha256_text(normalized),
        "semantic_line_count": len(normalized.splitlines()),
        "contract": contract,
    }

    if args.write_baseline:
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_text(yaml.safe_dump(observed, allow_unicode=True, sort_keys=False, width=240), encoding="utf-8")
        report = {"ok": True, "mode": "write-baseline", "baseline": str(baseline), **{k: observed[k] for k in ("artifact", "raw_sha256", "semantic_sha256", "semantic_line_count")}}
    else:
        expected = yaml.safe_load(baseline.read_text(encoding="utf-8"))
        diffs = compare(expected.get("contract"), contract)
        expected_sha = expected.get("semantic_sha256")
        if expected_sha != observed["semantic_sha256"] and not diffs:
            diffs.append({"path": "semantic_sha256", "expected": expected_sha, "actual": observed["semantic_sha256"]})
        report = {
            "ok": not diffs,
            "mode": "verify",
            "baseline": str(baseline),
            "artifact": config.name,
            "expected_semantic_sha256": expected_sha,
            "actual_semantic_sha256": observed["semantic_sha256"],
            "differences": diffs[:100],
            "scope": "General, Proxy Group, Rule order/policy, Host and FINAL; comments and release labels are ignored.",
        }

    output = Path(args.json_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
