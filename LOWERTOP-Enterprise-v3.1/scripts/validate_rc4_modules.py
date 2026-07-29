#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"(?i)(?:api[_-]?key|token|secret|private[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b[a-f0-9]{32}\b", re.I),
)


def fail(message: str) -> None:
    raise SystemExit(message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing v3.1 module: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, values: tuple[str, ...], label: str) -> None:
    missing = [value for value in values if value not in text]
    if missing:
        fail(f"{label}: missing required markers: {', '.join(missing)}")


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    optional = project / "modules" / "optional"
    weather_path = project / "modules" / "optional" / "AppleWeather.QWeather.v3.1.sgmodule"
    private_relay_path = (
        project / "modules" / "optional" / "iCloud.PrivateRelay.Priority.v3.1.sgmodule"
    )
    weather = read(weather_path)
    private_relay = read(private_relay_path)

    require(
        weather,
        (
            "NSRingo/WeatherKit/releases/download/v3.1.0/response.bundle.js",
            'API.QWeather.Token:""',
            'API.QWeather.Token="{{{API.QWeather.Token}}}"',
            'Weather.Provider="{{{Weather.Provider}}}"',
            "hostname = %APPEND% weatherkit.apple.com",
        ),
        "Apple Weather module",
    )

    for pattern in SECRET_PATTERNS:
        match = pattern.search(weather)
        if match:
            fail(f"v3.1 modules: possible credential detected: {match.group(0)[:24]}...")

    if 'API.QWeather.Token:""' not in weather:
        fail("Apple Weather module: QWeather token default must remain empty")

    require(
        private_relay,
        (
            "#!name=iCloud 专用代理优先 v3.1",
            "DOMAIN,mask.icloud.com,AI",
            "DOMAIN,mask-h2.icloud.com,AI",
            "DOMAIN,mask-api.icloud.com,AI",
        ),
        "iCloud Private Relay priority module",
    )

    relay_rules = [
        line.strip()
        for line in private_relay.splitlines()
        if line.strip().startswith(("DOMAIN,", "DOMAIN-SUFFIX,", "RULE-SET,"))
    ]
    expected_relay_rules = [
        "DOMAIN,mask.icloud.com,AI",
        "DOMAIN,mask-h2.icloud.com,AI",
        "DOMAIN,mask-api.icloud.com,AI",
    ]
    if relay_rules != expected_relay_rules:
        fail("iCloud Private Relay priority module: rules must remain exact and ordered")
    if "[Script]" in private_relay or "[MITM]" in private_relay:
        fail("iCloud Private Relay priority module: script and MITM sections are forbidden")

    audited_specs = {
        "WeChat.OfficialAccounts.NoAds.v3.1.sgmodule": {
            "markers": (
                "NobyDa/Script/7f8b309f8d943806b90c6ff25d8b8aa0c59b0c03/",
                "微信公众号底部广告 = type=http-response",
            ),
            "hosts": ("mp.weixin.qq.com",),
        },
        "Weibo.NoAds.v3.1.sgmodule": {
            "markers": (
                "zmqcherish/proxy-script/1d9f51bc9a0077d81998bb503ee6158ca83faa73/",
                "微博信息流去广告 = type=http-response",
                "微博开屏去广告 = type=http-response",
            ),
            "hosts": (
                "api.weibo.cn",
                "mapi.weibo.com",
                "sdkapp.uve.weibo.com",
                "wbapp.uve.weibo.com",
            ),
        },
        "Netflix.Ratings.v3.1.sgmodule": {
            "markers": (
                "yichahucha/surge/06d6e36771880959c008d3c59c192068f00ddd51/",
                "Netflix 评分请求 = type=http-request",
                "Netflix 评分响应 = type=http-response",
                "Netflix 季度评分 = type=http-response",
            ),
            "hosts": ("ios.prod.ftl.netflix.com",),
        },
        "YouTube.NoAds.v3.1.sgmodule": {
            "markers": (
                "app2smile/rules/df6366a7024e0b3f0aa3510c5b791eea6f3cba89/",
                "YouTube 信息流广告 = type=http-response",
            ),
            "hosts": ("youtubei.googleapis.com",),
        },
    }

    for filename, spec in audited_specs.items():
        module = read(optional / filename)
        require(module, spec["markers"], filename)
        for mutable in ("/main/", "/master/", "/releases/latest/"):
            if mutable in module:
                fail(f"{filename}: mutable runtime URL is forbidden: {mutable}")
        for pattern in SECRET_PATTERNS:
            match = pattern.search(module)
            if match:
                fail(f"{filename}: possible credential detected: {match.group(0)[:24]}...")

        hostname_lines = [
            line.split("=", 1)[1].strip()
            for line in module.splitlines()
            if line.strip().lower().startswith("hostname")
        ]
        if len(hostname_lines) != 1 or "%APPEND%" not in hostname_lines[0]:
            fail(f"{filename}: exactly one additive MITM hostname line is required")
        hosts = tuple(
            item.strip()
            for item in hostname_lines[0].replace("%APPEND%", "").split(",")
            if item.strip()
        )
        if hosts != spec["hosts"]:
            fail(f"{filename}: MITM hostnames must remain exact and ordered")
        if any("*" in host for host in hosts):
            fail(f"{filename}: wildcard MITM hostnames are forbidden")

    print(
        "v3.1 module audit OK: Apple Weather local-only token; "
        "iCloud Private Relay exact priority rules; audited optional runtimes pinned"
    )


if __name__ == "__main__":
    main()
