#!/usr/bin/env python3
"""Static validator for Shadowrocket module/config files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_SECTIONS = {
    "General", "Rule", "Host", "URL Rewrite", "Map Local", "Script", "MITM",
    "Proxy", "Proxy Group", "DNS", "Rewrite", "Header Rewrite",
}
ALLOWED_SCRIPT_TYPES = {"http-request", "http-response", "event", "rule", "dns", "cron"}
MODULE_SUFFIXES = {".sgmodule", ".srmodule", ".module", ".conf"}
META_RE = re.compile(r"^#!([A-Za-z0-9_-]+)\s*=\s*(.*)$")
SECTION_RE = re.compile(r"^\[([^]]+)]\s*$")
SCRIPT_TYPE_RE = re.compile(r"(?:^|,)\s*type\s*=\s*([^,\s]+)", re.I)
SCRIPT_PATH_RE = re.compile(r"(?:^|,)\s*script-path\s*=\s*([^,\s]+)", re.I)
HOSTNAME_RE = re.compile(r"^\s*hostname\s*=\s*(.+)$", re.I)


def discover(inputs: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in MODULE_SUFFIXES)
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(raw)
    return sorted(set(files))


def issue(level: str, code: str, message: str, line: int | None = None) -> dict:
    result = {"level": level, "code": code, "message": message}
    if line is not None:
        result["line"] = line
    return result


def parse_hostnames(value: str) -> list[str]:
    return [part.strip() for part in value.replace("%APPEND%", "").split(",") if part.strip()]


def validate(path: Path, allowed_wildcards: set[str] | None = None) -> dict:
    allowed_wildcards = allowed_wildcards or set()
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    is_module = path.suffix.lower() in {".sgmodule", ".srmodule", ".module"}
    metadata: dict[str, str] = {}
    sections: list[str] = []
    hostnames: list[str] = []
    findings: list[dict] = []
    current_section = ""

    for number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith("#") and not line.startswith("#!"):
            continue

        meta_match = META_RE.match(line)
        if meta_match:
            metadata[meta_match.group(1).lower()] = meta_match.group(2).strip()
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1).strip()
            sections.append(current_section)
            if current_section not in ALLOWED_SECTIONS:
                findings.append(issue("error", "unknown-section", f"未知区块 [{current_section}]", number))
            continue

        if current_section == "Script":
            if "=" not in raw_line:
                findings.append(issue("error", "invalid-script-line", "脚本行缺少名称与等号", number))
                continue
            payload = raw_line.split("=", 1)[1]
            type_match = SCRIPT_TYPE_RE.search(payload)
            if not type_match:
                findings.append(issue("error", "missing-script-type", "脚本行缺少 type=", number))
            else:
                script_type = type_match.group(1).lower()
                if script_type not in ALLOWED_SCRIPT_TYPES:
                    findings.append(issue("error", "unsupported-script-type", f"Shadowrocket 不支持脚本类型 {script_type}", number))
            path_match = SCRIPT_PATH_RE.search(payload)
            if path_match:
                script_path = path_match.group(1)
                if not script_path.startswith("https://"):
                    findings.append(issue("error", "insecure-script-path", "远程 script-path 必须使用 HTTPS", number))
                if "/releases/latest/" in script_path:
                    findings.append(issue("warning", "mutable-script-release", "script-path 使用 releases/latest，稳定发布前应锁定不可变版本", number))

        if current_section == "MITM":
            host_match = HOSTNAME_RE.match(raw_line)
            if host_match:
                value = host_match.group(1)
                hostnames.extend(parse_hostnames(value))
                if is_module and "%APPEND%" not in value:
                    findings.append(issue("error", "mitm-without-append", "模块的 MITM hostname 必须使用 %APPEND%", number))

        if current_section == "Map Local" and re.search(r'data\s*=\s*"\{\}"', raw_line):
            findings.append(issue("warning", "empty-object-map-local", "整接口返回空对象可能删除正常业务字段，应完成实机回归", number))

        if current_section == "URL Rewrite" and re.search(r"\s-\sreject(?:-dict|-array)?\s*$", raw_line, re.I):
            pattern = raw_line.split(" - ", 1)[0].strip()
            if pattern.endswith(r"\.com") or pattern.endswith(r"\.net"):
                findings.append(issue("warning", "broad-url-reject", "URL Rewrite 看起来可能覆盖整个域名", number))

    for key in ("name", "desc"):
        if is_module and not metadata.get(key):
            findings.append(issue("error", f"missing-meta-{key}", f"模块缺少 #!{key}= 元数据"))

    if len(sections) != len(set(sections)):
        findings.append(issue("warning", "duplicate-section", "存在重复区块，需确认 Shadowrocket 合并行为"))

    for hostname in sorted(set(hostnames)):
        if hostname == "*" or hostname.startswith("*."):
            if hostname not in allowed_wildcards:
                findings.append(issue("error", "wildcard-mitm", f"禁止使用过宽 MITM Hostname：{hostname}"))
        elif "/" in hostname or "://" in hostname:
            findings.append(issue("error", "invalid-mitm-hostname", f"MITM Hostname 只能填写主机名：{hostname}"))

    errors = [item for item in findings if item["level"] == "error"]
    warnings = [item for item in findings if item["level"] == "warning"]
    return {
        "file": str(path),
        "ok": not errors,
        "metadata": metadata,
        "sections": sections,
        "mitm_hostnames": sorted(set(hostnames)),
        "summary": {"errors": len(errors), "warnings": len(warnings)},
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="模块文件或目录")
    parser.add_argument("--json-out", help="将完整报告写入 JSON")
    parser.add_argument("--strict", action="store_true", help="将警告也视为失败")
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

    allowed_wildcards = set(args.allow_wildcard_host)
    reports = [validate(path, allowed_wildcards) for path in files]
    payload = {
        "ok": all(r["ok"] and (not args.strict or not r["summary"]["warnings"]) for r in reports),
        "strict": args.strict,
        "allowed_wildcards": sorted(allowed_wildcards),
        "files": len(reports),
        "reports": reports,
    }

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for report in reports:
        status = "PASS" if report["ok"] else "FAIL"
        print(f"[{status}] {report['file']} errors={report['summary']['errors']} warnings={report['summary']['warnings']}")
        for finding in report["findings"]:
            location = f":{finding['line']}" if "line" in finding else ""
            print(f"  {finding['level'].upper()} {finding['code']}{location}: {finding['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
