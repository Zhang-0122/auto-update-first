#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a self-contained public lottery dashboard."""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean

from lottery_config import DISCLAIMER, LOTTERIES, LotteryConfig


ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "ssq_analyzer.html"


def number(value: int | str) -> str:
    return f"{int(value):02d}"


def split_numbers(value: str) -> list[int]:
    return [int(item) for item in str(value).replace("，", ",").split(",") if item.strip()]


def load_records(config: LotteryConfig) -> list[dict[str, str]]:
    data_file = ROOT / config.data_file
    if not data_file.exists():
        return []
    with data_file.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    records = data if isinstance(data, list) else []
    return sorted(records, key=lambda item: (item.get("Date", ""), item.get("Issue", "")))


def record_groups(lottery_id: str, record: dict[str, str]) -> list[list[int]]:
    if lottery_id == "ssq":
        return [split_numbers(record["Red"]), [int(record["Blue"])]]
    if lottery_id == "dlt":
        return [split_numbers(record["Front"]), split_numbers(record["Back"])]
    if lottery_id in {"fc3d", "pl3", "pl5", "qxc"}:
        return [split_numbers(record["Digit"])]
    if lottery_id == "qlc":
        return [split_numbers(record["Main"]), [int(record["Special"])]]
    return []


def latest_text(records: list[dict[str, str]]) -> str:
    if not records:
        return "暂无数据"
    latest = records[-1]
    return f"已同步到 {latest['Date']} 第 {latest['Issue']} 期"


def balls_html(values: list[int], class_name: str) -> str:
    return "".join(f'<span class="ball {class_name}">{number(value)}</span>' for value in values)


def latest_balls_html(lottery_id: str, records: list[dict[str, str]]) -> str:
    if not records:
        return '<span class="empty">等待同步</span>'
    groups = record_groups(lottery_id, records[-1])
    parts = []
    for index, group in enumerate(groups):
        area = LOTTERIES[lottery_id].areas[index]
        parts.append(balls_html(group, area.color))
    return "".join(parts)


def area_counter(lottery_id: str, records: list[dict[str, str]], area_index: int) -> Counter[int]:
    counter: Counter[int] = Counter()
    for record in records:
        for value in record_groups(lottery_id, record)[area_index]:
            counter[value] += 1
    return counter


def build_frequency_rows(config: LotteryConfig, records: list[dict[str, str]], area_index: int) -> str:
    area = config.areas[area_index]
    counter = area_counter(config.lottery_id, records, area_index)
    if not records:
        return '<div class="empty">暂无统计数据</div>'
    max_count = max(counter.values()) if counter else 1
    expected = len(records) * area.count / (area.max_number - area.min_number + 1)
    rows = []
    for value in range(area.min_number, area.max_number + 1):
        count = counter[value]
        percent = round(count / max_count * 100, 2) if max_count else 0
        state = "中"
        state_class = "normal"
        if count >= expected * 1.08:
            state = "热"
            state_class = "hot"
        elif count <= expected * 0.92:
            state = "冷"
            state_class = "cold"
        rows.append(
            f"""
            <div class="freq-row {area.color} {state_class}">
              <span class="mini-ball">{number(value)}</span>
              <span class="freq-track"><span class="freq-fill" style="width:{percent}%"></span></span>
              <span class="freq-count">{count} 次</span>
              <span class="freq-tag">{state}</span>
            </div>
            """
        )
    return "\n".join(rows)


def build_history_rows(lottery_id: str, records: list[dict[str, str]], limit: int = 40) -> str:
    rows = []
    for record in reversed(records[-limit:]):
        groups = record_groups(lottery_id, record)
        rows.append(
            f"""
            <tr data-lottery="{lottery_id}" data-search="{html.escape(record['Issue'] + ' ' + record['Date'] + ' ' + ' '.join(number(v) for group in groups for v in group))}">
              <td>{html.escape(record["Issue"])}</td>
              <td>{html.escape(record["Date"])}</td>
              <td>{balls_html(groups[0], LOTTERIES[lottery_id].areas[0].color)}</td>
              <td>{balls_html(groups[1], LOTTERIES[lottery_id].areas[1].color) if len(groups) > 1 else '<span class="muted">无</span>'}</td>
            </tr>
            """
        )
    return "\n".join(rows) if rows else '<tr><td colspan="4">暂无数据</td></tr>'


