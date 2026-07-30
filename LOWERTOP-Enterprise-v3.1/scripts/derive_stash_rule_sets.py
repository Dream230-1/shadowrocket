#!/usr/bin/env python3
"""Convert Shadowrocket modules into full and delta-optimized Stash rule providers."""

from __future__ import annotations

import argparse
import csv
import ipaddress
import json
from collections import OrderedDict
from dataclasses import dataclass, field
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


def normalize_domain(value: str) -> str:
    return value.strip().lower().rstrip(".")


def suffix_chain(domain: str) -> Iterable[str]:
    parts = domain.split(".")
    for index in range(len(parts)):
        yield ".".join(parts[index:])


@dataclass
class DomainCoverage:
    exact: set[str] = field(default_factory=set)
    suffix: set[str] = field(default_factory=set)
    keyword: set[str] = field(default_factory=set)

    def copy(self) -> "DomainCoverage":
        return DomainCoverage(set(self.exact), set(self.suffix), set(self.keyword))

    def update(self, other: "DomainCoverage") -> None:
        self.exact.update(other.exact)
        self.suffix.update(other.suffix)
        self.keyword.update(other.keyword)

    def add_provider_item(self, item: str) -> None:
        if item.startswith("+."):
            domain = normalize_domain(item[2:])
            if domain:
                self.suffix.add(domain)
        else:
            domain = normalize_domain(item)
            if domain:
                self.exact.add(domain)

    def covers_exact(self, domain: str) -> bool:
        domain = normalize_domain(domain)
        if domain in self.exact:
            return True
        if any(candidate in self.suffix for candidate in suffix_chain(domain)):
            return True
        return any(keyword in domain for keyword in self.keyword)

    def covers_suffix(self, domain: str) -> bool:
        domain = normalize_domain(domain)
        if any(candidate in self.suffix for candidate in suffix_chain(domain)):
            return True
        return any(keyword in domain for keyword in self.keyword)


def parse_rule(line: str) -> tuple[str, str, list[str]] | None:
    """Parse a Shadowrocket module rule and locate its policy field safely."""
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


def parse_plain_rule(line: str) -> tuple[str, str, list[str]] | None:
    """Parse a Stash/Clash classical text rule without a policy field."""
    try:
        fields = next(csv.reader([line], skipinitialspace=True))
    except csv.Error:
        return None
    fields = [field.strip() for field in fields]
    if len(fields) < 2:
        return None
    rule_type = fields[0].upper()
    value = fields[1].strip()
    if not value:
        return None
    return rule_type, value, fields[2:]


def url_regex_to_domain_regex(value: str) -> str | None:
    """Convert host-only URL regex rules to Stash DOMAIN-REGEX rules."""
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
            domain.append(normalize_domain(value))
        elif rule_type == "DOMAIN-SUFFIX" and not modifiers:
            domain.append(f"+.{normalize_domain(value.lstrip('.'))}")
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
        "domain": unique(item for item in domain if item and item != "+."),
        "ipcidr": unique(ipcidr),
        "classical": unique(classical),
    }


def load_base_rules(paths: list[Path]) -> tuple[DomainCoverage, list[ipaddress._BaseNetwork]]:
    coverage = DomainCoverage()
    networks: list[ipaddress._BaseNetwork] = []

    for path in paths:
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            parsed = parse_plain_rule(line)
            if parsed is None:
                continue
            rule_type, value, _modifiers = parsed
            if rule_type == "DOMAIN":
                domain = normalize_domain(value)
                if domain:
                    coverage.exact.add(domain)
            elif rule_type == "DOMAIN-SUFFIX":
                domain = normalize_domain(value.lstrip("."))
                if domain:
                    coverage.suffix.add(domain)
            elif rule_type == "DOMAIN-KEYWORD":
                keyword = normalize_domain(value)
                if keyword:
                    coverage.keyword.add(keyword)
            elif rule_type in IP_TYPES:
                try:
                    networks.append(ipaddress.ip_network(value, strict=False))
                except ValueError:
                    continue

    return coverage, list(ipaddress.collapse_addresses(networks))


