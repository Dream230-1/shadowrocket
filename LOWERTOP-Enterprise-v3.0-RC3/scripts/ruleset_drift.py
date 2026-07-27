#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from .common import load_yaml
except ImportError:
    from common import load_yaml


def pct_change(old: int, new: int) -> float:
    if old == 0:
        return 0.0 if new == 0 else 100.0
    return round((new - old) * 100.0 / old, 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--current', default='reports/remote-audit.json')
    parser.add_argument('--json-out', default='reports/ruleset-drift.json')
    parser.add_argument('--fail-on-sha-change', action='store_true')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = load_yaml(root / 'manifest.yaml')
    settings = manifest.get('drift_audit', {})
    baseline_path = root / settings.get('baseline_file', 'baselines/remote-rules.json')
    current_path = root / args.current
    baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    current = json.loads(current_path.read_text(encoding='utf-8'))
    baseline_rules = baseline.get('rulesets', {})
    current_rules = {item['name']: item for item in current.get('results', [])}

    count_limit = float(settings.get('max_rule_count_change_percent', 15))
    byte_limit = float(settings.get('max_byte_change_percent', 20))
    results, failures, warnings = [], [], []
    for name, old in baseline_rules.items():
        now = current_rules.get(name)
        if not now:
            item = {'name': name, 'ok': False, 'error': '当前审计缺少该规则集'}
            results.append(item); failures.append(item); continue
        count_change = pct_change(int(old['rule_count']), int(now['rule_count']))
        byte_change = pct_change(int(old['bytes']), int(now['bytes']))
        sha_changed = old['sha256'] != now['sha256']
        errors = []
        item_warnings = []
        if abs(count_change) > count_limit:
            errors.append(f'规则数变化 {count_change}% 超过 ±{count_limit}%')
        if abs(byte_change) > byte_limit:
            errors.append(f'字节数变化 {byte_change}% 超过 ±{byte_limit}%')
        if sha_changed:
            message = 'SHA-256 已变化'
            if args.fail_on_sha_change or not settings.get('sha_change_is_warning', True):
                errors.append(message)
            else:
                item_warnings.append(message)
        item = {
            'name': name,
            'ok': not errors,
            'baseline': old,
            'current': {'sha256': now['sha256'], 'rule_count': now['rule_count'], 'bytes': now['bytes']},
            'rule_count_change_percent': count_change,
            'byte_change_percent': byte_change,
            'errors': errors,
            'warnings': item_warnings,
        }
        results.append(item)
        if errors: failures.append(item)
        if item_warnings: warnings.append(item)

    report = {
        'ok': not failures,
        'baseline_version': baseline.get('version'),
        'baseline_upstream_commit': baseline.get('upstream_commit'),
        'current_upstream_commit': current.get('upstream_commit'),
        'summary': {'checked': len(results), 'failed': len(failures), 'warnings': len(warnings)},
        'results': results,
        'failures': failures,
        'warnings': warnings,
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['ok'] else 1)


if __name__ == '__main__':
    main()
