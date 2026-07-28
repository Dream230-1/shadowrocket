#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

import yaml

SECRET_PATTERNS = (
    re.compile(r"(?i)(?:api[_-]?key|token|secret|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b[a-f0-9]{32}\b", re.I),
)
RULE_PREFIXES = (
    "DOMAIN,", "DOMAIN-SUFFIX,", "DOMAIN-KEYWORD,", "IP-CIDR,", "IP-CIDR6,",
    "GEOIP,", "RULE-SET,", "FINAL,",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def as_string_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        fail(f"config/scripts.yaml: {key} must be a list of non-empty strings")
    return [item.strip() for item in value]


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    path = project / "config" / "scripts.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    scripts = as_string_list(data, "script_rules")
    rules = as_string_list(data, "extra_rules")
    hosts = as_string_list(data, "mitm_hostname")

    if bool(scripts) != bool(hosts):
        fail("config/scripts.yaml: script_rules and mitm_hostname must be enabled together")
    if len(hosts) != len(set(hosts)):
        fail("config/scripts.yaml: duplicate MITM hostname")
    if any("*" in host for host in hosts):
        fail("config/scripts.yaml: wildcard MITM hosts are forbidden in release profiles")
    if any(not rule.startswith(RULE_PREFIXES) for rule in rules):
        fail("config/scripts.yaml: extra_rules contains a non-rule entry")

    combined = "\n".join(scripts + rules + hosts)
    for pattern in SECRET_PATTERNS:
        if pattern.search(combined):
            fail("config/scripts.yaml: possible credential or API key detected")

    broad_baidu = [
        rule for rule in rules
        if rule.startswith("DOMAIN-KEYWORD,baidu") or rule.startswith("DOMAIN-SUFFIX,baidu.com")
    ]
    if broad_baidu:
        fail("config/scripts.yaml: broad Baidu blocking can break login, download or sharing")

    for rule in scripts:
        if "script-path=" not in rule:
            fail("config/scripts.yaml: every script rule must declare script-path")
        if "raw.githubusercontent.com/Dream230-1/shadowrocket/main/" in rule:
            fail("config/scripts.yaml: release scripts must not track main")

    print(
        f"scripts config OK: {len(scripts)} scripts, {len(hosts)} MITM hosts, "
        f"{len(rules)} extra rules"
    )


if __name__ == "__main__":
    main()