def build_sum_svg(lottery_id: str, records: list[dict[str, str]]) -> str:
    recent = records[-50:]
    if len(recent) < 2:
        return '<div class="empty">暂无趋势数据</div>'
    values = [sum(record_groups(lottery_id, record)[0]) for record in recent]
    width, height = 860, 260
    left, right, top, bottom = 48, 20, 18, 36
    plot_width = width - left - right
    plot_height = height - top - bottom
    low = min(values) - 5
    high = max(values) + 5
    span = high - low or 1

    def point(index: int, value: int) -> tuple[float, float]:
        x = left + index / max(1, len(values) - 1) * plot_width
        y = top + (high - value) / span * plot_height
        return x, y

    path = " ".join(("M" if index == 0 else "L") + f"{point(index, value)[0]:.1f},{point(index, value)[1]:.1f}" for index, value in enumerate(values))
    avg_value = round(mean(values), 1)
    avg_y = top + (high - avg_value) / span * plot_height
    grid = []
    for step in range(5):
        value = round(low + (high - low) * step / 4)
        y = top + (high - value) / span * plot_height
        grid.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}"></line>')
        grid.append(f'<text class="axis" x="{left - 8}" y="{y + 4:.1f}" text-anchor="end">{value}</text>')
    dots = []
    labels = []
    for index, record in enumerate(recent):
        x, y = point(index, values[index])
        dots.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="3"><title>{record["Issue"]}期 {record["Date"]}：{values[index]}</title></circle>')
        if index in (0, len(recent) - 1) or index % 12 == 0:
            labels.append(f'<text class="axis" x="{x:.1f}" y="{height - 10}" text-anchor="middle">{html.escape(record["Date"][5:])}</text>')
    return f"""
    <svg class="trend-svg" viewBox="0 0 {width} {height}" role="img" aria-label="近50期一区号码和值趋势">
      {''.join(grid)}
      <line class="avg" x1="{left}" y1="{avg_y:.1f}" x2="{width - right}" y2="{avg_y:.1f}"></line>
      <text class="avg-label" x="{width - right - 6}" y="{avg_y - 8:.1f}" text-anchor="end">均值 {avg_value}</text>
      <path class="line" d="{path}"></path>
      {''.join(dots)}
      {''.join(labels)}
    </svg>
    """


def recommend_groups(config: LotteryConfig, records: list[dict[str, str]]) -> list[dict[str, str]]:
    if not records:
        return []
    groups = []
    for area_index, area in enumerate(config.areas):
        counter = area_counter(config.lottery_id, records, area_index)
        hot = [num for num, _ in counter.most_common(area.count + 2)]
        cold = [num for num, _ in sorted(counter.items(), key=lambda item: item[1])[: max(1, area.count)]]
        balanced = sorted((hot[: area.count - 1] + cold[:1])[: area.count])
        groups.append({"label": area.label, "numbers": " ".join(number(value) for value in balanced)})
    return groups


def lottery_payload() -> dict[str, object]:
    payload: dict[str, object] = {"lotteries": {}, "disclaimer": DISCLAIMER}
    for lottery_id, config in LOTTERIES.items():
        records = load_records(config)
        payload["lotteries"][lottery_id] = {
            "id": lottery_id,
            "name": config.name,
            "shortName": config.short_name,
            "officialSource": config.official_source,
            "sourceUrl": config.source_url,
            "drawDays": config.draw_days,
            "areas": [area.__dict__ for area in config.areas],
            "records": records,
            "latestText": latest_text(records),
        }
    return payload


