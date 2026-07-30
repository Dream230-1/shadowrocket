#!/usr/bin/env python3
"""Convert Shadowrocket-style modules into memory-efficient Stash rule providers."""

from __future__ import annotations

import argparse
import csv
import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterable

IP_TYPES = {"IP-CIDR", "IP-CIDR6"}
POLICIES = {
    "DIRECT",
    "PROXY",
    "REJECT",
    "REJECT-DROP",
    "REJECT-DICT",
    "REJECT-ARRAY",
    "REJECT-200",
    "REJECT-IMG",
    "REJECT-TINYGIF",
    "REJECT-NO-DROP",
}
URL_SCHEME_PREFIXES = (r"^https?:\/\/", r"^https?://")


def unique(items: Iterable[str]) -> list[str]:
    return list(OrderedDict.fromkeys(items))


def parse_rule(line: str) -> tuple[str, str, list[str]] | None:
    """Return rule type, complete payload and modifiers after the policy field.

    URL regular expressions can contain commas in quantifiers such as ``{0,5}``.
    The policy is therefore located first, then every field before it is joined
    back into the payload instead of treating the second CSV field as complete.
    """
    try:
        fields = next(csv.reader([line], skipinitialspace=True))
    except csv.Error:
        return None

    fields = [field.strip() for field in fields]
    if len(fields) < 3:
        return None

    policy_index = next(
        (index for index in range(2, len(fields)) if fields[index].upper() in POLICIES),
        None,
    )
    if policy_index is None:
        return None

    rule_type = fields[0].upper()
    value = ",".join(fields[1:policy_index]).strip()
    modifiers = fields[policy_index + 1 :]
    if not value:
        return None
    return rule_type, value, modifiers


def url_regex_to_domain_regex(value: str) -> str | None:
    """Convert host-only URL regex rules to Stash DOMAIN-REGEX rules.

    The upstream rules match only the URL scheme and hostname. Converting them
    avoids Stash classical-provider parsing failures while preserving the actual
    hostname match. Path-specific URL expressions are deliberately left alone.
    """
    host_pattern: str | None = None
    for prefix in URL_SCHEME_PREFIXES:
        if value.startswith(prefix):
            host_pattern = value[len(prefix) :]
            break

    if host_pattern is None or not host_pattern:
        return None
    if "/" in host_pattern or r"\/" in host_pattern:
        return None

    if host_pattern.endswith(".*$"):
        host_pattern = host_pattern[:-3]
    if not host_pattern:
        return None

    if not host_pattern.startswith("^"):
        host_pattern = "^" + host_pattern
    if not host_pattern.endswith("$"):
        host_pattern += "$"
    return host_pattern


def convert(input_path: Path) -> dict[str, list[str]]:
    domain: list[str] = []
    ipcidr: list[str] = []
    classical: list[str] = []

    for raw_line in input_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue

        parsed = parse_rule(line)
        if parsed is None:
            continue

        rule_type, value, modifiers = parsed
        if rule_type == "DOMAIN" and not modifiers:
            domain.append(value)
        elif rule_type == "DOMAIN-SUFFIX" and not modifiers:
            domain.append(f"+.{value.lstrip('.')}")
        elif rule_type in IP_TYPES and all(item.lower() == "no-resolve" for item in modifiers):
            ipcidr.append(value)
        elif rule_type == "URL-REGEX" and not modifiers:
            domain_regex = url_regex_to_domain_regex(value)
            if domain_regex is not None:
                classical.append(f"DOMAIN-REGEX,{domain_regex}")
            else:
                classical.append(f"URL-REGEX,{value}")
        else:
            classical.append(",".join([rule_type, value, *modifiers]))

    return {
        "domain": unique(domain),
        "ipcidr": unique(ipcidr),
        "classical": unique(classical),
    }


def write_yaml(path: Path, payload: list[str], source_sha: str, source_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Source: GMOogway/shadowrocket-rules@{source_sha}",
        f"# Input: {source_name}",
        f"# Rules: {len(payload)}",
    ]
    if payload:
        lines.append("payload:")
        lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in payload)
    else:
        lines.append("payload: []")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("reject_module", type=Path)
    parser.add_argument("direct_module", type=Path)
    parser.add_argument("proxy_module", type=Path)
    args = parser.parse_args()

    inputs = {
        "reject": args.reject_module,
        "direct": args.direct_module,
        "proxy": args.proxy_module,
    }
    for name, input_path in inputs.items():
        converted = convert(input_path)
        for behavior, payload in converted.items():
            output = args.output_dir / f"gmoogway-{name}-{behavior}.yaml"
            write_yaml(output, payload, args.source_commit, input_path.name)
            print(f"{output}: {len(payload)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
