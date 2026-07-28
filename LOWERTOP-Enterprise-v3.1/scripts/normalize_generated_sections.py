#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

RULE_PREFIXES = (
    "DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,", "IP-CIDR,", "IP-CIDR6,",
    "GEOIP,", "RULE-SET,", "FINAL,",
)


def section_index(lines: list[str], name: str) -> int | None:
    try:
        return lines.index(name)
    except ValueError:
        return None


def section_end(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        line = lines[index].strip()
        if line.startswith("[") and line.endswith("]"):
            return index
    return len(lines)


def normalize(path: Path, extra_rules: list[str], hosts: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()

    extras = set(extra_rules)
    lines = [line for line in lines if line.strip() not in extras]

    rule_start = section_index(lines, "[Rule]")
    if rule_start is None:
        raise ValueError(f"{path}: missing [Rule]")
    rule_end = section_end(lines, rule_start)
    final_index = next(
        (index for index in range(rule_start + 1, rule_end) if lines[index].strip().startswith("FINAL,")),
        None,
    )
    if final_index is None:
        raise ValueError(f"{path}: missing FINAL rule")
    if extra_rules:
        block = ["# 额外广告域名拦截（由 scripts.yaml 注入）", *extra_rules]
        lines[final_index:final_index] = block

    mitm_start = section_index(lines, "[MITM]")
    if mitm_start is not None:
        mitm_end = section_end(lines, mitm_start)
        del lines[mitm_start:mitm_end]

    if hosts:
        host_start = section_index(lines, "[Host]")
        if host_start is None:
            raise ValueError(f"{path}: missing [Host]")
        lines[host_start:host_start] = [
            "[MITM]",
            "hostname = " + ",".join(hosts),
            "",
        ]

    current = ""
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            current = stripped
        elif stripped.startswith(RULE_PREFIXES) and current != "[Rule]":
            raise ValueError(f"{path}:{number}: rule outside [Rule]")
    if hosts and section_index(lines, "[MITM]") is None:
        raise ValueError(f"{path}: MITM hosts were not rendered")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    project = Path(args.project).resolve()
    data = yaml.safe_load((project / "config" / "scripts.yaml").read_text(encoding="utf-8")) or {}
    extra_rules = [str(item).strip() for item in data.get("extra_rules", [])]
    hosts = [str(item).strip() for item in data.get("mitm_hostname", [])]

    outputs = []
    for directory in ("build", "modular", "experimental"):
        for path in sorted((project / directory).glob("*.conf")):
            normalize(path, extra_rules, hosts)
            outputs.append(str(path.relative_to(project)))
    if not outputs:
        raise SystemExit("no generated configuration files found")
    print(f"normalized {len(outputs)} generated configurations")


if __name__ == "__main__":
    main()