def build_page() -> str:
    data = lottery_payload()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    lottery_cards = []
    history_sections = []
    frequency_sections = []
    trend_sections = []
    recommend_sections = []

    for lottery_id, config in LOTTERIES.items():
        records = load_records(config)
        latest = records[-1] if records else None
        latest_issue = f"第 {latest['Issue']} 期" if latest else "等待同步"
        lottery_cards.append(
            f"""
            <button class="lottery-card {'active' if lottery_id == 'ssq' else ''}" data-lottery="{lottery_id}" type="button">
              <span class="lottery-card-head"><strong>{config.short_name}</strong><small>{html.escape(config.draw_days)}</small></span>
              <span class="lottery-balls">{latest_balls_html(lottery_id, records)}</span>
              <span class="lottery-meta">{latest_text(records)} · {config.official_source}</span>
            </button>
            """
        )
        history_sections.append(
            f"""
            <tbody class="history-body {'active' if lottery_id == 'ssq' else ''}" data-lottery-panel="{lottery_id}">
              {build_history_rows(lottery_id, records)}
            </tbody>
            """
        )
        area_blocks = []
        for area_index, area in enumerate(config.areas):
            area_blocks.append(
                f"""
                <div class="panel mini-panel">
                  <div class="panel-title"><h3>{config.short_name}{area.label}频率</h3><span>{area.min_number}-{area.max_number}</span></div>
                  <div class="freq-list">{build_frequency_rows(config, records, area_index)}</div>
                </div>
                """
            )
        frequency_sections.append(
            f'<div class="frequency-panel {"active" if lottery_id == "ssq" else ""}" data-lottery-panel="{lottery_id}">{"".join(area_blocks)}</div>'
        )
        trend_sections.append(
            f"""
            <div class="trend-panel {'active' if lottery_id == 'ssq' else ''}" data-lottery-panel="{lottery_id}">
              <div class="panel-title"><h3>{config.short_name}近50期一区和值趋势</h3><span>只看走势，不代表未来结果</span></div>
              {build_sum_svg(lottery_id, records)}
            </div>
            """
        )
        rec_parts = recommend_groups(config, records)
        recommend_sections.append(
            f"""
            <div class="recommend-panel {'active' if lottery_id == 'ssq' else ''}" data-lottery-panel="{lottery_id}">
              <div class="rec-card">
                <strong>{config.short_name}统计参考 A</strong>
                <p>{'　'.join(f'{item["label"]}：{item["numbers"]}' for item in rec_parts) or '暂无数据'}</p>
                <small>理由：混合高频号码和少量低频号码，帮助观察分布；不代表预测。</small>
              </div>
              <div class="rec-card">
                <strong>{config.short_name}统计参考 B</strong>
                <p>建议结合个人预算，只做娱乐参考。</p>
                <small>风险提示：彩票开奖结果具有随机性，历史频率不能推出未来号码。</small>
              </div>
            </div>
            """
        )

    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>彩票开奖数据中心</title>
  <style>
    :root {{
      --page:#f6f7fb; --card:#ffffff; --ink:#202633; --muted:#667085; --line:#e4e7ec;
      --warm:#f05a28; --warm-soft:#f4b29a; --warm-mid:#ff914d;
      --cool:#176fd1; --cool-soft:#c4dcf5; --cool-mid:#63adff;
      --green:#1f8a58; --amber:#a76813; --shadow:0 18px 45px rgba(31,41,55,.08);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--page); color:var(--ink); font-family:"Microsoft YaHei", "PingFang SC", Arial, sans-serif; line-height:1.6; }}
    .page {{ max-width:1220px; margin:0 auto; padding:24px; }}
    .hero {{ display:grid; grid-template-columns:1.15fr .85fr; gap:16px; align-items:stretch; }}
    .hero-main {{ border-radius:28px; padding:26px; background:linear-gradient(135deg,#fff3ec,#eef6ff); border:1px solid var(--line); box-shadow:var(--shadow); }}
    .hero-side, .panel {{ border-radius:24px; background:var(--card); border:1px solid var(--line); box-shadow:var(--shadow); padding:18px; }}
    h1 {{ margin:0 0 8px; font-size:34px; letter-spacing:-.04em; }}
    h2, h3 {{ margin:0; }}
    p {{ margin:0; }}
    .muted, small {{ color:var(--muted); }}
    .search-row {{ display:grid; grid-template-columns:1fr auto; gap:10px; margin:18px 0 14px; }}
    input, textarea, select {{ width:100%; border:1px solid var(--line); border-radius:14px; padding:11px 12px; font:inherit; background:#fff; color:var(--ink); }}
    textarea {{ min-height:120px; resize:vertical; }}
    button {{ font:inherit; }}
    .btn {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:999px; padding:10px 14px; cursor:pointer; }}
    .btn.primary {{ background:var(--ink); color:#fff; border-color:var(--ink); }}
    .chips, .tabs, .action-row {{ display:flex; flex-wrap:wrap; gap:8px; }}
    .chip, .tab {{ border:1px solid var(--line); background:#fff; border-radius:999px; padding:8px 12px; cursor:pointer; }}
    .tab.active, .chip.active {{ border-color:var(--ink); background:var(--ink); color:#fff; }}
    .status-list {{ display:grid; gap:10px; }}
    .status-row {{ display:flex; justify-content:space-between; gap:12px; border-bottom:1px dashed var(--line); padding-bottom:9px; }}
    .status-row:last-child {{ border-bottom:0; padding-bottom:0; }}
    .ok {{ color:var(--green); font-weight:700; }}
    .lottery-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin:18px 0; }}
    .lottery-card {{ text-align:left; display:grid; gap:9px; border:1px solid var(--line); border-radius:20px; padding:14px; background:#fff; cursor:pointer; }}
    .lottery-card.active {{ border-color:var(--ink); background:linear-gradient(135deg,#fff8f3,#eef6ff); }}
    .lottery-card-head {{ display:flex; justify-content:space-between; gap:10px; align-items:center; }}
    .lottery-meta {{ color:var(--muted); font-size:13px; }}
    .ball, .mini-ball {{ display:inline-flex; align-items:center; justify-content:center; border-radius:999px; font-weight:700; font-variant-numeric:tabular-nums; }}
    .ball {{ width:32px; height:32px; margin:0 4px 4px 0; }}
    .mini-ball {{ width:30px; height:30px; }}
    .warm {{ background:linear-gradient(145deg,var(--warm-mid),var(--warm)); color:#fff8f3; }}
    .cool {{ background:linear-gradient(145deg,var(--cool-mid),var(--cool)); color:#eef7ff; }}
    .neutral {{ background:linear-gradient(145deg,#eef1f6,#d7dee8); color:#344054; }}
    .main {{ display:grid; grid-template-columns:260px 1fr; gap:16px; align-items:start; }}
    .sidebar {{ position:sticky; top:16px; }}
    .content {{ display:grid; gap:16px; }}
    .section {{ display:none; }}
    .section.active {{ display:block; }}
    .panel-title {{ display:flex; justify-content:space-between; gap:12px; align-items:center; margin-bottom:12px; }}
    .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .three-col {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }}
    .feature {{ border:1px solid var(--line); border-radius:18px; padding:14px; background:#fbfcff; }}
    .history-body, .frequency-panel, .trend-panel, .recommend-panel {{ display:none; }}
    .history-body.active {{ display:table-row-group; }}
    .frequency-panel.active, .trend-panel.active, .recommend-panel.active {{ display:grid; gap:14px; }}
    table {{ width:100%; border-collapse:collapse; }}
    th, td {{ border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; vertical-align:middle; }}
    th {{ color:var(--muted); font-weight:700; }}
    .table-wrap {{ overflow:auto; }}
    .freq-list {{ display:grid; gap:8px; }}
    .freq-row {{ display:grid; grid-template-columns:34px 1fr 56px 36px; gap:8px; align-items:center; }}
    .freq-track {{ height:10px; border-radius:999px; background:#edf0f5; overflow:hidden; }}
    .freq-fill {{ display:block; height:100%; border-radius:999px; }}
    .freq-row.warm .freq-fill {{ background:linear-gradient(90deg,var(--warm-soft),var(--warm)); }}
    .freq-row.cool .freq-fill {{ background:linear-gradient(90deg,var(--cool-soft),var(--cool)); }}
    .freq-row.warm.cold .mini-ball {{ background:linear-gradient(145deg,#ffd9ca,var(--warm-soft)); color:#6e321f; }}
    .freq-row.warm.hot .mini-ball {{ background:linear-gradient(145deg,var(--warm-mid),var(--warm)); color:#fff8f3; }}
    .freq-row.cool.cold .mini-ball {{ background:linear-gradient(145deg,#e7f2ff,var(--cool-soft)); color:#204c76; }}
    .freq-row.cool.hot .mini-ball {{ background:linear-gradient(145deg,var(--cool-mid),var(--cool)); color:#eef7ff; }}
    .freq-row.normal .mini-ball {{ background:#eef1f6; color:#344054; }}
    .trend-svg {{ width:100%; height:auto; }}
    .grid {{ stroke:#e4e7ec; stroke-width:1; }}
    .axis, .avg-label {{ fill:#667085; font-size:12px; }}
    .line {{ fill:none; stroke:var(--warm); stroke-width:3; }}
    .dot {{ fill:var(--cool); }}
    .avg {{ stroke:#98a2b3; stroke-dasharray:6 6; }}
    .checker-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .result {{ margin-top:12px; border-radius:16px; padding:12px; background:#f8fafc; border:1px solid var(--line); white-space:pre-wrap; }}
    .rec-card, .notice {{ border-radius:18px; padding:14px; border:1px solid var(--line); background:#fbfcff; }}
    .notice {{ background:#fff8ed; border-color:#f0d7ad; }}
    .footer {{ margin-top:18px; color:var(--muted); text-align:center; font-size:13px; }}
    .empty {{ color:var(--muted); }}
    @media (max-width:860px) {{
      .page {{ padding:14px; }}
      .hero, .main, .two-col, .three-col, .checker-grid {{ grid-template-columns:1fr; }}
      .sidebar {{ position:static; }}
      .lottery-grid {{ grid-template-columns:1fr; }}
      h1 {{ font-size:28px; }}
      .search-row {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <section class="hero-main">
        <h1>彩票开奖数据中心</h1>
        <p class="muted">公开开奖记录查询、中奖核验、号码统计和同步状态说明。先支持双色球和大乐透，后续彩种按配置逐步接入。</p>
        <div class="search-row">
          <input id="globalSearch" type="search" placeholder="输入彩种、期号、日期或号码，例如：双色球 2026086 / 大乐透 26084 / 04 07 13">
          <button class="btn primary" type="button" id="searchBtn">一键查询</button>
        </div>
        <div class="chips">
          <span class="chip active">双色球</span>
          <span class="chip">大乐透</span>
          <span class="chip">福彩3D</span>
          <span class="chip">排列3</span>
          <span class="chip">排列5</span>
          <span class="chip">七星彩</span>
          <span class="chip">七乐彩</span>
        </div>
      </section>
      <aside class="hero-side">
        <div class="panel-title"><h2>同步与来源</h2><span class="ok">自动检查</span></div>
        <div class="status-list">
          <div class="status-row"><span>双色球</span><strong>{data["lotteries"]["ssq"]["latestText"]}</strong></div>
          <div class="status-row"><span>大乐透</span><strong>{data["lotteries"]["dlt"]["latestText"]}</strong></div>
          <div class="status-row"><span>官方来源</span><strong>中国福彩网 / 中国体彩网</strong></div>
          <div class="status-row"><span>生成时间</span><strong>{generated_at}</strong></div>
        </div>
      </aside>
    </header>

    <section class="lottery-grid" aria-label="彩种选择">
      {''.join(lottery_cards)}
    </section>

    <main class="main">
      <aside class="panel sidebar">
        <div class="panel-title"><h2>功能入口</h2><span id="currentLotteryLabel">双色球</span></div>
        <div class="tabs">
          <button class="tab active" data-section="history" type="button">历史查询</button>
          <button class="tab" data-section="checker" type="button">中奖核验</button>
          <button class="tab" data-section="stats" type="button">号码统计</button>
          <button class="tab" data-section="trend" type="button">走势查看</button>
          <button class="tab" data-section="recommend" type="button">选号参考</button>
          <button class="tab" data-section="about" type="button">同步说明</button>
        </div>
      </aside>

      <div class="content">
        <section id="history" class="section active panel">
          <div class="panel-title"><h2>历史查询</h2><span class="muted">默认显示最近 40 期</span></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>期号</th><th>日期</th><th>一区号码</th><th>二区号码</th></tr></thead>
              {''.join(history_sections)}
            </table>
          </div>
        </section>

        <section id="checker" class="section panel">
          <div class="panel-title"><h2>中奖核验</h2><span class="muted">结果以官方规则为准</span></div>
          <div class="checker-grid">
            <div>
              <label>一区号码</label>
              <input id="mainNumbers" placeholder="输入一区/开奖号码，例如 双色球6个红球、大乐透5个前区、排列5填5位数字">
            </div>
            <div>
              <label>二区号码</label>
              <input id="specialNumbers" placeholder="有二区再填，例如 双色球蓝球、大乐透后区、七乐彩特别号；数字彩可留空">
            </div>
          </div>
          <div class="action-row" style="margin-top:12px">
            <button class="btn primary" id="checkSingle" type="button">核验当前号码</button>
            <button class="btn" id="fillExample" type="button">示例填入</button>
            <button class="btn" id="clearResult" type="button">清空结果</button>
          </div>
          <label style="display:block;margin-top:14px">批量核验（一行一注，前后区用 + 分隔）</label>
          <textarea id="batchNumbers" placeholder="例：01 02 03 04 05 06 + 07&#10;13 25 30 32 33 + 04 05&#10;3 0 5"></textarea>
          <div class="action-row" style="margin-top:12px">
            <button class="btn" id="checkBatch" type="button">批量核验</button>
            <button class="btn" id="exportCsv" type="button">导出 CSV</button>
          </div>
          <div id="checkResult" class="result">请输入号码后核验。</div>
        </section>

        <section id="stats" class="section">
          {''.join(frequency_sections)}
        </section>

        <section id="trend" class="section panel">
          {''.join(trend_sections)}
        </section>

        <section id="recommend" class="section panel">
          <div class="panel-title"><h2>选号参考</h2><span class="muted">统计参考，不是预测</span></div>
          {''.join(recommend_sections)}
        </section>

        <section id="about" class="section panel">
          <div class="panel-title"><h2>同步说明</h2><span class="ok">失败保护已开启</span></div>
          <div class="three-col">
            <div class="feature"><strong>官方公开数据</strong><p class="muted">福彩类优先查询中国福彩网，体彩类优先查询中国体彩网。</p></div>
            <div class="feature"><strong>自动同步日期</strong><p class="muted">GitHub Actions 定时检查最新开奖，数据变化后生成新版网页。</p></div>
            <div class="feature"><strong>保留旧数据</strong><p class="muted">官方接口异常或网络失败时，不会清空已可用页面。</p></div>
          </div>
          <div class="notice" style="margin-top:14px"><strong>权威免责声明</strong><p>{html.escape(DISCLAIMER)}</p></div>
        </section>
      </div>
    </main>
    <div class="footer">本页面不销售彩票，不提供代购服务。开奖号码、奖级和兑奖规则以官方公告为准。</div>
  </div>

  <script>
    const DATA = {data_json};
    let currentLottery = "ssq";
    let lastBatchRows = [];

    const parseNums = (value) => (value || "").replace(/，/g, " ").replace(/,/g, " ").trim().split(/\\s+/).filter(Boolean).map(Number);
    const fmt = (value) => String(value).padStart(2, "0");
    const currentData = () => DATA.lotteries[currentLottery];
    const latestDraw = () => currentData().records[currentData().records.length - 1];

    function groupsFromDraw(draw) {{
      if (!draw) return [[], []];
      if (currentLottery === "ssq") return [parseNums(draw.Red), parseNums(draw.Blue)];
      if (currentLottery === "dlt") return [parseNums(draw.Front), parseNums(draw.Back)];
      if (currentLottery === "qlc") return [parseNums(draw.Main), parseNums(draw.Special)];
      return [parseNums(draw.Digit)];
    }}

    function checkSsq(redHits, blueHits) {{
      if (redHits === 6 && blueHits === 1) return "一等奖";
      if (redHits === 6 && blueHits === 0) return "二等奖";
      if (redHits === 5 && blueHits === 1) return "三等奖";
      if (redHits === 5 || (redHits === 4 && blueHits === 1)) return "四等奖";
      if ((redHits === 4 && blueHits === 0) || (redHits === 3 && blueHits === 1)) return "五等奖";
      if (blueHits === 1) return "六等奖";
      return "未中奖";
    }}

    function checkDlt(frontHits, backHits) {{
      if (frontHits === 5 && backHits === 2) return "一等奖";
      if (frontHits === 5 && backHits === 1) return "二等奖";
      if (frontHits === 5 && backHits === 0) return "三等奖";
      if (frontHits === 4 && backHits === 2) return "四等奖";
      if (frontHits === 4 && backHits === 1) return "五等奖";
      if (frontHits === 3 && backHits === 2) return "六等奖";
      if (frontHits === 4 && backHits === 0) return "七等奖";
      if ((frontHits === 3 && backHits === 1) || (frontHits === 2 && backHits === 2)) return "八等奖";
      if ((frontHits === 3 && backHits === 0) || (frontHits === 2 && backHits === 1) || (frontHits === 1 && backHits === 2) || (frontHits === 0 && backHits === 2)) return "九等奖";
      return "未中奖";
    }}

    function checkQlc(mainHits, specialHits) {{
      if (mainHits === 7 && specialHits === 1) return "一等奖";
      if (mainHits === 7 && specialHits === 0) return "二等奖";
      if (mainHits === 6 && specialHits === 1) return "三等奖";
      if (mainHits === 6 && specialHits === 0) return "四等奖";
      if (mainHits === 5 && specialHits === 1) return "五等奖";
      if ((mainHits === 5 && specialHits === 0) || (mainHits === 4 && specialHits === 1)) return "六等奖";
      if (mainHits === 4 && specialHits === 0) return "七等奖";
      return "未中奖";
    }}

    function checkDigits(drawMain, ticketMain) {{
      const exact = drawMain.length === ticketMain.length && drawMain.every((value, index) => value === ticketMain[index]);
      if (exact) return currentLottery === "fc3d" || currentLottery === "pl3" ? "直选命中" : "命中开奖号码";
      if ((currentLottery === "fc3d" || currentLottery === "pl3") && [...drawMain].sort().join(",") === [...ticketMain].sort().join(",")) return "组选参考命中";
      return "未中奖";
    }}

    function checkTicket(mainNums, specialNums) {{
      const draw = latestDraw();
      if (!draw) return {{ level: "暂无开奖数据", mainHits: 0, specialHits: 0 }};
      const [drawMain, drawSpecial] = groupsFromDraw(draw);
      const areas = currentData().areas;
      if (areas.length === 1) {{
        const level = checkDigits(drawMain, mainNums);
        const orderedHits = mainNums.filter((value, index) => drawMain[index] === value).length;
        return {{ level, mainHits: orderedHits, specialHits: 0 }};
      }}
      const mainHits = mainNums.filter(value => drawMain.includes(value)).length;
      const specialHits = specialNums.filter(value => drawSpecial.includes(value)).length;
      let level = "未中奖";
      if (currentLottery === "ssq") level = checkSsq(mainHits, specialHits);
      else if (currentLottery === "dlt") level = checkDlt(mainHits, specialHits);
      else if (currentLottery === "qlc") level = checkQlc(mainHits, specialHits);
      return {{ level, mainHits, specialHits }};
    }}

    function setLottery(lotteryId) {{
      currentLottery = lotteryId;
      const data = currentData();
      document.getElementById("currentLotteryLabel").textContent = data.shortName;
      document.querySelectorAll(".lottery-card").forEach(card => card.classList.toggle("active", card.dataset.lottery === lotteryId));
      document.querySelectorAll("[data-lottery-panel]").forEach(panel => panel.classList.toggle("active", panel.dataset.lotteryPanel === lotteryId));
      document.getElementById("checkResult").textContent = `当前彩种：${{data.shortName}}。请输入号码后核验。`;
      document.getElementById("mainNumbers").value = "";
      document.getElementById("specialNumbers").value = "";
      document.getElementById("batchNumbers").value = "";
      lastBatchRows = [];
    }}

    function setSection(sectionId) {{
      document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.section === sectionId));
      document.querySelectorAll(".section").forEach(section => section.classList.toggle("active", section.id === sectionId));
    }}

    function validateInput(mainNums, specialNums) {{
      const areas = currentData().areas;
      const specialArea = areas[1];
      if (mainNums.length !== areas[0].count || (specialArea && specialNums.length !== specialArea.count) || (!specialArea && specialNums.length !== 0)) {{
        return specialArea
          ? `号码数量不对：${{currentData().shortName}}需要${{areas[0].count}}个${{areas[0].label}}、${{specialArea.count}}个${{specialArea.label}}。`
          : `号码数量不对：${{currentData().shortName}}需要${{areas[0].count}}个${{areas[0].label}}，二区请留空。`;
      }}
      if (areas[0].unique && new Set(mainNums).size !== mainNums.length) return "一区号码不能重复。";
      if (specialArea && specialArea.unique && new Set(specialNums).size !== specialNums.length) return "二区号码不能重复。";
      if (mainNums.some(value => value < areas[0].min_number || value > areas[0].max_number)) return `${{areas[0].label}}超出范围。`;
      if (specialArea && specialNums.some(value => value < specialArea.min_number || value > specialArea.max_number)) return `${{specialArea.label}}超出范围。`;
      return "";
    }}

    function runSingleCheck() {{
      const mainNums = parseNums(document.getElementById("mainNumbers").value);
      const specialNums = parseNums(document.getElementById("specialNumbers").value);
      const error = validateInput(mainNums, specialNums);
      if (error) {{
        document.getElementById("checkResult").textContent = error;
        return;
      }}
      const result = checkTicket(mainNums, specialNums);
      const latest = latestDraw();
      const specialText = currentData().areas.length > 1 ? `，二区命中 ${{result.specialHits}} 个` : "";
      document.getElementById("checkResult").textContent = `${{currentData().shortName}} ${{latest.Issue}}期：${{result.level}}\\n一区/开奖号码命中 ${{result.mainHits}} 个${{specialText}}。\\n提示：核验结果仅供参考，最终以官方兑奖规则为准。`;
    }}

    function parseBatchLine(line) {{
      const parts = line.split("+");
      if (parts.length === 2) return [parseNums(parts[0]), parseNums(parts[1])];
      const nums = parseNums(line);
      const mainCount = currentData().areas[0].count;
      return [nums.slice(0, mainCount), nums.slice(mainCount)];
    }}

    function runBatchCheck() {{
      const lines = document.getElementById("batchNumbers").value.split(/\\n+/).map(line => line.trim()).filter(Boolean);
      if (!lines.length) {{
        document.getElementById("checkResult").textContent = "请先粘贴要批量核验的号码。";
        return;
      }}
      lastBatchRows = [];
      const output = lines.map((line, index) => {{
        const [mainNums, specialNums] = parseBatchLine(line);
        const error = validateInput(mainNums, specialNums);
        if (error) {{
          lastBatchRows.push([index + 1, line, "格式错误", error]);
          return `${{index + 1}}. 格式错误：${{error}}`;
        }}
        const result = checkTicket(mainNums, specialNums);
        const hitText = currentData().areas.length > 1 ? `一区${{result.mainHits}} 二区${{result.specialHits}}` : `按位命中${{result.mainHits}}`;
        lastBatchRows.push([index + 1, line, result.level, hitText]);
        return `${{index + 1}}. ${{result.level}}（${{hitText}}）`;
      }});
      document.getElementById("checkResult").textContent = output.join("\\n");
    }}

    function exportCsv() {{
      if (!lastBatchRows.length) runBatchCheck();
      if (!lastBatchRows.length) return;
      const csv = "序号,号码,结果,命中\\n" + lastBatchRows.map(row => row.map(cell => `"${{String(cell).replace(/"/g, '""')}}"`).join(",")).join("\\n");
      const blob = new Blob(["\\ufeff" + csv], {{ type: "text/csv;charset=utf-8" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${{currentData().shortName}}批量核验.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    }}

    function fillExample() {{
      const draw = latestDraw();
      const [main, special] = groupsFromDraw(draw);
      document.getElementById("mainNumbers").value = main.map(fmt).join(" ");
      document.getElementById("specialNumbers").value = (special || []).map(fmt).join(" ");
      document.getElementById("batchNumbers").value = special && special.length ? `${{main.map(fmt).join(" ")}} + ${{special.map(fmt).join(" ")}}` : main.map(fmt).join(" ");
      document.getElementById("checkResult").textContent = "已填入最新开奖号作为示例。";
    }}

    function runSearch() {{
      const keyword = document.getElementById("globalSearch").value.trim().toLowerCase();
      setSection("history");
      document.querySelectorAll(".history-body.active tr").forEach(row => {{
        const haystack = (row.dataset.search || row.textContent).toLowerCase();
        row.style.display = !keyword || haystack.includes(keyword) ? "" : "none";
      }});
    }}

    document.querySelectorAll(".lottery-card").forEach(card => card.addEventListener("click", () => setLottery(card.dataset.lottery)));
    document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => setSection(tab.dataset.section)));
    document.getElementById("checkSingle").addEventListener("click", runSingleCheck);
    document.getElementById("checkBatch").addEventListener("click", runBatchCheck);
    document.getElementById("exportCsv").addEventListener("click", exportCsv);
    document.getElementById("fillExample").addEventListener("click", fillExample);
    document.getElementById("clearResult").addEventListener("click", () => {{
      document.getElementById("mainNumbers").value = "";
      document.getElementById("specialNumbers").value = "";
      document.getElementById("batchNumbers").value = "";
      document.getElementById("checkResult").textContent = "已清空。";
      lastBatchRows = [];
    }});
    document.getElementById("searchBtn").addEventListener("click", runSearch);
    document.getElementById("globalSearch").addEventListener("keydown", event => {{ if (event.key === "Enter") runSearch(); }});
  </script>
</body>
</html>
"""


def main() -> None:
    html_text = build_page()
    OUT_FILE.write_text(html_text, encoding="utf-8")
    print(f"Dashboard generated: {OUT_FILE}")


if __name__ == "__main__":
    main()
