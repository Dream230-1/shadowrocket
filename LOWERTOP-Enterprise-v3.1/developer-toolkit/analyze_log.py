#!/usr/bin/env python3
"""Analyze exported Shadowrocket text logs with tolerant parsing."""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

POLICIES = ("DIRECT", "PROXY", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "MITM", "SCRIPT")
URL_RE = re.compile(r"https?://[^\s]+", re.I)
HOSTPORT_RE = re.compile(r"(?<![\w.-])([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?::\d{1,5})?")
RULE_RE = re.compile(r"\b(DOMAIN(?:-SUFFIX|-KEYWORD)?|IP-CIDR6?|URL-REGEX|RULE-SET|FINAL),([^\s]+)", re.I)
STATUS_RE = re.compile(r"(?:status(?:Code)?|HTTP)\s*[:= ]\s*(\d{3})", re.I)


def host_from_line(line: str) -> str | None:
    url = URL_RE.search(line)
    if url:
        try:
            return urlsplit(url.group(0)).hostname
        except ValueError:
            pass
    match = HOSTPORT_RE.search(line)
    return match.group(1).lower() if match else None


def policy_from_line(line: str) -> str:
    upper = line.upper()
    for policy in POLICIES:
        if re.search(rf"\b{re.escape(policy)}\b", upper):
            return policy
    return "UNKNOWN"


def analyze(lines: list[str], keywords: list[str]) -> dict:
    selected: list[dict] = []
    policy_counts: collections.Counter[str] = collections.Counter()
    host_counts: collections.Counter[str] = collections.Counter()
    rule_counts: collections.Counter[str] = collections.Counter()
    status_counts: collections.Counter[str] = collections.Counter()
    rejected_hosts: collections.Counter[str] = collections.Counter()

    normalized_keywords = [item.lower() for item in keywords if item]
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        if normalized_keywords and not any(keyword in line.lower() for keyword in normalized_keywords):
            continue

        host = host_from_line(line)
        policy = policy_from_line(line)
        rule_match = RULE_RE.search(line)
        rule = f"{rule_match.group(1).upper()},{rule_match.group(2)}" if rule_match else None
        status_match = STATUS_RE.search(line)
        status = status_match.group(1) if status_match else None

        policy_counts[policy] += 1
        if host:
            host_counts[host] += 1
            if policy.startswith("REJECT"):
                rejected_hosts[host] += 1
        if rule:
            rule_counts[rule] += 1
        if status:
            status_counts[status] += 1

        selected.append({
            "line": number,
            "text": line,
            "host": host,
            "policy": policy,
            "rule": rule,
            "status": status,
        })

    suspicious = [
        item for item in selected
        if item["policy"].startswith("REJECT")
        or item["policy"] in {"MITM", "SCRIPT"}
        or item["status"] and int(item["status"]) >= 400
    ]
    return {
        "ok": not any(item["policy"].startswith("REJECT") for item in selected),
        "keywords": keywords,
        "matched_lines": len(selected),
        "summary": {
            "policies": dict(policy_counts.most_common()),
            "hosts": dict(host_counts.most_common()),
            "rules": dict(rule_counts.most_common()),
            "statuses": dict(status_counts.most_common()),
            "rejected_hosts": dict(rejected_hosts.most_common()),
        },
        "suspicious": suspicious,
        "entries": selected,
    }


def markdown(payload: dict) -> str:
    lines = [
        "# Shadowrocket 日志分析",
        "",
        f"- 匹配行数：{payload['matched_lines']}",
        f"- 关键字：{', '.join(payload['keywords']) if payload['keywords'] else '无'}",
        "",
        "## 策略汇总",
        "",
        "| 策略 | 次数 |",
        "|---|---:|",
    ]
    for key, value in payload["summary"]["policies"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## 可疑记录", ""])
    if not payload["suspicious"]:
        lines.append("- 未发现 REJECT、MITM、SCRIPT 或 HTTP 4xx/5xx 记录。")
    else:
        for item in payload["suspicious"]:
            lines.append(f"- L{item['line']} `{item['policy']}` `{item['host'] or '-'}`：{item['text']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", help="Shadowrocket 导出的文本日志")
    parser.add_argument("--keyword", action="append", default=[], help="筛选关键字，可重复使用")
    parser.add_argument("--json-out", help="写入 JSON 报告")
    parser.add_argument("--markdown-out", help="写入 Markdown 摘要")
    parser.add_argument("--fail-on-reject", action="store_true", help="存在 REJECT 时退出码为 1")
    args = parser.parse_args()

    path = Path(args.log)
    if not path.is_file():
        parser.error(f"日志不存在：{path}")
    payload = analyze(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), args.keyword)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.markdown_out:
        out = Path(args.markdown_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown(payload), encoding="utf-8")

    print(json.dumps({"ok": payload["ok"], "matched_lines": payload["matched_lines"], "summary": payload["summary"], "suspicious": payload["suspicious"]}, ensure_ascii=False, indent=2))
    return 1 if args.fail_on_reject and not payload["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
