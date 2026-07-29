#!/usr/bin/env python3
"""Extract and audit MITM hostnames from Shadowrocket files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^\[([^]]+)]\s*$")
HOSTNAME_RE = re.compile(r"^\s*hostname\s*=\s*(.+)$", re.I)
SUFFIXES = {".sgmodule", ".srmodule", ".module", ".conf"}


def discover(inputs: list[str]) -> list[Path]:
    result: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            result.extend(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIXES)
        elif path.is_file():
            result.append(path)
        else:
            raise FileNotFoundError(raw)
    return sorted(set(result))


def extract(path: Path) -> dict:
    section = ""
    entries: list[dict] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        section_match = SECTION_RE.match(line)
        if section_match:
            section = section_match.group(1).strip()
            continue
        if section != "MITM":
            continue
        match = HOSTNAME_RE.match(raw)
        if not match:
            continue
        append = "%APPEND%" in match.group(1)
        for item in match.group(1).replace("%APPEND%", "").split(","):
            hostname = item.strip().lower().rstrip(".")
            if hostname:
                entries.append({"hostname": hostname, "line": number, "append": append})
    return {"file": str(path), "entries": entries}


def classify(hostname: str, allowed_wildcards: set[str] | None = None) -> list[str]:
    allowed_wildcards = allowed_wildcards or set()
    flags: list[str] = []
    if (hostname == "*" or hostname.startswith("*.")) and hostname not in allowed_wildcards:
        flags.append("wildcard")
    if "://" in hostname or "/" in hostname:
        flags.append("invalid-format")
    if hostname.count(".") < 1 and hostname != "localhost":
        flags.append("apex-or-local")
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="模块、配置文件或目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--json-out", help="写入 JSON 文件")
    parser.add_argument("--unique", action="store_true", help="仅输出去重 Hostname")
    parser.add_argument(
        "--allow-wildcard-host",
        action="append",
        default=[],
        help="显式允许一个经审计的 MITM 通配符主机；可重复传入",
    )
    args = parser.parse_args()

    try:
        files = discover(args.inputs)
    except FileNotFoundError as exc:
        parser.error(f"路径不存在：{exc}")

    sources = [extract(path) for path in files]
    index: dict[str, list[dict]] = {}
    for source in sources:
        for entry in source["entries"]:
            index.setdefault(entry["hostname"], []).append({
                "file": source["file"], "line": entry["line"], "append": entry["append"]
            })

    allowed_wildcards = set(args.allow_wildcard_host)
    hostnames = [
        {
            "hostname": hostname,
            "flags": classify(hostname, allowed_wildcards),
            "sources": entries,
        }
        for hostname, entries in sorted(index.items())
    ]
    payload = {
        "ok": not any(item["flags"] for item in hostnames),
        "allowed_wildcards": sorted(allowed_wildcards),
        "files": len(files),
        "hostname_count": len(hostnames),
        "hostnames": hostnames,
    }

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.unique:
        for item in hostnames:
            print(item["hostname"])
    else:
        for item in hostnames:
            flags = f" [{','.join(item['flags'])}]" if item["flags"] else ""
            print(f"{item['hostname']}{flags}")
            for source in item["sources"]:
                mode = "%APPEND%" if source["append"] else "replace"
                print(f"  - {source['file']}:{source['line']} ({mode})")

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
