#!/usr/bin/env python3
"""Audit Shadowrocket rewrite, script, and MITM coverage for conflicts."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^\[([^]]+)]\s*$")
HOSTNAME_RE = re.compile(r"^\s*hostname\s*=\s*(.+)$", re.I)
NAMED_SCRIPT_RE = re.compile(r"^\s*([^=]+?)\s*=\s*(.+)$")
SCRIPT_PATTERN_RE = re.compile(r"(?:^|,)\s*pattern\s*=\s*([^,]+)", re.I)
SCRIPT_TYPE_PREFIX_RE = re.compile(r"^\s*(http-(?:request|response))\s+(\S+)", re.I)
TAG_RE = re.compile(r"(?:^|,)\s*tag\s*=\s*([^,]+)", re.I)
SUPPORTED_SUFFIXES = {".sgmodule", ".srmodule", ".module", ".conf"}
AUDITED_SECTIONS = {"URL Rewrite", "Map Local", "Script", "MITM"}


def discover(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES
            )
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return sorted(set(files))


def normalize_pattern(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def parse_script(line: str) -> tuple[str | None, str | None]:
    prefixed = SCRIPT_TYPE_PREFIX_RE.match(line)
    if prefixed:
        tag = TAG_RE.search(line)
        name = tag.group(1).strip() if tag else None
        return name, normalize_pattern(prefixed.group(2))

    named = NAMED_SCRIPT_RE.match(line)
    if named:
        name = named.group(1).strip()
        pattern = SCRIPT_PATTERN_RE.search(named.group(2))
        return name, normalize_pattern(pattern.group(1)) if pattern else None

    return None, None


def parse_file(path: Path, role: str) -> dict:
    current_section = ""
    scripts: list[dict] = []
    coverage: list[dict] = []
    hostnames: list[dict] = []

    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        section = SECTION_RE.match(line)
        if section:
            current_section = section.group(1).strip()
            continue
        if current_section not in AUDITED_SECTIONS:
            continue

        source = {"file": str(path), "line": number, "role": role}
        if current_section == "MITM":
            match = HOSTNAME_RE.match(raw)
            if match:
                for item in match.group(1).replace("%APPEND%", "").split(","):
                    hostname = item.strip().lower().rstrip(".")
                    if hostname:
                        hostnames.append({**source, "hostname": hostname})
            continue

        if current_section == "Script":
            name, pattern = parse_script(raw)
            if name:
                scripts.append({**source, "name": name})
            if pattern:
                coverage.append({**source, "mechanism": "Script", "pattern": pattern})
            continue

        pattern = (
            raw.split(" - ", 1)[0]
            if current_section == "URL Rewrite"
            else re.split(r"\s+data\s*=", raw, maxsplit=1, flags=re.I)[0]
        )
        coverage.append(
            {
                **source,
                "mechanism": current_section,
                "pattern": normalize_pattern(pattern),
            }
        )

    return {
        "file": str(path),
        "role": role,
        "scripts": scripts,
        "coverage": coverage,
        "mitm_hostnames": hostnames,
    }


def finding(level: str, code: str, message: str, sources: list[dict]) -> dict:
    return {"level": level, "code": code, "message": message, "sources": sources}


def audit(base: Path, module_files: list[Path]) -> dict:
    parsed = [parse_file(base, "base")]
    parsed.extend(parse_file(path, "module") for path in module_files)
    findings: list[dict] = []

    script_index: dict[str, list[dict]] = {}
    pattern_index: dict[str, list[dict]] = {}
    hostname_index: dict[str, list[dict]] = {}
    for report in parsed:
        for item in report["scripts"]:
            script_index.setdefault(item["name"].casefold(), []).append(item)
        for item in report["coverage"]:
            pattern_index.setdefault(item["pattern"], []).append(item)
        for item in report["mitm_hostnames"]:
            hostname_index.setdefault(item["hostname"], []).append(item)

    for entries in script_index.values():
        if len(entries) > 1:
            findings.append(
                finding(
                    "error",
                    "duplicate-script-name",
                    f"脚本名称重复：{entries[0]['name']}",
                    entries,
                )
            )

    for pattern, entries in pattern_index.items():
        mechanisms = {item["mechanism"] for item in entries}
        if len(mechanisms) > 1:
            findings.append(
                finding(
                    "error",
                    "cross-mechanism-pattern",
                    f"同一匹配表达式被多个机制覆盖：{pattern}",
                    entries,
                )
            )
        elif len(entries) > 1:
            findings.append(
                finding(
                    "warning",
                    "duplicate-pattern",
                    f"匹配表达式重复：{pattern}",
                    entries,
                )
            )

    for hostname, entries in hostname_index.items():
        roles = {item["role"] for item in entries}
        if len(entries) > 1:
            level = "error" if len(roles) > 1 else "warning"
            findings.append(
                finding(
                    level,
                    "duplicate-mitm-hostname",
                    f"MITM Hostname 重复：{hostname}",
                    entries,
                )
            )

    errors = [item for item in findings if item["level"] == "error"]
    warnings = [item for item in findings if item["level"] == "warning"]
    return {
        "ok": not errors,
        "base_config": str(base),
        "module_files": len(module_files),
        "summary": {
            "scripts": sum(len(item["scripts"]) for item in parsed),
            "coverage_patterns": sum(len(item["coverage"]) for item in parsed),
            "mitm_hostnames": len(hostname_index),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "findings": findings,
        "files": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", required=True, help="RC 主配置文件")
    parser.add_argument("modules", nargs="+", help="可选模块文件或目录")
    parser.add_argument("--json-out", help="将审计报告写入 JSON")
    parser.add_argument("--strict", action="store_true", help="将警告也视为失败")
    args = parser.parse_args()

    base = Path(args.base_config)
    if not base.is_file():
        parser.error(f"主配置不存在：{base}")
    try:
        module_files = discover(args.modules)
    except FileNotFoundError as exc:
        parser.error(f"路径不存在：{exc}")

    payload = audit(base, module_files)
    passed = payload["ok"] and (not args.strict or payload["summary"]["warnings"] == 0)
    payload["strict"] = args.strict
    payload["passed"] = passed

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = "PASS" if passed else "FAIL"
    print(
        f"[{status}] coverage audit "
        f"errors={payload['summary']['errors']} warnings={payload['summary']['warnings']}"
    )
    for item in payload["findings"]:
        print(f"  {item['level'].upper()} {item['code']}: {item['message']}")
        for source in item["sources"]:
            print(f"    - {source['file']}:{source['line']} ({source['role']})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
