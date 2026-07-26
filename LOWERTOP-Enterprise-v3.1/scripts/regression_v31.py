#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import yaml


def load_kernel_module(path: Path):
    spec = importlib.util.spec_from_file_location("lowertop_kernel_regression", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法载入回归内核：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description="V3.1 route regression with negative assertions")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--kernel-root", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--cases", action="append", required=True)
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--cache-dir", default=".cache/regression")
    parser.add_argument("--json-out", default="reports/regression.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    kernel = Path(args.kernel_root).resolve()
    sys.path.insert(0, str(kernel / "scripts"))
    regression = load_kernel_module(kernel / "scripts" / "regression.py")
    cache_dir = Path(args.cache_dir)
    if not cache_dir.is_absolute():
        cache_dir = root / cache_dir
    # The inherited regression kernel hashes URL paths for its cache names. Seed those names
    # from the shared ruleset-name cache so online regression performs no duplicate downloads.
    if args.online:
        config_text = (root / args.config).read_text(encoding="utf-8")
        source = None
        for raw in config_text.splitlines():
            line = raw.strip()
            if line.startswith("# Remote ruleset:"):
                source = line.removeprefix("# Remote ruleset:").strip().split(" → ", 1)[0]
            elif source and line.startswith("RULE-SET,"):
                url = line.split(",", 2)[1]
                named = cache_dir / f"{source}.list"
                hashed = cache_dir / regression.cache_name(url)
                if named.exists() and not hashed.exists():
                    shutil.copy2(named, hashed)
                source = None
    rules, skipped = regression.compile_config(root / args.config, cache_dir, not args.online)

    cases = []
    for case_file in args.cases:
        data = yaml.safe_load((root / case_file).read_text(encoding="utf-8")) or {}
        for case in data.get("cases", []):
            item = dict(case)
            item["case_file"] = case_file
            cases.append(item)

    results, failures, skipped_cases = [], [], []
    for case in cases:
        if case.get("requires_remote", False) and not args.online:
            skipped_cases.append(case["name"])
            continue
        hit = regression.first_match(rules, case)
        if hit is None:
            result = {"name": case["name"], "ok": False, "error": "无匹配规则", "case_file": case["case_file"]}
        else:
            expected_source = case.get("expected_source_contains")
            forbidden_policies = case.get("forbidden_policies", [])
            forbidden_sources = case.get("forbidden_sources", [])
            checks = {
                "policy": hit.policy == case["expected_policy"],
                "source": not expected_source or expected_source.lower() in hit.source.lower(),
                "forbidden_policy": hit.policy not in forbidden_policies,
                "forbidden_source": not any(value.lower() in hit.source.lower() for value in forbidden_sources),
            }
            result = {
                "name": case["name"], "ok": all(checks.values()), "case_file": case["case_file"],
                "host": case.get("host"), "expected_policy": case["expected_policy"], "actual_policy": hit.policy,
                "expected_source_contains": expected_source, "actual_source": hit.source,
                "forbidden_policies": forbidden_policies, "forbidden_sources": forbidden_sources,
                "checks": checks, "matched_rule": hit.raw, "order": hit.order,
            }
        results.append(result)
        if not result["ok"]:
            failures.append(result)

    report = {
        "ok": not failures,
        "mode": "online" if args.online else "offline",
        "config": args.config,
        "case_files": args.cases,
        "compiled_rule_count": len(rules),
        "summary": {"executed": len(results), "passed": len(results) - len(failures), "failed": len(failures), "skipped": len(skipped_cases)},
        "skipped_remote_urls": skipped,
        "skipped_cases": skipped_cases,
        "results": results,
        "failures": failures,
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