def compact_domain_items(items: list[str], external: DomainCoverage) -> list[str]:
    """Remove rules already covered by base or broader higher-priority rules."""
    coverage = external.copy()
    suffixes = unique(normalize_domain(item[2:]) for item in items if item.startswith("+."))
    exacts = unique(normalize_domain(item) for item in items if not item.startswith("+."))

    output: list[str] = []
    for suffix in sorted(suffixes, key=lambda value: (value.count("."), len(value), value)):
        if not suffix or coverage.covers_suffix(suffix):
            continue
        output.append(f"+.{suffix}")
        coverage.suffix.add(suffix)

    for exact in exacts:
        if not exact or coverage.covers_exact(exact):
            continue
        output.append(exact)
        coverage.exact.add(exact)

    return output


def coverage_from_items(items: list[str]) -> DomainCoverage:
    coverage = DomainCoverage()
    for item in items:
        coverage.add_provider_item(item)
    return coverage


def compact_ipcidr(
    items: list[str], base_networks: list[ipaddress._BaseNetwork]
) -> list[str]:
    parsed: list[ipaddress._BaseNetwork] = []
    for item in items:
        try:
            network = ipaddress.ip_network(item, strict=False)
        except ValueError:
            continue
        if any(network.version == base.version and network.subnet_of(base) for base in base_networks):
            continue
        parsed.append(network)
    return [str(network) for network in ipaddress.collapse_addresses(parsed)]


def write_yaml(
    path: Path,
    payload: list[str],
    source_sha: str,
    source_name: str,
    base_sha: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Source: GMOogway/shadowrocket-rules@{source_sha}",
        f"# Input: {source_name}",
    ]
    if base_sha:
        lines.append(f"# Excludes: Repcz/Tool@{base_sha}")
    lines.append(f"# Rules: {len(payload)}")
    if payload:
        lines.append("payload:")
        lines.extend(f"  - {json.dumps(item, ensure_ascii=False)}" for item in payload)
    else:
        lines.append("payload: []")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--base-commit")
    parser.add_argument("--base-rule", action="append", type=Path, default=[])
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
    converted: dict[str, dict[str, list[str]]] = {}
    for name, input_path in inputs.items():
        converted[name] = convert(input_path)
        for behavior, payload in converted[name].items():
            output = args.output_dir / f"gmoogway-{name}-{behavior}.yaml"
            write_yaml(output, payload, args.source_commit, input_path.name)
            print(f"{output}: {len(payload)}")

    base_coverage, base_networks = load_base_rules(args.base_rule)

    lite_reject = compact_domain_items(converted["reject"]["domain"], base_coverage)
    after_reject = base_coverage.copy()
    after_reject.update(coverage_from_items(lite_reject))

    lite_direct = compact_domain_items(converted["direct"]["domain"], after_reject)
    after_direct = after_reject.copy()
    after_direct.update(coverage_from_items(lite_direct))

    lite_proxy = compact_domain_items(converted["proxy"]["domain"], after_direct)
    lite_proxy_ip = compact_ipcidr(converted["proxy"]["ipcidr"], base_networks)

    lite_outputs = {
        "reject-domain": lite_reject,
        "direct-domain": lite_direct,
        "proxy-domain": lite_proxy,
        "proxy-ipcidr": lite_proxy_ip,
    }
    for name, payload in lite_outputs.items():
        output = args.output_dir / f"gmoogway-lite-{name}.yaml"
        write_yaml(
            output,
            payload,
            args.source_commit,
            f"delta:{name}",
            args.base_commit,
        )
        print(f"{output}: {len(payload)}")

    full_total = sum(
        len(converted[name]["domain"]) for name in ("reject", "direct", "proxy")
    ) + len(converted["proxy"]["ipcidr"])
    lite_total = sum(len(payload) for payload in lite_outputs.values())
    report = [
        f"source_sha={args.source_commit}",
        f"base_sha={args.base_commit or ''}",
        f"base_files={len(args.base_rule)}",
        f"full_total={full_total}",
        f"lite_reject_domain={len(lite_reject)}",
        f"lite_direct_domain={len(lite_direct)}",
        f"lite_proxy_domain={len(lite_proxy)}",
        f"lite_proxy_ipcidr={len(lite_proxy_ip)}",
        f"lite_total={lite_total}",
        f"removed={full_total - lite_total}",
    ]
    report_path = args.output_dir / "gmoogway-lite-report.txt"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
