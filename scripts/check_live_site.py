#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check whether the public Netlify site is usable for regular visitors."""

from __future__ import annotations

import os
import sys

import requests


DEFAULT_URL = "https://fanciful-unicorn-343425.netlify.app"
SITE_URL = os.environ.get("SITE_URL", DEFAULT_URL).rstrip("/")
TIMEOUT = 20


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    print(f"Checking live site: {SITE_URL}")
    try:
        response = requests.get(SITE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        fail(f"site request failed: {exc}")

    print(f"HTTP {response.status_code}")
    if response.status_code != 200:
        fail(f"expected HTTP 200, got {response.status_code}")

    html = response.text
    checks = {
        "not password protected": "Password Protection" not in html,
        "has sync status": "已同步到" in html,
        "has official source": "官方来源" in html,
        "has disclaimer": "数据来源与免责声明" in html and "不构成购彩建议" in html,
        "has lottery title": "双色球开奖查询与统计参考" in html,
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'FAIL'} {name}")
    if failed:
        fail("live site content check failed: " + ", ".join(failed))

    print("Live site check passed.")


if __name__ == "__main__":
    sys.exit(main())

