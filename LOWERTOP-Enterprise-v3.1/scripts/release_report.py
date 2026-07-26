#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess


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
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def mark(value: bool | None) -> str:
    return "PASS" if value is True else "FAIL" if value is False else "PENDING"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--json-out", default="reports/release-validation.json")
    parser.add_argument("--markdown-out", default="RELEASE-VALIDATION.md")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    repo = root.parents[1]
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
    real_device = [p for p in device_files if "TEMPLATE" not in p.name]
    real_ad = [p for p in ad_files if "TEMPLATE" not in p.name]
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
    }
    mandatory_static = ["behavior_lock", "dns_audit", "offline_regression", "rule_conflicts", "modular_equivalence"]
    automation_ok = all(gates[key] is True for key in mandatory_static)
    required_release_gates = (
        "cache_refresh", "online_regression", "remote_audit", "ruleset_drift", "adblock_collisions",
        "service_health", "network_benchmark", "wifi_record", "cellular_record", "switching_record", "adblock_observation"
    )
    release_values = [gates[key] for key in required_release_gates]
    release_ready = False if any(value is False for value in release_values) else (True if automation_ok and all(value is True for value in release_values) else None)
    payload = {
        "schema": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_commit": git_value(repo, "rev-parse", "HEAD"), "source_branch": git_value(repo, "branch", "--show-current"),
        "automation_ok": automation_ok, "release_ready": release_ready, "gates": gates, "artifacts": configs,
        "reports": {key: value for key, value in audit.items() if value is not None},
        "device_records": [str(p.relative_to(root)) for p in real_device], "adblock_records": [str(p.relative_to(root)) for p in real_ad],
        "note": "release_ready remains false until real Wi-Fi/cellular/switching evidence and the 72-hour AdvertisingLite observation are committed.",
    }
    json_out = root / args.json_out
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(f"| {key} | {mark(value)} |" for key, value in gates.items())
    artifacts = "\n".join(f"- `{item['path']}` — `{item['sha256']}`" for item in configs) or "- 尚未生成"
    markdown = f"""# LOWERTOP Enterprise v3.1 RC2 发布验证报告

> 自动生成骨架；设备实测与 AdvertisingLite 观察必须由真实记录补齐，不能由 CI 代填。

## 结论

- 自动化基线：**{mark(automation_ok)}**
- RC2 可发布：**{mark(release_ready)}**
- Source commit：`{payload['source_commit']}`
- Source branch：`{payload['source_branch']}`

## 发布闸门

| 闸门 | 状态 |
|---|---|
{rows}

## 构建产物

{artifacts}

## 尚需真实设备完成

1. 家庭/办公 Wi-Fi 实测记录。
2. 蜂窝网络实测记录。
3. Wi-Fi → 蜂窝与蜂窝 → Wi-Fi 网络切换记录。
4. AdvertisingLite 连续 72 小时误杀观察和处理结论。

## 边界

- Performance 的 DNS、QUIC、IPv6、UDP 和路由行为受 RC1 行为锁保护。
- DoQ/DoH3/DoH/DoT 自动回退、动态 DNS 选优、IPv6/ECH 不进入 RC2 默认配置。
- Experimental 仅提供 IPv6/SVCB 验证，不宣称强制或确认 ECH。
"""
    (root / args.markdown_out).write_text(markdown, encoding="utf-8")
    print(json.dumps({"ok": automation_ok, "release_ready": release_ready, "json": str(json_out), "markdown": str(root / args.markdown_out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
