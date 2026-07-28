#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a self-contained双色球 dashboard.

The output HTML embeds its data, charts, and interactions so users can open it
by double-clicking. No CDN, server, or browser file-fetch permission is needed.
"""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from datetime import datetime
from statistics import mean


ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(ROOT, "ssq_data.json")
OUT_FILE = os.path.join(ROOT, "ssq_analyzer.html")


def load_records() -> list[dict[str, str]]:
    with open(DATA_FILE, "r", encoding="utf-8-sig") as file:
        records = json.load(file)
    records.sort(key=lambda item: item["Date"])
    return records


def red_numbers(record: dict[str, str]) -> list[int]:
    return [int(value) for value in record["Red"].split(",")]


def number(value: int) -> str:
    return f"{value:02d}"


def build_bar_rows(items: list[dict[str, object]], max_count: int, theme: str) -> str:
    rows = []
    for item in items:
        count = int(item["count"])
        width = round(count / max_count * 100, 2)
        tag = html.escape(str(item.get("tag", "")))
        tag_html = f'<span class="tag">{tag}</span>' if tag else ""
        state = html.escape(str(item.get("state", "normal")))
        rows.append(
            f"""
            <div class="bar-row {theme} {state}">
              <div class="ball">{number(int(item["num"]))}</div>
              <div class="bar-track"><div class="bar-fill" style="width:{width}%"></div></div>
              <div class="bar-value">{count}次{tag_html}</div>
            </div>
            """
        )
    return "\n".join(rows)


def build_sum_distribution(sum_counts: Counter[int]) -> str:
    max_count = max(sum_counts.values())
    rows = []
    for bucket in sorted(sum_counts):
        count = sum_counts[bucket]
        width = round(count / max_count * 100, 2)
        rows.append(
            f"""
            <div class="dist-row">
              <div class="dist-label">{bucket}-{bucket + 9}</div>
              <div class="dist-track"><div class="dist-fill" style="width:{width}%"></div></div>
              <div class="dist-value">{count}期</div>
            </div>
            """
        )
    return "\n".join(rows)


def build_trend_svg(recent: list[dict[str, object]]) -> str:
    width = 920
    height = 270
    left = 46
    right = 18
    top = 20
    bottom = 38
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [int(item["sum"]) for item in recent]
    min_value = min(values) - 8
    max_value = max(values) + 8
    span = max_value - min_value or 1

    def point(index: int, value: int) -> tuple[float, float]:
        x = left + index / max(1, len(recent) - 1) * plot_width
        y = top + (max_value - value) / span * plot_height
        return x, y

    path = " ".join(
        ("M" if index == 0 else "L") + f"{point(index, value)[0]:.1f},{point(index, value)[1]:.1f}"
        for index, value in enumerate(values)
    )
    avg_y = top + (max_value - 102) / span * plot_height
    dots = []
    labels = []
    for index, item in enumerate(recent):
        x, y = point(index, int(item["sum"]))
        dots.append(
            f'<circle class="trend-dot" cx="{x:.1f}" cy="{y:.1f}" r="3">'
            f'<title>{html.escape(str(item["issue"]))}期 {html.escape(str(item["date"]))} 和值 {item["sum"]}</title>'
            "</circle>"
        )
        if index % 12 == 0 or index == len(recent) - 1:
            labels.append(f'<text class="axis-label" x="{x:.1f}" y="{height - 10}" text-anchor="middle">{html.escape(str(item["date"]))}</text>')

    grid = []
    for step in range(5):
        value = round(min_value + (max_value - min_value) * step / 4)
        y = top + (max_value - value) / span * plot_height
        grid.append(f'<line class="grid-line" x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}"></line>')
        grid.append(f'<text class="axis-label" x="{left - 10}" y="{y + 4:.1f}" text-anchor="end">{value}</text>')

    return f"""
    <svg class="trend-svg" viewBox="0 0 {width} {height}" role="img" aria-label="近100期红球和值走势">
      <g>{''.join(grid)}</g>
      <line class="avg-line" x1="{left}" y1="{avg_y:.1f}" x2="{width - right}" y2="{avg_y:.1f}"></line>
      <text class="avg-label" x="{width - right - 6}" y="{avg_y - 8:.1f}" text-anchor="end">均值 102</text>
      <path class="trend-path" d="{path}"></path>
      {''.join(dots)}
      {''.join(labels)}
    </svg>
    """


def main() -> None:
    records = load_records()
    total = len(records)
    latest = records[-1]
    data_modified = datetime.fromtimestamp(os.path.getmtime(DATA_FILE)).strftime("%Y-%m-%d %H:%M")
    red_counter: Counter[int] = Counter()
    blue_counter: Counter[int] = Counter()
    sum_counter: Counter[int] = Counter()
    pair_counter: Counter[str] = Counter()
    zone_counter = Counter({"front": 0, "middle": 0, "back": 0})

    enriched = []
    for record in records:
        reds = red_numbers(record)
        red_sum = sum(reds)
        for red in reds:
            red_counter[red] += 1
            if red <= 11:
                zone_counter["front"] += 1
            elif red <= 22:
                zone_counter["middle"] += 1
            else:
                zone_counter["back"] += 1
        blue_counter[int(record["Blue"])] += 1
        sum_counter[red_sum // 10 * 10] += 1
        for left, right in zip(reds, reds[1:]):
            if right - left == 1:
                pair_counter[f"{number(left)}-{number(right)}"] += 1
        enriched.append({**record, "RedSum": red_sum})

    red_avg = total * 6 / 33
    blue_avg = total / 16
    red_items = []
    for num in range(1, 34):
        count = red_counter[num]
        if count >= red_avg + 25:
            tag = "偏热"
            state = "hot"
        elif count <= red_avg - 25:
            tag = "偏冷"
            state = "cold"
        else:
            tag = ""
            state = "normal"
        red_items.append({"num": num, "count": count, "tag": tag, "state": state})

    blue_items = []
    for num in range(1, 17):
        count = blue_counter[num]
        if count >= blue_avg + 12:
            tag = "偏热"
            state = "hot"
        elif count <= blue_avg - 12:
            tag = "偏冷"
            state = "cold"
        else:
            tag = ""
            state = "normal"
        blue_items.append({"num": num, "count": count, "tag": tag, "state": state})

    hot_reds = sorted(red_items, key=lambda item: item["count"], reverse=True)[:6]
    cold_reds = sorted(red_items, key=lambda item: item["count"])[:6]
    hot_blues = sorted(blue_items, key=lambda item: item["count"], reverse=True)[:4]
    cold_blues = sorted(blue_items, key=lambda item: item["count"])[:4]
    recent = enriched[-100:]
    recent_table = list(reversed(enriched[-30:]))
    data_json = json.dumps(
        {
            "records": enriched,
            "total": total,
            "latest": latest,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )

    red_rows = build_bar_rows(red_items, max(item["count"] for item in red_items), "warm")
    blue_rows = build_bar_rows(blue_items, max(item["count"] for item in blue_items), "cool")
    sum_rows = build_sum_distribution(sum_counter)
    trend_svg = build_trend_svg(
        [{"issue": item["Issue"], "date": item["Date"][5:], "sum": item["RedSum"]} for item in recent]
    )
    pair_cards = "\n".join(
        f"""
        <div class="pair-card">
          <span class="pair-balls">{pair}</span>
          <span class="pair-count">{count}次</span>
        </div>
        """
        for pair, count in pair_counter.most_common(10)
    )
    latest_balls = "".join(f'<span class="red-ball">{value}</span>' for value in latest["Red"].split(","))
    latest_blue = f'<span class="blue-ball">{latest["Blue"]}</span>'
    update_hint = "本页面已同步到最新官方开奖日期；若官方未更新，则不会重复刷新。"
    table_rows = "\n".join(
        f"""
        <tr>
          <td>{html.escape(item["Issue"])}</td>
          <td>{html.escape(item["Date"])}</td>
          <td class="balls-cell">{''.join(f'<span class="red-ball">{value}</span>' for value in item["Red"].split(","))}</td>
          <td><span class="blue-ball">{html.escape(item["Blue"])}</span></td>
          <td>{item["RedSum"]}</td>
        </tr>
        """
        for item in recent_table
    )
    hot_red_text = "、".join(number(int(item["num"])) for item in hot_reds)
    cold_red_text = "、".join(number(int(item["num"])) for item in cold_reds)
    hot_blue_text = "、".join(number(int(item["num"])) for item in hot_blues)
    cold_blue_text = "、".join(number(int(item["num"])) for item in cold_blues)
    sums = [item["RedSum"] for item in enriched]
    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>双色球历史数据分析工具</title>
  <style>
    :root {{
      --page: #f7f8fb;
      --ink: #1c2430;
      --muted: #667085;
      --line: #e3e7ee;
      --panel: #ffffff;
      --orange-1: #e86f18;
      --orange-2: #d94a16;
      --orange-3: #f7a441;
      --orange-soft: #f4c2a5;
      --blue-1: #1f7ae0;
      --blue-2: #1254b8;
      --blue-soft: #b9d3f4;
      --ok: #16a34a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
      background: var(--page);
      color: var(--ink);
    }}
    .shell {{ max-width: 1240px; margin: 0 auto; padding: 22px; }}
    .topbar {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: center;
      margin-bottom: 18px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; font-weight: 700; }}
    .subtitle {{ margin: 0; color: var(--muted); }}
    .latest {{
      min-width: 360px;
      background: linear-gradient(135deg, #fff7ef, #eef6ff);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
    }}
    .latest-title {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
    .latest-row {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .status-card {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 0 0 16px;
    }}
    .status-item {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .status-label {{ color: var(--muted); font-size: 12px; margin-bottom: 5px; }}
    .status-value {{ font-weight: 800; }}
    .status-help {{ color: var(--muted); font-size: 13px; line-height: 1.6; }}
    .red-ball, .blue-ball {{
      display: inline-flex;
      width: 30px;
      height: 30px;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      color: #fff;
      font-size: 13px;
      font-weight: 700;
      box-shadow: inset 0 -2px 5px rgba(0,0,0,.18);
    }}
    .red-ball {{ background: linear-gradient(135deg, var(--orange-1), var(--orange-2)); }}
    .blue-ball {{ background: linear-gradient(135deg, var(--blue-1), var(--blue-2)); }}
    .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 20px; }}
    .tab {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--muted);
      padding: 9px 14px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
    }}
    .tab.active {{ color: #fffaf4; background: var(--orange-1); border-color: var(--orange-1); box-shadow: 0 0 0 3px rgba(232,111,24,.12); }}
    .section {{ display: none; }}
    .section.active {{ display: block; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px;
    }}
    .metric-label {{ color: var(--muted); font-size: 13px; margin-bottom: 6px; }}
    .metric-value {{ font-size: 24px; font-weight: 800; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .panel h2 {{ margin: 0 0 14px; font-size: 18px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
    .bar-list {{ display: grid; gap: 8px; }}
    .bar-row {{
      display: grid;
      grid-template-columns: 48px minmax(120px, 1fr) 112px;
      gap: 12px;
      align-items: center;
      min-height: 42px;
    }}
    .ball {{
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: 50%;
      color: #fff;
      font-weight: 800;
      font-size: 13px;
      border: 2px solid rgba(255,255,255,.88);
      box-shadow: 0 4px 12px rgba(20, 28, 40, .14);
    }}
    .warm.hot .ball {{
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #f26a21 0%, #d94a16 72%, #f7a441 100%);
      box-shadow: 0 5px 14px rgba(232, 111, 24, .24);
    }}
    .warm.cold .ball {{
      background: linear-gradient(135deg, #f4c2a5 0%, #df9c7b 100%);
      color: #653326;
      border-color: #f8d8c5;
      box-shadow: 0 4px 10px rgba(120, 72, 58, .12);
    }}
    .warm.normal .ball {{
      background: linear-gradient(135deg, #ee7b2a 0%, #dc5a18 100%);
    }}
    .cool.hot .ball {{
      width: 40px;
      height: 40px;
      background: linear-gradient(135deg, #66b4ff 0%, #1f7ae0 70%, #1254b8 100%);
      box-shadow: 0 5px 14px rgba(31, 122, 224, .24);
    }}
    .cool.cold .ball {{
      background: linear-gradient(135deg, #b9d3f4 0%, #7fa9dc 100%);
      color: #173b67;
      border-color: #d6e5f7;
      box-shadow: 0 4px 10px rgba(31, 122, 224, .12);
    }}
    .cool.normal .ball {{
      background: linear-gradient(135deg, #2f80ed 0%, #1f7ae0 100%);
    }}
    .bar-track {{
      height: 18px;
      background: #edf1f6;
      border-radius: 99px;
      overflow: hidden;
      border: 1px solid #e1e6ef;
    }}
    .bar-fill {{ height: 100%; border-radius: 99px; }}
    .warm.hot .bar-fill {{ background: linear-gradient(90deg, #f7a441, #e86f18, #d94a16); }}
    .warm.cold .bar-fill {{ background: linear-gradient(90deg, #f8d8c5, #f4c2a5, #df9c7b); }}
    .warm.normal .bar-fill {{ background: linear-gradient(90deg, #f7b15b, #e86f18); }}
    .cool.hot .bar-fill {{ background: linear-gradient(90deg, #66b4ff, #1f7ae0, #1254b8); }}
    .cool.cold .bar-fill {{ background: linear-gradient(90deg, #d6e5f7, #b9d3f4, #7fa9dc); }}
    .cool.normal .bar-fill {{ background: linear-gradient(90deg, #7bbcff, #1f7ae0); }}
    .bar-value {{ color: var(--muted); font-size: 13px; text-align: right; white-space: nowrap; }}
    .tag {{
      display: inline-block;
      margin-left: 6px;
      padding: 1px 6px;
      border-radius: 999px;
      color: var(--ink);
      background: #f2f4f8;
      font-weight: 700;
      font-size: 12px;
    }}
    .hot .tag {{ background: #fff0d6; color: #9a3c00; }}
    .cold .tag {{ background: #f5ddd5; color: #7a3e31; }}
    .cool.cold .tag {{ background: #dde5ff; color: #203071; }}
    .trend-svg {{ width: 100%; height: auto; display: block; }}
    .grid-line {{ stroke: #e7ebf2; stroke-width: 1; }}
    .avg-line {{ stroke: #f59e0b; stroke-width: 2; stroke-dasharray: 7 6; }}
    .avg-label, .axis-label {{ fill: var(--muted); font-size: 12px; }}
    .trend-path {{ fill: none; stroke: var(--orange-1); stroke-width: 3; }}
    .trend-dot {{ fill: var(--orange-2); stroke: #fff; stroke-width: 2; }}
    .dist-row {{
      display: grid;
      grid-template-columns: 70px minmax(160px, 1fr) 70px;
      gap: 10px;
      align-items: center;
      margin: 8px 0;
    }}
    .dist-label, .dist-value {{ color: var(--muted); font-size: 13px; }}
    .dist-track {{ height: 16px; border-radius: 99px; background: #edf1f6; overflow: hidden; }}
    .dist-fill {{ height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--orange-3), var(--orange-1)); }}
    .pair-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }}
    .pair-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: linear-gradient(135deg, #fff8ed, #fff);
      display: flex;
      justify-content: space-between;
      gap: 10px;
    }}
    .pair-balls {{ font-weight: 800; color: var(--orange-1); }}
    .pair-count {{ color: var(--muted); }}
    .recommend {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }}
    .rec-card {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 16px;
      background: #fff;
    }}
    .rec-card strong {{ color: var(--ink); }}
    .rec-card p {{ margin: 8px 0 0; color: var(--muted); }}
    .search-row {{ display: grid; grid-template-columns: 180px 1fr auto; gap: 10px; margin-bottom: 12px; }}
    select, input, textarea, button {{
      font: inherit;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      background: #fff;
      color: var(--ink);
    }}
    textarea {{
      min-height: 148px;
      resize: vertical;
      width: 100%;
    }}
    button {{ cursor: pointer; background: var(--orange-1); color: #fffaf4; border: none; font-weight: 700; }}
    .button-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }}
    .secondary-btn {{ background: #eef2f7; color: var(--ink); border: 1px solid var(--line); }}
    .checker-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    .checker-actions {{
      display: grid;
      grid-template-columns: minmax(180px, 240px) 1fr auto;
      gap: 10px;
      margin-bottom: 12px;
    }}
    .result-list {{ display: grid; gap: 10px; margin-top: 12px; }}
    .result-card {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: #fff;
    }}
    .result-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    .prize {{
      color: #a23b00;
      background: #fff0d6;
      border-radius: 999px;
      padding: 3px 9px;
      font-weight: 800;
    }}
    .miss {{ color: var(--muted); background: #f2f4f8; }}
    .hit-red {{ outline: 3px solid rgba(232, 111, 24, .34); }}
    .hit-blue {{ outline: 3px solid rgba(31, 122, 224, .34); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ color: var(--muted); font-weight: 700; background: #fafbfc; }}
    .balls-cell {{ min-width: 220px; }}
    .note {{ color: var(--muted); font-size: 13px; margin-top: 10px; }}
    @media (max-width: 880px) {{
      .topbar, .two-col, .recommend, .summary-grid, .checker-grid, .status-card {{ grid-template-columns: 1fr; }}
      .latest {{ min-width: 0; }}
      .pair-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .search-row, .checker-actions {{ grid-template-columns: 1fr; }}
      .shell {{ padding: 14px; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div>
        <h1>双色球开奖查询与统计参考</h1>
        <p class="subtitle">历史开奖、中奖核验、号码分布，一页查看。仅基于历史数据整理，不预测开奖结果。</p>
      </div>
      <aside class="latest">
        <div class="latest-title">最新开奖 {html.escape(latest["Issue"])}期 · {html.escape(latest["Date"])}</div>
        <div class="latest-row">{latest_balls}{latest_blue}</div>
      </aside>
    </header>

    <section class="status-card" aria-label="数据状态">
      <div class="status-item">
        <div class="status-label">最新期号</div>
        <div class="status-value">{html.escape(latest["Issue"])}期 · {html.escape(latest["Date"])}</div>
      </div>
      <div class="status-item">
        <div class="status-label">页面更新时间</div>
        <div class="status-value">{html.escape(data_modified)}</div>
      </div>
      <div class="status-item">
        <div class="status-label">同步说明</div>
        <div class="status-help">{html.escape(update_hint)}</div>
      </div>
    </section>

    <nav class="tabs" aria-label="功能切换">
      <button class="tab active" data-tab="history" type="button">历史查询</button>
      <button class="tab" data-tab="checker" type="button">中奖核验</button>
      <button class="tab" data-tab="overview" type="button">数据总览</button>
      <button class="tab" data-tab="red" type="button">红球统计</button>
      <button class="tab" data-tab="blue" type="button">蓝球统计</button>
      <button class="tab" data-tab="trend" type="button">和值趋势</button>
      <button class="tab" data-tab="recommend" type="button">选号参考</button>
    </nav>

    <section id="history" class="section active">
      <div class="panel">
        <h2>历年开奖记录查询</h2>
        <div class="search-row">
          <select id="yearSelect" aria-label="按年份筛选"></select>
          <input id="issueInput" placeholder="输入期号，例如 26085" aria-label="按期号查询">
          <button id="resetBtn" type="button">显示最近30期</button>
        </div>
        <table>
          <thead><tr><th>期号</th><th>开奖日期</th><th>红球</th><th>蓝球</th><th>和值</th></tr></thead>
          <tbody id="historyBody">{table_rows}</tbody>
        </table>
        <div class="note" id="historyNote">当前显示最近30期。可按年份或期号查询。</div>
      </div>
    </section>

    <section id="checker" class="section">
      <div class="panel">
        <h2>中奖核验</h2>
        <div class="checker-actions">
          <select id="checkIssueSelect" aria-label="选择核验期号"></select>
          <input id="singleTicketInput" placeholder="输入号码：01 02 03 04 05 06 + 07" aria-label="单注号码">
          <button id="checkSingleBtn" type="button">核验单注</button>
        </div>
        <div class="button-row">
          <button id="fillExampleBtn" class="secondary-btn" type="button">填入示例号码</button>
          <button id="clearCheckBtn" class="secondary-btn" type="button">清空核验结果</button>
        </div>
        <div class="checker-grid">
          <div>
            <textarea id="batchTicketInput" aria-label="批量号码" placeholder="批量核验：每行一注，例如
01 02 03 04 05 06 + 07
08,09,10,11,12,13,14"></textarea>
            <div class="note">支持空格、逗号、加号等格式；每行识别前 6 个红球和第 7 个蓝球。</div>
            <button id="checkBatchBtn" type="button" style="margin-top:10px;">批量核验</button>
          </div>
          <div>
            <div class="note" id="drawInfo"></div>
            <div class="result-list" id="checkResults"></div>
          </div>
        </div>
      </div>
    </section>

    <section id="overview" class="section">
      <div class="summary-grid">
        <div class="metric"><div class="metric-label">统计期数</div><div class="metric-value">{total}</div></div>
        <div class="metric"><div class="metric-label">数据范围</div><div class="metric-value">{records[0]["Date"][:4]}-{records[-1]["Date"][:4]}</div></div>
        <div class="metric"><div class="metric-label">红球和值均值</div><div class="metric-value">{mean(sums):.1f}</div></div>
        <div class="metric"><div class="metric-label">常见和值区间</div><div class="metric-value">90-119</div></div>
      </div>
      <div class="two-col">
        <div class="panel"><h2>红球频率总览</h2><div class="bar-list">{red_rows}</div></div>
        <div class="panel"><h2>蓝球频率总览</h2><div class="bar-list">{blue_rows}</div></div>
      </div>
    </section>

    <section id="red" class="section">
      <div class="panel"><h2>红球出现频率</h2><div class="bar-list">{red_rows}</div></div>
    </section>

    <section id="blue" class="section">
      <div class="panel"><h2>蓝球出现频率</h2><div class="bar-list">{blue_rows}</div></div>
    </section>

    <section id="trend" class="section">
      <div class="panel"><h2>近100期红球和值走势</h2>{trend_svg}</div>
      <div class="panel"><h2>全历史和值分布</h2>{sum_rows}</div>
    </section>

    <section id="recommend" class="section">
      <div class="recommend">
        <div class="rec-card"><strong>红球高频号码</strong><p>{hot_red_text}</p></div>
        <div class="rec-card"><strong>红球低频号码</strong><p>{cold_red_text}</p></div>
        <div class="rec-card"><strong>蓝球高频号码</strong><p>{hot_blue_text}</p></div>
        <div class="rec-card"><strong>蓝球低频号码</strong><p>{cold_blue_text}</p></div>
      </div>
      <div class="panel"><h2>高频连号组合</h2><div class="pair-grid">{pair_cards}</div></div>
      <div class="panel">
        <h2>使用建议</h2>
        <p class="note">选号参考只用于整理历史分布：可关注红球三区均衡、奇偶接近 3:3 或 4:2，和值尽量落在历史密集区间。彩票是随机事件，请理性参与。</p>
      </div>
    </section>
  </main>

  <script>
    const APP_DATA = {data_json};
    const body = document.getElementById('historyBody');
    const note = document.getElementById('historyNote');
    const yearSelect = document.getElementById('yearSelect');
    const issueInput = document.getElementById('issueInput');
    const checkIssueSelect = document.getElementById('checkIssueSelect');
    const singleTicketInput = document.getElementById('singleTicketInput');
    const batchTicketInput = document.getElementById('batchTicketInput');
    const checkResults = document.getElementById('checkResults');
    const drawInfo = document.getElementById('drawInfo');
    const exampleTickets = [
      '01 02 03 04 05 06 + 07',
      '08 09 10 11 12 13 + 14',
      '06 09 13 17 24 28 + 15'
    ];

    function redBalls(red) {{
      return red.split(',').map(value => `<span class="red-ball">${{value}}</span>`).join('');
    }}

    function redBallsWithHits(red, hitSet) {{
      return red.split(',').map(value => {{
        const cls = hitSet && hitSet.has(Number(value)) ? 'red-ball hit-red' : 'red-ball';
        return `<span class="${{cls}}">${{value}}</span>`;
      }}).join('');
    }}

    function blueBallWithHit(value, isHit) {{
      return `<span class="${{isHit ? 'blue-ball hit-blue' : 'blue-ball'}}">${{value}}</span>`;
    }}

    function rowHtml(item) {{
      return `<tr><td>${{item.Issue}}</td><td>${{item.Date}}</td><td class="balls-cell">${{redBalls(item.Red)}}</td><td><span class="blue-ball">${{item.Blue}}</span></td><td>${{item.RedSum}}</td></tr>`;
    }}

    function renderRows(items, message) {{
      body.innerHTML = items.map(rowHtml).join('');
      note.textContent = message;
    }}

    function parseTicket(text) {{
      const nums = (text.match(/\\d{{1,2}}/g) || []).map(value => Number(value));
      if (nums.length < 7) {{
        return {{ error: '至少需要 6 个红球和 1 个蓝球' }};
      }}
      const reds = nums.slice(0, 6);
      const blue = nums[6];
      const uniqueReds = new Set(reds);
      if (uniqueReds.size !== 6) {{
        return {{ error: '红球不能重复' }};
      }}
      if (reds.some(value => value < 1 || value > 33)) {{
        return {{ error: '红球范围应为 01-33' }};
      }}
      if (blue < 1 || blue > 16) {{
        return {{ error: '蓝球范围应为 01-16' }};
      }}
      return {{ reds: reds.sort((a, b) => a - b), blue }};
    }}

    function prizeName(redHits, blueHit) {{
      if (redHits === 6 && blueHit) return '一等奖';
      if (redHits === 6) return '二等奖';
      if (redHits === 5 && blueHit) return '三等奖';
      if (redHits === 5 || (redHits === 4 && blueHit)) return '四等奖';
      if (redHits === 4 || (redHits === 3 && blueHit)) return '五等奖';
      if (blueHit) return '六等奖';
      return '未中奖';
    }}

    function evaluateTicket(ticket, draw) {{
      const drawReds = draw.Red.split(',').map(value => Number(value));
      const drawRedSet = new Set(drawReds);
      const hitReds = ticket.reds.filter(value => drawRedSet.has(value));
      const blueHit = ticket.blue === Number(draw.Blue);
      const prize = prizeName(hitReds.length, blueHit);
      return {{ drawReds, hitReds, blueHit, prize }};
    }}

    function ticketBalls(ticket, result) {{
      const hitSet = new Set(result.hitReds);
      const reds = ticket.reds.map(value => {{
        const valueText = String(value).padStart(2, '0');
        const cls = hitSet.has(value) ? 'red-ball hit-red' : 'red-ball';
        return `<span class="${{cls}}">${{valueText}}</span>`;
      }}).join('');
      return reds + blueBallWithHit(String(ticket.blue).padStart(2, '0'), result.blueHit);
    }}

    function renderCheckResult(rawText, index) {{
      const draw = APP_DATA.records.find(item => item.Issue === checkIssueSelect.value) || APP_DATA.records[APP_DATA.records.length - 1];
      const ticket = parseTicket(rawText);
      if (ticket.error) {{
        return `<div class="result-card"><div class="result-head"><span>第 ${{index}} 注</span><span class="prize miss">${{ticket.error}}</span></div><div class="note">${{rawText || '空行'}}</div></div>`;
      }}
      const result = evaluateTicket(ticket, draw);
      const prizeClass = result.prize === '未中奖' ? 'prize miss' : 'prize';
      return `<div class="result-card">
        <div class="result-head"><span>第 ${{index}} 注 · 命中红球 ${{result.hitReds.length}} 个 / 蓝球 ${{result.blueHit ? '命中' : '未中'}}</span><span class="${{prizeClass}}">${{result.prize}}</span></div>
        <div class="latest-row">${{ticketBalls(ticket, result)}}</div>
      </div>`;
    }}

    function updateDrawInfo() {{
      const draw = APP_DATA.records.find(item => item.Issue === checkIssueSelect.value) || APP_DATA.records[APP_DATA.records.length - 1];
      const drawHitSet = new Set(draw.Red.split(',').map(value => Number(value)));
      drawInfo.innerHTML = `当前核验：${{draw.Issue}}期 · ${{draw.Date}}<div class="latest-row" style="margin-top:8px;">${{redBallsWithHits(draw.Red, drawHitSet)}}${{blueBallWithHit(draw.Blue, true)}}</div>`;
    }}

    function checkSingle() {{
      const value = singleTicketInput.value.trim();
      checkResults.innerHTML = renderCheckResult(value, 1);
    }}

    function checkBatch() {{
      const lines = batchTicketInput.value.split(/\\r?\\n/).map(line => line.trim()).filter(Boolean);
      if (!lines.length) {{
        checkResults.innerHTML = '<div class="result-card"><span class="prize miss">请先粘贴号码</span></div>';
        return;
      }}
      checkResults.innerHTML = lines.map((line, index) => renderCheckResult(line, index + 1)).join('');
    }}

    function fillExampleTickets() {{
      singleTicketInput.value = exampleTickets[0];
      batchTicketInput.value = exampleTickets.join('\\n');
      checkBatch();
    }}

    function clearCheckResults() {{
      singleTicketInput.value = '';
      batchTicketInput.value = '';
      checkResults.innerHTML = '';
      updateDrawInfo();
    }}

    const years = Array.from(new Set(APP_DATA.records.map(item => item.Date.slice(0, 4)))).reverse();
    yearSelect.innerHTML = '<option value="">选择年份</option>' + years.map(year => `<option value="${{year}}">${{year}}年</option>`).join('');
    checkIssueSelect.innerHTML = APP_DATA.records.slice().reverse().map(item => `<option value="${{item.Issue}}">${{item.Issue}}期 · ${{item.Date}}</option>`).join('');
    checkIssueSelect.value = APP_DATA.records[APP_DATA.records.length - 1].Issue;
    updateDrawInfo();

    document.querySelectorAll('.tab').forEach(tab => {{
      tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
        document.querySelectorAll('.section').forEach(item => item.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
      }});
    }});

    yearSelect.addEventListener('change', () => {{
      issueInput.value = '';
      const year = yearSelect.value;
      const rows = year ? APP_DATA.records.filter(item => item.Date.startsWith(year)) : APP_DATA.records.slice(-30).reverse();
      renderRows(rows.slice().reverse(), year ? `${{year}}年共 ${{rows.length}} 期` : '当前显示最近30期。可按年份或期号查询。');
    }});

    issueInput.addEventListener('input', () => {{
      yearSelect.value = '';
      const keyword = issueInput.value.trim();
      if (!keyword) {{
        renderRows(APP_DATA.records.slice(-30).reverse(), '当前显示最近30期。可按年份或期号查询。');
        return;
      }}
      const rows = APP_DATA.records.filter(item => item.Issue.includes(keyword));
      renderRows(rows.slice().reverse(), `找到 ${{rows.length}} 条匹配期号`);
    }});

    document.getElementById('resetBtn').addEventListener('click', () => {{
      yearSelect.value = '';
      issueInput.value = '';
      renderRows(APP_DATA.records.slice(-30).reverse(), '当前显示最近30期。可按年份或期号查询。');
    }});

    checkIssueSelect.addEventListener('change', () => {{
      updateDrawInfo();
      if (checkResults.innerHTML.trim()) {{
        if (batchTicketInput.value.trim()) checkBatch();
        else if (singleTicketInput.value.trim()) checkSingle();
      }}
    }});
    document.getElementById('checkSingleBtn').addEventListener('click', checkSingle);
    document.getElementById('checkBatchBtn').addEventListener('click', checkBatch);
    document.getElementById('fillExampleBtn').addEventListener('click', fillExampleTickets);
    document.getElementById('clearCheckBtn').addEventListener('click', clearCheckResults);
    singleTicketInput.addEventListener('keydown', event => {{
      if (event.key === 'Enter') checkSingle();
    }});
  </script>
</body>
</html>
"""
    with open(OUT_FILE, "w", encoding="utf-8") as file:
        file.write(html_text)
    print(f"Built {OUT_FILE} with {total} records.")


if __name__ == "__main__":
    main()
