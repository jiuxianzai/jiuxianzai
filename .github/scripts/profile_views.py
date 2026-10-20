#!/usr/bin/env python3
"""抓取个人资料访问量并渲染成本地静态 SVG。

GitHub 渲染 README 时会经 camo 代理抓第三方图片，komarev 源站响应太慢会被判为抓取失败
（表现为 404 破图），所以这里改成把数字抓下来自己出图，README 只引用 raw.githubusercontent.com。
"""

import re
import sys
import time
import urllib.request
from pathlib import Path

USERNAME = "jiuxianzai"
SOURCE = f"https://komarev.com/ghpvc/?username={USERNAME}"
OUTPUT = Path("dist/profile-views.svg")

LABEL = "Profile Views"
COLOR = "#0071e3"

# 近似 DejaVu Sans 11px 的字宽，用于估算数字区宽度
DIGIT_WIDTH = 7.0


def fetch_views(attempts: int = 4) -> int:
    last_error: Exception | None = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(
                SOURCE,
                headers={"User-Agent": "profile-views-badge/1.0"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", "replace")
            # 只取 <text> 节点里的纯数字，避免误匹配 width/height 等属性值
            numbers = re.findall(r">\s*(\d{1,9})\s*<", body)
            if not numbers:
                raise ValueError("响应里找不到计数数字")
            return int(numbers[-1])
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"第 {i + 1} 次抓取失败: {exc}", file=sys.stderr)
            if i < attempts - 1:
                time.sleep(5 * (i + 1))
    raise SystemExit(f"抓取访问量失败，不做更新（保留上一次的数字）: {last_error}")


def render(views: int) -> str:
    value = str(views)
    label_w = 84
    value_w = max(24, int(8 + DIGIT_WIDTH * len(value)))
    total_w = label_w + value_w
    label_cx = label_w / 2
    value_cx = label_w + value_w / 2

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{LABEL}: {value}">
    <title>{LABEL}: {value}</title>
    <linearGradient id="s" x2="0" y2="100%">
        <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
        <stop offset="1" stop-opacity=".1"/>
    </linearGradient>
    <clipPath id="r">
        <rect width="{total_w}" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#r)">
        <rect width="{label_w}" height="20" fill="#555"/>
        <rect x="{label_w}" width="{value_w}" height="20" fill="{COLOR}"/>
        <rect width="{total_w}" height="20" fill="url(#s)"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
        <text x="{label_cx}" y="15" fill="#010101" fill-opacity=".3">{LABEL}</text>
        <text x="{label_cx}" y="14">{LABEL}</text>
        <text x="{value_cx}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
        <text x="{value_cx}" y="14">{value}</text>
    </g>
</svg>
"""


def main() -> None:
    views = fetch_views()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(views), encoding="utf-8")
    print(f"访问量 {views} -> {OUTPUT}")


if __name__ == "__main__":
    main()
