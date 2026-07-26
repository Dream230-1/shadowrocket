#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

try:
    from common import ALLOWED_RULE_TYPES, load_yaml, parse_rule, sha256_bytes, upstream_url
except ModuleNotFoundError:
    kernel_scripts = Path(__file__).resolve().parents[2] / "LOWERTOP-Enterprise-v3.0-RC3" / "scripts"
    sys.path.insert(0, str(kernel_scripts))
    from common import ALLOWED_RULE_TYPES, load_yaml, parse_rule, sha256_bytes, upstream_url


def audit_cached(manifest: dict, item: dict, cache_dir: Path) -> dict:
    url = upstream_url(manifest, item["path"])
    audit = item.get("audit", {})
    path = cache_dir / f'{item["name"]}.list'
    result = {"name": item["name"], "url": url, "policy": item["policy"], "cache_file": str(path), "ok": False}
    if f'/{manifest["meta"]["upstream_commit"]}/' not in url:
        result["error"] = "URL 未固定到 manifest commit"; return result
    if not path.exists():
        result["error"] = "条件缓存缺失，请先运行 cache_refresh.py"; return result
    content = path.read_bytes()
    if len(content) > audit.get("max_bytes", 100_000_000):
        result["error"] = f"文件过大：{len(content)} bytes"; return result
    text = content.decode("utf-8")
    counts, unknown = Counter(), Counter()
    invalid, rule_count = [], 0
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            parts = parse_rule(stripped, allow_unknown=True)
        except Exception as exc:
            invalid.append({"line": lineno, "content": stripped[:200], "error": str(exc)}); continue
        if not parts:
            continue
        if parts[0] not in ALLOWED_RULE_TYPES:
            unknown[parts[0]] += 1
        else:
            counts[parts[0]] += 1; rule_count += 1
    errors = []
    if not audit.get("min_rules", 1) <= rule_count <= audit.get("max_rules", 10**9):
        errors.append(f"规则数 {rule_count} 超出审计范围")
    if invalid: errors.append(f"存在 {len(invalid)} 条无法解析的规则")
    if unknown: errors.append(f"存在未知规则类型：{dict(unknown)}")
    result.update({"ok": not errors, "bytes": len(content), "sha256": sha256_bytes(content), "rule_count": rule_count,
                   "rule_types": dict(counts), "unknown_types": dict(unknown), "invalid_lines": invalid[:20], "errors": errors})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the shared conditional cache without downloading again")
    parser.add_argument("--root", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()
    root, cache = Path(args.root).resolve(), Path(args.cache_dir).resolve()
    manifest = load_yaml(root / "manifest.yaml")
    results = [audit_cached(manifest, item, cache) for item in manifest.get("remote_rulesets", [])]
    failures = [item for item in results if not item["ok"]]
    report = {"ok": not failures, "upstream_commit": manifest["meta"]["upstream_commit"], "cache_reused": True, "results": results, "failures": failures}
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__": main()
