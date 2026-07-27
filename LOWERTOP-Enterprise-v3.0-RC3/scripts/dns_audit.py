#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import re
from urllib.parse import urlsplit

try:
    from .common import load_yaml
except ImportError:
    from common import load_yaml


def parse_general(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    section = None
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line
            continue
        if section == '[General]' and '=' in line:
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip()
    return values


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(',') if item.strip()]


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.lower()
    if lowered == 'true':
        return True
    if lowered == 'false':
        return False
    return None


def endpoint_url(item: str) -> str:
    # Shadowrocket modifiers are appended with #, while URL fragments are not used by DoH endpoints here.
    return item.split('#', 1)[0]


def audit_file(path: Path, profile_name: str, profile: dict, manifest: dict) -> dict:
    cfg = parse_general(path)
    policy = manifest.get('dns_audit', {})
    errors: list[str] = []
    warnings: list[str] = []

    for key in ('dns-server', 'fallback-dns-server', 'proxy-dns-server'):
        endpoints = split_csv(cfg.get(key, ''))
        if not endpoints:
            errors.append(f'{key} 缺失或为空')
            continue
        if policy.get('require_https_dns', True):
            for endpoint in endpoints:
                parsed = urlsplit(endpoint_url(endpoint))
                if parsed.scheme.lower() != 'https' or not parsed.netloc:
                    errors.append(f'{key} 存在非 HTTPS DoH：{endpoint}')

    if policy.get('require_proxy_tag_on_fallback', True):
        for endpoint in split_csv(cfg.get('fallback-dns-server', '')):
            if '#proxy' not in endpoint.lower():
                errors.append(f'fallback-dns-server 未通过代理发送：{endpoint}')

    for key in policy.get('required_false', []):
        if parse_bool(cfg.get(key)) is not False:
            errors.append(f'{key} 必须为 false，当前为 {cfg.get(key)!r}')

    release_profiles = set(policy.get('release_profiles', []))
    experimental_profiles = set(policy.get('experimental_profiles', []))
    ipv6 = parse_bool(cfg.get('ipv6'))
    prefer_ipv6 = parse_bool(cfg.get('prefer-ipv6'))
    if profile_name in release_profiles:
        if ipv6 is not policy.get('release_ipv6', False):
            errors.append(f'发布配置 ipv6 必须为 {str(policy.get("release_ipv6", False)).lower()}')
        if prefer_ipv6 is not False:
            errors.append('发布配置 prefer-ipv6 必须为 false')
    elif profile_name in experimental_profiles:
        if ipv6 is not True:
            errors.append('IPv6 实验配置必须明确 ipv6=true')
        if parse_bool(cfg.get('allow-dns-svcb')) is not True:
            errors.append('IPv6/SVCB 实验配置必须 allow-dns-svcb=true')

    expected_udp = str(policy.get('udp_unsupported_behavior', 'REJECT'))
    if cfg.get('udp-policy-not-supported-behaviour') != expected_udp:
        errors.append(
            'udp-policy-not-supported-behaviour 必须为 '
            f'{expected_udp}，当前为 {cfg.get("udp-policy-not-supported-behaviour")!r}'
        )

    hijack = set(split_csv(cfg.get('hijack-dns', '')))
    missing_hijack = [item for item in policy.get('required_hijack', []) if item not in hijack]
    if missing_hijack:
        errors.append(f'hijack-dns 缺少：{missing_hijack}')

    expected_quic = profile.get('block-quic')
    if expected_quic and cfg.get('block-quic') != expected_quic:
        errors.append(f'block-quic 应为 {expected_quic}，当前为 {cfg.get("block-quic")!r}')

    if cfg.get('private-ip-answer', '').lower() != 'true':
        warnings.append('private-ip-answer 未设置为 true，局域网域名解析可能受影响')

    return {
        'file': str(path),
        'profile': profile_name,
        'ok': not errors,
        'errors': errors,
        'warnings': warnings,
        'observed': {
            'dns-server': cfg.get('dns-server'),
            'fallback-dns-server': cfg.get('fallback-dns-server'),
            'proxy-dns-server': cfg.get('proxy-dns-server'),
            'ipv6': cfg.get('ipv6'),
            'prefer-ipv6': cfg.get('prefer-ipv6'),
            'allow-dns-svcb': cfg.get('allow-dns-svcb'),
            'block-quic': cfg.get('block-quic'),
            'udp-policy-not-supported-behaviour': cfg.get('udp-policy-not-supported-behaviour'),
        },
    }


def artifact_label(meta: dict) -> str:
    version = str(meta.get("version", "3.0.0"))
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-(.+))?", version)
    if not match:
        return "v3.0"
    major, minor, _patch, suffix = match.groups()
    label = f"v{major}.{minor}"
    if suffix:
        label += "-" + suffix.upper()
    return label


def expected_filename(meta: dict, profile: dict) -> str:
    return f'LOWERTOP-Enterprise-{artifact_label(meta)}-{profile["title"]}-Direct.conf'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--build-dir', default='build')
    parser.add_argument('--experimental-dir', default='experimental')
    parser.add_argument('--json-out', default='reports/dns-audit.json')
    parser.add_argument('--profiles', nargs='*')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest = load_yaml(root / 'manifest.yaml')
    wanted = set(args.profiles or manifest['profiles'].keys())
    results = []
    for name, profile in manifest['profiles'].items():
        if name not in wanted:
            continue
        directory = root / (args.build_dir if profile.get('release', True) else args.experimental_dir)
        path = directory / expected_filename(manifest["meta"], profile)
        if not path.exists():
            results.append({'file': str(path), 'profile': name, 'ok': False, 'errors': ['生成配置不存在'], 'warnings': []})
            continue
        results.append(audit_file(path, name, profile, manifest))

    failures = [item for item in results if not item['ok']]
    report = {
        'ok': not failures,
        'version': manifest['meta']['version'],
        'summary': {
            'checked': len(results),
            'passed': len(results) - len(failures),
            'failed': len(failures),
            'warnings': sum(len(item.get('warnings', [])) for item in results),
        },
        'results': results,
        'failures': failures,
        'scope_note': '静态审计可阻止系统 DNS 回退、明文 DNS 和 IPv6 主力配置旁路；真实运营商、路由器与 WebRTC 泄漏仍需设备侧验证。',
    }
    out = root / args.json_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['ok'] else 1)


if __name__ == '__main__':
    main()
