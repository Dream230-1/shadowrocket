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
        fail(f"missing RC4 module: {path}")
    return path.read_text(encoding="utf-8")


def require(text: str, values: tuple[str, ...], label: str) -> None:
    missing = [value for value in values if value not in text]
    if missing:
        fail(f"{label}: missing required markers: {', '.join(missing)}")


def forbid(text: str, values: tuple[str, ...], label: str) -> None:
    hits = [value for value in values if value.lower() in text.lower()]
    if hits:
        fail(f"{label}: forbidden markers detected: {', '.join(hits)}")


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    bilibili_path = project / "modules" / "optional" / "Bilibili.ADBlock.RC4.sgmodule"
    baidu_path = project / "modules" / "experimental" / "BaiduNetdisk.AdBlock.Experimental.sgmodule"
    weather_path = project / "modules" / "optional" / "AppleWeather.QWeather.RC4.sgmodule"

    bilibili = read(bilibili_path)
    baidu = read(baidu_path)
    weather = read(weather_path)

    require(
        bilibili,
        (
            "BiliUniverse/ADBlock/releases/",
            "View/(View|TFInfo|RelatesFeed)",
            "Reply/MainList",
            "Dynamic/Dyn(All|Video)",
            "binary-body-mode=1",
            "hostname = %APPEND%",
        ),
        "Bilibili module",
    )
    forbid(
        bilibili,
        (
            "emptyJson",
            "vip.status",
            "due_date",
            "role: 15",
            "$done({response:",
        ),
        "Bilibili module",
    )

    require(
        baidu,
        (
            "/act\\/api\\/activityentry",
            "/act\\/v2\\/welfare\\/list",
            "/pcs\\/adv",
            "method=gamecenter",
            "hostname = %APPEND% pan.baidu.com",
        ),
        "Baidu Netdisk module",
    )
    forbid(
        baidu,
        (
            "DOMAIN-KEYWORD,baidu",
            "DOMAIN-SUFFIX,baidu.com",
            "svip",
            "vip_type",
            "api/user/getinfo",
            "video speed",
            "视频倍速",
        ),
        "Baidu Netdisk module",
    )

    require(
        weather,
        (
            "NSRingo/WeatherKit/releases/download/v3.1.0/response.bundle.js",
            'API.QWeather.Token:""',
            "API.QWeather.Token=\"{{{API.QWeather.Token}}}\"",
            "Weather.Provider=\"{{{Weather.Provider}}}\"",
            "hostname = %APPEND% weatherkit.apple.com",
        ),
        "Apple Weather module",
    )

    combined = "\n".join((bilibili, baidu, weather))
    for pattern in SECRET_PATTERNS:
        match = pattern.search(combined)
        if match:
            fail(f"RC4 modules: possible credential detected: {match.group(0)[:24]}...")

    if "API.QWeather.Token:\"\"" not in weather:
        fail("Apple Weather module: QWeather token default must remain empty")

    print("RC4 module audit OK: Bilibili structural filter, conservative Baidu module, local-only QWeather token")


if __name__ == "__main__":
    main()
