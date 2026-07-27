#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
import sys

try:
    from .common import load_yaml, parse_rule, read_rules
except ImportError:
    from common import load_yaml, parse_rule, read_rules

DOMAIN_KINDS = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}
IP_KINDS = {'IP-CIDR', 'IP-CIDR6'}


def cache_path(root: Path, cache_dir: str, name: str) -> Path:
    return root / cache_dir / f'{name}.list'


def collect_rules(root: Path, manifest: dict, cache_dir: str, names: list[str], local: bool) -> list[dict]:
    output = []
    source_items = manifest['local_rulesets'] if local else manifest['remote_rulesets']
    lookup = {item['name']: item for item in source_items}
    for name in names:
        item = lookup.get(name)
        if not item:
            raise ValueError(f'不存在的规则集：{name}')
        path = root / item['file'] if local else cache_path(root, cache_dir, name)
        if not path.exists():
            raise FileNotFoundError(f'缺少规则缓存：{path}，请先运行 remote_audit.py')
        for lineno, raw, parts in read_rules(path, allow_unknown=True):
            output.append({
                'ruleset': name,
                'policy': item['policy'],
                'stage': item['stage'],
                'line': lineno,
                'raw': raw,
                'parts': parts,
            })
    return output


def suffix_match(domain: str, suffix: str) -> bool:
    domain = domain.lower().strip('.')
    suffix = suffix.lower().strip('.')
    return domain == suffix or domain.endswith('.' + suffix)


def domain_overlap(a: list[str], b: list[str]) -> tuple[bool, str | None]:
    ka, va = a[0], a[1].lower()
    kb, vb = b[0], b[1].lower()
    if ka not in DOMAIN_KINDS or kb not in DOMAIN_KINDS:
        return False, None
    if ka == 'DOMAIN' and kb == 'DOMAIN':
        return va == vb, 'exact-domain' if va == vb else None
    if ka == 'DOMAIN' and kb == 'DOMAIN-SUFFIX':
        return suffix_match(va, vb), 'domain-in-suffix' if suffix_match(va, vb) else None
    if ka == 'DOMAIN-SUFFIX' and kb == 'DOMAIN':
        return suffix_match(vb, va), 'domain-in-suffix' if suffix_match(vb, va) else None
    if ka == 'DOMAIN-SUFFIX' and kb == 'DOMAIN-SUFFIX':
        hit = suffix_match(va, vb) or suffix_match(vb, va)
        return hit, 'suffix-overlap' if hit else None
    if ka == 'DOMAIN-KEYWORD' and kb == 'DOMAIN-KEYWORD':
        hit = va in vb or vb in va
        return hit, 'keyword-overlap' if hit else None
    if ka == 'DOMAIN-KEYWORD':
        hit = va in vb
        return hit, 'keyword-target' if hit else None
    if kb == 'DOMAIN-KEYWORD':
        hit = vb in va
        return hit, 'keyword-target' if hit else None
    return False, None


def ip_overlap(a: list[str], b: list[str]) -> tuple[bool, str | None]:
    if a[0] not in IP_KINDS or b[0] not in IP_KINDS:
        return False, None
    try:
        na = ipaddress.ip_network(a[1], strict=False)
        nb = ipaddress.ip_network(b[1], strict=False)
    except ValueError:
        return False, None
    if na.version != nb.version:
        return False, None
    hit = na.overlaps(nb)
    return hit, 'cidr-overlap' if hit else None


def overlap(a: list[str], b: list[str]) -> tuple[bool, str | None]:
    hit, reason = domain_overlap(a, b)
    if hit:
        return hit, reason
    return ip_overlap(a, b)


def severity(reason: str, critical_policy: str, blocking: set[str]) -> str:
    if critical_policy in blocking and reason in {'exact-domain', 'domain-in-suffix', 'cidr-overlap'}:
        return 'high'
    if reason in {'suffix-overlap', 'keyword-target'}:
        return 'medium'
    return 'low'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--cache-dir', default='.cache/remote-rules')
    parser.add_argument('--json-out', default='reports/adblock-collisions.json')
    parser.add_argument('--fail-on-high-risk', action='store_true')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = load_yaml(root / 'manifest.yaml')
    settings = manifest.get('adblock_audit', {})
    ad_name = settings.get('advertising_ruleset', 'AdvertisingLite')
    remote_lookup = {item['name']: item for item in manifest['remote_rulesets']}
    ad_item = remote_lookup[ad_name]
    ad_rules = collect_rules(root, manifest, args.cache_dir, [ad_name], local=False)
    critical = collect_rules(root, manifest, args.cache_dir, settings.get('critical_local_rulesets', []), local=True)
    critical += collect_rules(root, manifest, args.cache_dir, settings.get('critical_remote_rulesets', []), local=False)

    blocking = set(settings.get('blocking_policies', []))
    approved = set(settings.get('approved_overlaps', []))
    collisions = []
    for c in critical:
        for ad in ad_rules:
            hit, reason = overlap(c['parts'], ad['parts'])
            if not hit or not reason:
                continue
            key = f'{c["ruleset"]}:{c["raw"]}|{ad["ruleset"]}:{ad["raw"]}'
            item = {
                'key': key,
                'severity': severity(reason, c['policy'], blocking),
                'reason': reason,
                'approved': key in approved,
                'critical': {k: c[k] for k in ('ruleset', 'policy', 'stage', 'line', 'raw')},
                'advertising': {k: ad[k] for k in ('ruleset', 'policy', 'stage', 'line', 'raw')},
                'runtime_safe_by_order': c['stage'] < ad['stage'],
            }
            collisions.append(item)

    unsafe_order = [item for item in collisions if not item['runtime_safe_by_order']]
    high_risk = [item for item in collisions if item['severity'] == 'high' and not item['approved']]
    fail_on_order = settings.get('fail_on_unsafe_order', True)
    fail_on_high = args.fail_on_high_risk or settings.get('fail_on_high_risk_overlap', False)
    ok = not (fail_on_order and unsafe_order) and not (fail_on_high and high_risk)
    report = {
        'ok': ok,
        'version': manifest['meta']['version'],
        'advertising_ruleset': ad_name,
        'ad_stage': ad_item['stage'],
        'summary': {
            'critical_rules': len(critical),
            'advertising_rules': len(ad_rules),
            'collisions': len(collisions),
            'high_risk': len(high_risk),
            'unsafe_order': len(unsafe_order),
        },
        'collisions': collisions[:500],
        'high_risk': high_risk[:200],
        'unsafe_order': unsafe_order[:200],
        'policy_note': 'RC3 默认以规则顺序作为安全闸门：关键服务必须先于 AdvertisingLite。碰撞报告用于发现潜在误杀，不会因流媒体常见共享追踪域名自动阻断发布。',
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
