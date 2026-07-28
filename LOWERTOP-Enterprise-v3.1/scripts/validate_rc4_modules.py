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


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    weather_path = project / "modules" / "optional" / "AppleWeather.QWeather.RC4.sgmodule"
    weather = read(weather_path)

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
            fail(f"RC4 modules: possible credential detected: {match.group(0)[:24]}...")

    if 'API.QWeather.Token:""' not in weather:
        fail("Apple Weather module: QWeather token default must remain empty")

    print("RC4 module audit OK: Apple Weather module, local-only QWeather token")


if __name__ == "__main__":
    main()
