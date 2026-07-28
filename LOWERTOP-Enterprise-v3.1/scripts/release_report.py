#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

import yaml


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return {"ok": False, "error": "invalid JSON", "path": str(path)}


def git_value(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "unknown"


def mark(value: bool | None) -> str:
    return "PASS" if value is True else "FAIL" if value is False else "PENDING"


def release_meta(root: Path) -> tuple[str, str]:
    data = yaml.safe_load((root / "config" / "release.yaml").read_text(encoding="utf-8")) or {}
    version = str(data.get("meta", {}).get("version", "unknown"))
    suffix = version.split("-", 1)[1].upper() if "-" in version else version.upper()
    return version, suffix


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="reports/release-validation.json")
    parser.add_argument("--markdown-out", default="RELEASE-VALIDATION.md")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    repo = root.parent
    version, release_label = release_meta(root)
    reports = root / "reports"
    report_names = {
        "behavior_lock": "behavior-lock.json", "dns_audit": "dns-audit.json",
        "regression_offline": "regression-offline.json", "regression_online": "regression-online.json",
        "remote_audit": "remote-audit.json", "ruleset_drift": "ruleset-drift.json",
        "adblock_collisions": "adblock-collisions.json", "rule_conflicts_offline": "rule-conflicts-offline.json",
        "rule_conflicts_online": "rule-conflicts-online.json", "service_health": "service-health.json",
        "network_benchmark": "network-benchmark.json", "cache_refresh": "cache-refresh.json",
        "field_validation": "field-validation.json",
        "modular_equivalence_offline": "modular-equivalence-offline.json",
        "modular_equivalence_online": "modular-equivalence-online.json",
    }
    audit = {key: load_json(reports / name) for key, name in report_names.items()}
    configs = []
    for directory in (root / "build", root / "modular", root / "experimental"):
        for path in sorted(directory.glob("*.conf")):
            configs.append({"path": str(path.relative_to(root)), "sha256": sha256(path), "bytes": path.stat().st_size})

    device_files = sorted((root / "validation" / "device").glob("**/*.yaml"))
    ad_files = sorted((root / "validation" / "adblock").glob("*.yaml"))
    module_files = sorted((root / "validation" / "modules").glob("*.yaml"))
    real_device = [p for p in device_files if "TEMPLATE" not in p.name]
    real_ad = [p for p in ad_files if "TEMPLATE" not in p.name]
    real_modules = [p for p in module_files if "TEMPLATE" not in p.name]

    field_report = audit.get("field_validation") or {}
    missing_evidence = set(field_report.get("missing_evidence", []))
    field_records_ok = bool(field_report.get("ok"))

    def evidence_gate(name: str) -> bool | None:
        if name in missing_evidence:
            return None
        return field_records_ok

    gates = {
        "behavior_lock": bool(audit["behavior_lock"] and audit["behavior_lock"].get("ok")),
        "dns_audit": bool(audit["dns_audit"] and audit["dns_audit"].get("ok")),
        "offline_regression": bool(audit["regression_offline"] and audit["regression_offline"].get("ok")),
        "cache_refresh": bool(audit["cache_refresh"] and audit["cache_refresh"].get("ok")) if audit["cache_refresh"] else None,
        "online_regression": bool(audit["regression_online"] and audit["regression_online"].get("ok")) if audit["regression_online"] else None,
        "remote_audit": bool(audit["remote_audit"] and audit["remote_audit"].get("ok")) if audit["remote_audit"] else None,
        "ruleset_drift": bool(audit["ruleset_drift"] and audit["ruleset_drift"].get("ok")) if audit["ruleset_drift"] else None,
        "adblock_collisions": bool(audit["adblock_collisions"] and audit["adblock_collisions"].get("ok")) if audit["adblock_collisions"] else None,
        "service_health": bool(audit["service_health"] and audit["service_health"].get("ok")) if audit["service_health"] else None,
        "network_benchmark": bool(audit["network_benchmark"] and audit["network_benchmark"].get("ok")) if audit["network_benchmark"] else None,
        "rule_conflicts": bool((audit["rule_conflicts_online"] or audit["rule_conflicts_offline"]) and (audit["rule_conflicts_online"] or audit["rule_conflicts_offline"]).get("ok")),
        "modular_equivalence": bool((audit["modular_equivalence_online"] or audit["modular_equivalence_offline"]) and (audit["modular_equivalence_online"] or audit["modular_equivalence_offline"]).get("ok")),
        "wifi_record": evidence_gate("wifi"),
        "cellular_record": evidence_gate("cellular"),
        "switching_record": evidence_gate("switching"),
        "adblock_observation": evidence_gate("adblock-72h"),
        "apple_weather_module": evidence_gate("module:apple-weather-qweather"),
        "icloud_ai_routing": evidence_gate("module:icloud-ai-routing"),
    }

    mandatory_static = ["behavior_lock", "dns_audit", "offline_regression", "rule_conflicts", "modular_equivalence"]
    automation_ok = all(gates[key] is True for key in mandatory_static)
    module_gate_names = ["apple_weather_module", "icloud_ai_routing"]
    module_values = [gates[key] for key in module_gate_names]
    modules_ready = False if any(value is False for value in module_values) else (True if all(value is True for value in module_values) else None)

    required_release_gates = (
        "cache_refresh", "online_regression", "remote_audit", "ruleset_drift", "adblock_collisions",
        "service_health", "network_benchmark", "wifi_record", "cellular_record", "switching_record",
        "adblock_observation", *module_gate_names,
    )
    release_values = [gates[key] for key in required_release_gates]
    release_ready = False if any(value is False for value in release_values) else (
        True if automation_ok and all(value is True for value in release_values) else None
    )

    source_branch = (
        os.getenv("GITHUB_HEAD_REF")
        or os.getenv("GITHUB_REF_NAME")
        or git_value(repo, "branch", "--show-current")
    )
    payload = {
        "schema": 2,
        "version": version,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit": git_value(repo, "rev-parse", "HEAD"),
        "source_branch": source_branch or "unknown",
        "automation_ok": automation_ok,
        "modules_ready": modules_ready,
        "release_ready": release_ready,
        "gates": gates,
        "missing_evidence": sorted(missing_evidence),
        "artifacts": configs,
        "reports": {key: value for key, value in audit.items() if value is not None},
        "device_records": [str(p.relative_to(root)) for p in real_device],
        "adblock_records": [str(p.relative_to(root)) for p in real_ad],
        "module_records": [str(p.relative_to(root)) for p in real_modules],
        "note": f"{release_label} remains pending until current-version network, 72-hour advertising, Apple Weather and iCloud layered-routing validation records are complete.",
    }
    json_out = root / args.json_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = "\n".join(f"| {key} | {mark(value)} |" for key, value in gates.items())
    artifacts = "\n".join(f"- `{item['path']}` — `{item['sha256']}`" for item in configs) or "- 尚未生成"
    missing_rows = "\n".join(f"- `{item}`" for item in sorted(missing_evidence)) or "- 无"
    markdown = f"""# LOWERTOP Enterprise {version} 发布验证报告

> 自动化测试与真实设备证据分开计算；旧版本记录不能证明 {release_label} 新模块有效。

## 结论

- 自动化基线：**{mark(automation_ok)}**
- RC4 模块实机验证：**{mark(modules_ready)}**
- {release_label} 可发布：**{mark(release_ready)}**
- Source commit：`{payload['source_commit']}`
- Source branch：`{payload['source_branch']}`

## 发布闸门

| 闸门 | 状态 |
|---|---|
{rows}

## 构建产物

{artifacts}

## 尚缺证据

{missing_rows}

## 必须完成的真实设备验证

1. 使用 {release_label} 主配置完成 Wi-Fi、蜂窝及双向网络切换记录。
2. 使用 {release_label} 配置完成连续至少 72 小时广告误杀观察。
3. 验证 Apple 天气模块并提交对应记录，覆盖当前、小时、每日、降水、空气质量、定位与小组件。
4. 验证 iCloud Drive、照片、备份、CloudKit、iWork 与 Apple Account 均命中 DIRECT，同时专用代理 mask 端点命中 AI。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 与核心路由继承既有基线，RC4 对最终规范化配置建立独立行为锁。
- Apple Weather 不会自动注入 Direct 主配置，可单独禁用和回滚。
- iCloud 分层路由会进入 Direct 主配置但不加入 MITM；发布前必须完成同步直连与专用代理 AI 的独立实机记录。
- Bilibili Next 与 BaiduNetdisk Next 保持独立实验分支，不计入 RC4 发布闸门。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优及 IPv6/ECH 不进入 RC4 默认配置。
"""
    (root / args.markdown_out).write_text(markdown, encoding="utf-8")
    print(json.dumps({
        "ok": automation_ok,
        "modules_ready": modules_ready,
        "release_ready": release_ready,
        "json": str(json_out),
        "markdown": str(root / args.markdown_out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
