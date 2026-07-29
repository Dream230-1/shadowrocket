#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import yaml


SHA40 = re.compile(r"^[0-9a-f]{40}$")
RAW_GITHUB = re.compile(
    r"^https://raw\.githubusercontent\.com/[^/]+/[^/]+/([0-9a-f]{40})/(.+)$"
)
MUTABLE_URL_MARKERS = (
    "/main/",
    "/master/",
    "/blob/",
    "/releases/latest/",
    "/latest/download/",
)
SENSITIVE_HOST_TOKENS = (
    "account",
    "auth",
    "bank",
    "login",
    "oauth",
    "passport",
    "pay",
    "payment",
    "wallet",
)
UNLOCK_NAME_TOKENS = ("解锁", "会员版", "vip版", "svip")


def script_lines(text: str) -> list[str]:
    section = ""
    result: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line.lower()
            continue
        if section == "[script]" and line and not line.startswith("#"):
            result.append(line)
    return result


def script_urls(text: str) -> list[str]:
    urls: list[str] = []
    for line in script_lines(text):
        match = re.search(r"(?:script-path|script-update-url)=([^,\s]+)", line)
        if match:
            urls.append(match.group(1))
    return urls


def mitm_hosts(text: str) -> list[str]:
    hosts: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.lower().startswith("hostname") and "=" in line:
            value = line.split("=", 1)[1].replace("%APPEND%", "").replace("%INSERT%", "")
            hosts.extend(item.strip() for item in value.split(",") if item.strip())
    return hosts


def hosts_overlap(left: str, right: str) -> bool:
    left_suffix = left.removeprefix("*.")
    right_suffix = right.removeprefix("*.")
    return (
        left == right
        or left.endswith("." + right_suffix)
        or right.endswith("." + left_suffix)
        or ("*" in left and right.endswith(left_suffix))
        or ("*" in right and left.endswith(right_suffix))
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", default="reports/optional-module-security.json")
    args = parser.parse_args()

    project = Path(__file__).resolve().parents[1]
    optional = project / "modules" / "optional"
    inventory_path = project / "config" / "module-audit.yaml"
    inventory = yaml.safe_load(inventory_path.read_text(encoding="utf-8")) or {}
    specs = inventory.get("modules", {}) or {}
    errors: list[str] = []
    warnings: list[str] = []
    observed: dict[str, dict] = {}

    files = {path.name: path for path in optional.glob("*.sgmodule")}
    missing_specs = sorted(set(files) - set(specs))
    missing_files = sorted(set(specs) - set(files))
    if missing_specs:
        errors.append("modules missing audit inventory: " + ", ".join(missing_specs))
    if missing_files:
        errors.append("audit inventory references missing modules: " + ", ".join(missing_files))

    host_owners: list[tuple[str, str]] = []
    for filename, path in sorted(files.items()):
        text = path.read_text(encoding="utf-8")
        spec = specs.get(filename, {}) or {}
        title = next(
            (line.split("=", 1)[1].strip() for line in text.splitlines() if line.startswith("#!name=")),
            filename,
        )
        if any(token.lower() in title.lower() for token in UNLOCK_NAME_TOKENS):
            errors.append(f"{filename}: membership or entitlement unlock naming is forbidden")

        commits = spec.get("source_commits", []) or []
        if not commits or any(not SHA40.fullmatch(str(commit)) for commit in commits):
            errors.append(f"{filename}: every audited source commit must be a 40-character SHA")

        urls = script_urls(text)
        for url in urls:
            lower = url.lower()
            if any(marker in lower for marker in MUTABLE_URL_MARKERS):
                errors.append(f"{filename}: mutable or blob script URL: {url}")
                continue
            match = RAW_GITHUB.fullmatch(url)
            if not match:
                errors.append(f"{filename}: script URL must use raw GitHub with a 40-character SHA: {url}")

        hosts = mitm_hosts(text)
        expected_hosts = [str(host) for host in spec.get("mitm_hosts", []) or []]
        if hosts != expected_hosts:
            errors.append(f"{filename}: MITM hosts differ from audit inventory")
        allowed_wildcards = set(spec.get("allowed_wildcards", []) or [])
        for host in hosts:
            host_owners.append((filename, host))
            if "*" in host and host not in allowed_wildcards:
                errors.append(f"{filename}: unapproved MITM wildcard: {host}")
            normalized = host.replace("*.", "").lower()
            labels = set(re.split(r"[.-]", normalized))
            hits = sorted(token for token in SENSITIVE_HOST_TOKENS if token in labels)
            if hits:
                errors.append(
                    f"{filename}: payment/login/account-like MITM hostname is forbidden: {host}"
                )

        joined_scripts = "\n".join(script_lines(text)).lower()
        for token in spec.get("forbidden_pattern_tokens", []) or []:
            if str(token).lower() in joined_scripts:
                errors.append(f"{filename}: forbidden URL-pattern token: {token}")

        capture = spec.get("capture_validation")
        if capture and capture != "passed":
            warnings.append(f"{filename}: capture validation is {capture}")
        observed[filename] = {
            "source": spec.get("source"),
            "source_commits": commits,
            "script_urls": urls,
            "mitm_hosts": hosts,
            "conflicts": spec.get("conflicts", []) or [],
            "capture_validation": capture,
        }

    for index, (left_file, left_host) in enumerate(host_owners):
        for right_file, right_host in host_owners[index + 1 :]:
            if left_file != right_file and hosts_overlap(left_host, right_host):
                errors.append(
                    f"MITM host conflict: {left_file}:{left_host} overlaps "
                    f"{right_file}:{right_host}"
                )

    report = {
        "ok": not errors,
        "inventory": str(inventory_path.relative_to(project)),
        "module_count": len(files),
        "errors": errors,
        "warnings": warnings,
        "modules": observed,
    }
    output = project / args.json_out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
