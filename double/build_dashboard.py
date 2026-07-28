#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a self-contained multi-lottery dashboard."""

from __future__ import annotations

import json
from pathlib import Path

from lottery_config import DISCLAIMER, LOTTERIES


ROOT = Path(__file__).resolve().parent
OUT_FILE = ROOT / "ssq_analyzer.html"


def load_records(file_name: str) -> list[dict[str, str]]:
    path = ROOT / file_name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    records = data if isinstance(data, list) else []
    return sorted(records, key=lambda item: (item.get("Date", ""), item.get("Issue", "")))


def build_payload() -> dict[str, object]:
    games: dict[str, object] = {}
    for lottery_id, config in LOTTERIES.items():
        records = load_records(config.data_file)
        games[lottery_id] = {
            "id": lottery_id,
            "name": config.short_name,
            "fullName": config.name,
            "source": config.official_source,
            "sourceUrl": config.source_url,
            "drawDays": config.draw_days,
            "areas": [area.__dict__ for area in config.areas],
            "records": records,
            "latestText": latest_text(records),
        }
    return {"games": games, "disclaimer": DISCLAIMER}


def latest_text(records: list[dict[str, str]]) -> str:
    if not records:
        return "等待同步"
    latest = records[-1]
    return f"已同步到 {latest['Date']} 第 {latest['Issue']} 期"


def main() -> None:
    payload = json.dumps(build_payload(), ensure_ascii=False, separators=(",", ":"))
    html = HTML_TEMPLATE.replace("__LOTTERY_DATA__", payload)
    OUT_FILE.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {OUT_FILE}")


HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>彩票开奖数据中心</title>
  <style>
    :root {
      --page:#f5f7fb; --card:#fff; --ink:#1f2937; --muted:#667085; --line:#e4e7ec;
      --warm:#f26b35; --warm-mid:#ff9a4d; --warm-soft:#ffd5c2;
      --cool:#2f8fe8; --cool-mid:#6ab5ff; --cool-soft:#d9ecff;
      --neutral:#d9e0ea; --green:#14835b; --amber:#a76813;
      --shadow:0 20px 48px rgba(31,41,55,.08);
    }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--page); color:var(--ink); font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif; line-height:1.6; }
    button, input, textarea { font:inherit; }
    button { cursor:pointer; }
    .page { max-width:1240px; margin:0 auto; padding:24px; }
    .hero { display:grid; grid-template-columns:1.1fr .9fr; gap:16px; align-items:stretch; }
    .panel, .hero-main, .hero-side { background:var(--card); border:1px solid var(--line); border-radius:26px; padding:20px; box-shadow:var(--shadow); }
    .hero-main { background:linear-gradient(135deg,#fff3ec,#eef6ff); }
    h1 { margin:0 0 8px; font-size:36px; letter-spacing:-.04em; }
    h2, h3 { margin:0; }
    p { margin:0; }
    .muted, small { color:var(--muted); }
    .head { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
    .pill { border:1px solid var(--line); border-radius:999px; padding:7px 12px; background:#f8fafc; }
    .ok { color:var(--green); font-weight:700; }
    .search-row { display:grid; grid-template-columns:1fr auto; gap:10px; margin-top:18px; }
    input, textarea { width:100%; border:1px solid var(--line); border-radius:16px; padding:12px 14px; background:#fff; color:var(--ink); }
    textarea { min-height:112px; resize:vertical; }
    .btn { border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:999px; padding:10px 16px; }
    .btn.primary { background:var(--ink); color:#fff; border-color:var(--ink); }
    .status-list { display:grid; gap:10px; margin-top:12px; }
    .status-row { display:flex; justify-content:space-between; gap:14px; border-bottom:1px dashed var(--line); padding-bottom:9px; }
    .status-row:last-child { border-bottom:0; padding-bottom:0; }
    .lottery-grid { display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:12px; margin:18px 0; }
    .lottery-card { min-height:164px; display:grid; gap:9px; text-align:left; border:1px solid var(--line); border-radius:22px; padding:14px; background:#fff; transition:.16s ease; }
    .lottery-card:hover { transform:translateY(-2px); border-color:#98a2b3; }
    .lottery-card.active { border-color:var(--ink); box-shadow:0 0 0 2px rgba(31,41,55,.08); background:linear-gradient(145deg,#fff8f3,#eef6ff); }
    .lottery-card-head { display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }
    .lottery-card strong { font-size:18px; }
    .source { color:var(--muted); font-size:13px; white-space:nowrap; }
    .lottery-meta { color:var(--muted); font-size:13px; border-top:1px dashed var(--line); padding-top:8px; }
    .balls { display:flex; flex-wrap:wrap; gap:5px; align-items:center; }
    .ball, .mini-ball { display:inline-flex; align-items:center; justify-content:center; border-radius:999px; font-weight:700; font-variant-numeric:tabular-nums; }
    .ball { width:32px; height:32px; }
    .mini-ball { width:30px; height:30px; }
    .warm { background:linear-gradient(145deg,var(--warm-mid),var(--warm)); color:#fff8f2; }
    .cool { background:linear-gradient(145deg,var(--cool-mid),var(--cool)); color:#eef7ff; }
    .neutral { background:linear-gradient(145deg,#eef1f6,var(--neutral)); color:#344054; }
    .detail { scroll-margin-top:16px; }
    .detail-layout { display:grid; grid-template-columns:290px 1fr; gap:16px; align-items:start; }
    .side { display:grid; gap:12px; }
    .stat { border:1px solid var(--line); border-radius:18px; padding:14px; background:#fbfcff; }
    .tabs { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }
    .tab { border:1px solid var(--line); border-radius:14px; padding:10px; background:#fff; color:var(--ink); text-align:center; }
    .tab.active { background:var(--ink); color:#fff; border-color:var(--ink); }
    .section { display:none; }
    .section.active { display:block; }
    .feature-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-bottom:14px; }
    .feature { border:1px solid var(--line); border-radius:18px; padding:14px; background:#fbfcff; }
    .feature strong { display:block; margin-bottom:4px; }
    table { width:100%; border-collapse:collapse; }
    th, td { border-bottom:1px solid var(--line); padding:10px 8px; text-align:left; vertical-align:middle; }
    th { color:var(--muted); }
    .table-wrap { overflow:auto; }
    .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
    .actions { display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }
    .result { margin-top:12px; border:1px solid var(--line); border-radius:16px; padding:12px; background:#f8fafc; white-space:pre-wrap; }
    .freq-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
    .freq-list { display:grid; gap:8px; }
    .freq-row { display:grid; grid-template-columns:36px 1fr 58px 36px; gap:8px; align-items:center; }
    .track { height:10px; border-radius:999px; background:#edf0f5; overflow:hidden; }
    .fill { display:block; height:100%; border-radius:999px; background:linear-gradient(90deg,var(--warm-soft),var(--warm)); }
    .fill.cool-fill { background:linear-gradient(90deg,var(--cool-soft),var(--cool)); }
    .trend-svg { width:100%; height:auto; display:block; }
    .grid-line { stroke:#e4e7ec; stroke-width:1; }
    .axis { fill:#667085; font-size:12px; }
    .trend-line { fill:none; stroke:var(--warm); stroke-width:3; }
    .trend-dot { fill:var(--cool); }
    .avg-line { stroke:#98a2b3; stroke-dasharray:6 6; }
    .notice { border:1px solid #f0d7ad; border-radius:18px; padding:14px; background:#fff8ed; }
    .footer { text-align:center; color:var(--muted); font-size:13px; margin-top:18px; }
    .empty { color:var(--muted); }
    @media (max-width:1100px) {
      .lottery-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
      .hero, .detail-layout { grid-template-columns:1fr; }
    }
    @media (max-width:720px) {
      .page { padding:14px; }
      h1 { font-size:28px; }
      .lottery-grid, .feature-grid, .freq-grid, .form-grid, .search-row { grid-template-columns:1fr; }
      .tabs { grid-template-columns:repeat(2,minmax(0,1fr)); }
    }
  </style>
</head>
<body>
  <div class="page">
    <header class="hero">
      <section class="hero-main">
        <div class="head">
          <div>
            <h1>彩票开奖数据中心</h1>
            <p class="muted">七个彩种平等入口：点哪一个，就进入哪一个的专属详情分析。</p>
          </div>
          <span class="pill">官方数据 · 自动同步 · 合规展示</span>
        </div>
        <div class="search-row">
          <input id="globalSearch" type="search" placeholder="支持输入：彩种名 / 期号 / 日期 / 完整号码，例如 大乐透 26084 或 13 25 30 32 33 + 04 05">
          <button class="btn primary" type="button" id="searchBtn">进入查询</button>
        </div>
      </section>
      <aside class="hero-side">
        <div class="head"><h2>同步与来源</h2><span class="ok">自动检查</span></div>
        <div class="status-list" id="statusList"></div>
      </aside>
    </header>

    <section class="lottery-grid" id="lotteryGrid" aria-label="彩种首页入口"></section>

    <section class="panel detail" id="detailPanel">
      <div class="detail-layout">
        <aside class="side">
          <div class="head"><h2 id="detailTitle">双色球详情页</h2><span class="pill" id="detailSource">中国福彩网</span></div>
          <div class="stat">
            <div class="muted" id="detailSync">已同步到</div>
            <div class="balls" id="detailBalls" style="margin-top:10px"></div>
          </div>
          <div class="stat">
            <strong>彩种规则</strong>
            <p class="muted" id="detailRule"></p>
          </div>
          <div class="tabs">
            <button class="tab active" data-section="overview" type="button">总览</button>
            <button class="tab" data-section="history" type="button">历史</button>
            <button class="tab" data-section="checker" type="button">核验</button>
            <button class="tab" data-section="stats" type="button">统计</button>
            <button class="tab" data-section="trend" type="button">走势</button>
            <button class="tab" data-section="recommend" type="button">参考</button>
          </div>
        </aside>
        <main class="side">
          <section class="section active" id="overview"></section>
          <section class="section" id="history"></section>
          <section class="section" id="checker"></section>
          <section class="section" id="stats"></section>
          <section class="section" id="trend"></section>
          <section class="section" id="recommend"></section>
        </main>
      </div>
    </section>

    <section class="notice" style="margin-top:16px">
      <strong>权威免责声明</strong>
      <p id="disclaimerText"></p>
    </section>
    <div class="footer">本页面不销售彩票，不提供代购服务。开奖号码、奖级和兑奖规则以官方公告为准。</div>
  </div>

  <script>
    const DATA = __LOTTERY_DATA__;
    const ORDER = ["ssq", "dlt", "fc3d", "pl3", "pl5", "qxc", "qlc"];
    let currentLottery = "ssq";
    let lastBatchRows = [];

    const $ = (id) => document.getElementById(id);
    const parseNums = (value) => (value || "").replace(/，/g, " ").replace(/,/g, " ").replace(/\+/g, " + ").trim().split(/\s+/).filter(Boolean).filter(item => item !== "+").map(Number);
    const fmt = (value) => String(value).padStart(2, "0");
    const game = () => DATA.games[currentLottery];
    const latest = () => game().records[game().records.length - 1];

    function recordGroups(lotteryId, record) {
      if (!record) return [[], []];
      if (lotteryId === "ssq") return [parseNums(record.Red), parseNums(record.Blue)];
      if (lotteryId === "dlt") return [parseNums(record.Front), parseNums(record.Back)];
      if (lotteryId === "qlc") return [parseNums(record.Main), parseNums(record.Special)];
      return [parseNums(record.Digit)];
    }

    function ballClass(area) {
      return area.color === "cool" ? "cool" : area.color === "neutral" ? "neutral" : "warm";
    }

    function ballsHtml(lotteryId, record) {
      const item = DATA.games[lotteryId];
      return recordGroups(lotteryId, record).map((group, index) => {
        const css = ballClass(item.areas[index] || item.areas[0]);
        return group.map(value => `<span class="ball ${css}">${fmt(value)}</span>`).join("");
      }).join("");
    }

    function renderHome() {
      $("disclaimerText").textContent = DATA.disclaimer;
      $("statusList").innerHTML = ORDER.map(id => {
        const item = DATA.games[id];
        return `<div class="status-row"><span>${item.name}</span><strong>${item.latestText}</strong></div>`;
      }).join("") + `<div class="status-row"><span>官方来源</span><strong>中国福彩网 / 中国体彩网</strong></div>`;
      $("lotteryGrid").innerHTML = ORDER.map(id => {
        const item = DATA.games[id];
        const draw = item.records[item.records.length - 1];
        return `<button class="lottery-card ${id === currentLottery ? "active" : ""}" data-lottery="${id}" type="button">
          <span class="lottery-card-head"><strong>${item.name}</strong><span class="source">${item.source}</span></span>
          <span class="balls">${ballsHtml(id, draw)}</span>
          <span class="lottery-meta">${item.latestText}<br>${item.drawDays}</span>
        </button>`;
      }).join("");
      document.querySelectorAll(".lottery-card").forEach(card => card.addEventListener("click", () => selectLottery(card.dataset.lottery, true)));
    }

    function selectLottery(lotteryId, scrollToDetail) {
      currentLottery = lotteryId;
      lastBatchRows = [];
      document.querySelectorAll(".lottery-card").forEach(card => card.classList.toggle("active", card.dataset.lottery === lotteryId));
      const item = game();
      const draw = latest();
      $("detailTitle").textContent = `${item.name}详情页`;
      $("detailSource").textContent = item.source;
      $("detailSync").textContent = item.latestText;
      $("detailBalls").innerHTML = ballsHtml(lotteryId, draw);
      $("detailRule").textContent = ruleText(item);
      renderOverview();
      renderHistory();
      renderChecker();
      renderStats();
      renderTrend();
      renderRecommend();
      if (scrollToDetail) $("detailPanel").scrollIntoView({ behavior:"smooth", block:"start" });
      history.replaceState(null, "", `#${lotteryId}`);
    }

    function ruleText(item) {
      return item.areas.map(area => `${area.label}${area.count}个，范围${area.min_number}-${area.max_number}${area.ordered ? "，按顺序" : ""}`).join("；") + "。";
    }

    function renderOverview() {
      const item = game();
      const draw = latest();
      $("overview").innerHTML = `<div class="feature-grid">
        <div class="feature"><strong>最新开奖</strong><span class="muted">${item.latestText}</span></div>
        <div class="feature"><strong>中奖核验</strong><span class="muted">按${item.name}独立规则核验，不硬套双色球。</span></div>
        <div class="feature"><strong>特色功能</strong><span class="muted">${featureText(currentLottery)}</span></div>
      </div>
      <div class="stat">
        <div class="head"><h3>${item.name}单彩种分析</h3><span class="muted">${item.drawDays}</span></div>
        <p class="muted">这里是从首页点击 ${item.name} 后展开的专属区域。用户不用在小按钮里猜，当前页面只围绕这个彩种做历史、核验、统计、走势和参考。</p>
        <div class="balls" style="margin-top:12px">${ballsHtml(currentLottery, draw)}</div>
      </div>`;
    }

    function featureText(id) {
      return {
        ssq:"红球/蓝球热冷分布、红球和值走势",
        dlt:"前区/后区分区频率、前区和值走势",
        fc3d:"直选/组选参考、三位数字按位观察",
        pl3:"三位数字按位核验与走势",
        pl5:"五位数字定位走势",
        qxc:"七位数字分位观察",
        qlc:"基本号/特别号分开分析"
      }[id] || "开奖数据统计";
    }

    function renderHistory(filter = "") {
      const item = game();
      const rows = item.records.slice(-60).reverse().filter(record => {
        if (!filter) return true;
        const haystack = `${record.Issue} ${record.Date} ${Object.values(record).join(" ")}`.toLowerCase();
        return haystack.includes(filter.toLowerCase());
      }).map(record => {
        const groups = recordGroups(currentLottery, record);
        return `<tr><td>${record.Issue}</td><td>${record.Date}</td><td>${groupBalls(groups[0], item.areas[0])}</td><td>${groups[1] ? groupBalls(groups[1], item.areas[1]) : '<span class="muted">无</span>'}</td></tr>`;
      }).join("");
      $("history").innerHTML = `<div class="panel">
        <div class="head"><h3>${item.name}历史查询</h3><span class="muted">最近60期，可用顶部搜索过滤</span></div>
        <div class="table-wrap"><table><thead><tr><th>期号</th><th>日期</th><th>一区/开奖号码</th><th>二区/特别号</th></tr></thead><tbody>${rows || '<tr><td colspan="4">没有匹配记录</td></tr>'}</tbody></table></div>
      </div>`;
    }

    function groupBalls(group, area) {
      const css = ballClass(area);
      return group.map(value => `<span class="ball ${css}">${fmt(value)}</span>`).join("");
    }

    function renderChecker() {
      const item = game();
      const special = item.areas[1];
      $("checker").innerHTML = `<div class="panel">
        <div class="head"><h3>${item.name}中奖核验</h3><span class="muted">结果仅供参考，以官方规则为准</span></div>
        <div class="form-grid" style="margin-top:12px">
          <div><label>${item.areas[0].label}</label><input id="mainNumbers" placeholder="${item.areas[0].count}个号码，范围${item.areas[0].min_number}-${item.areas[0].max_number}"></div>
          <div><label>${special ? special.label : "二区号码"}</label><input id="specialNumbers" placeholder="${special ? `${special.count}个号码，范围${special.min_number}-${special.max_number}` : "数字彩留空"}"></div>
        </div>
        <div class="actions">
          <button class="btn primary" id="checkSingle" type="button">核验当前号码</button>
          <button class="btn" id="fillExample" type="button">示例填入</button>
          <button class="btn" id="clearResult" type="button">清空结果</button>
        </div>
        <label style="display:block;margin-top:14px">批量核验（一行一注，前后区可用 + 分隔）</label>
        <textarea id="batchNumbers"></textarea>
        <div class="actions">
          <button class="btn" id="checkBatch" type="button">批量核验</button>
          <button class="btn" id="exportCsv" type="button">导出 CSV</button>
        </div>
        <div class="result" id="checkResult">请输入号码后核验。</div>
      </div>`;
      $("checkSingle").addEventListener("click", runSingleCheck);
      $("checkBatch").addEventListener("click", runBatchCheck);
      $("exportCsv").addEventListener("click", exportCsv);
      $("fillExample").addEventListener("click", fillExample);
      $("clearResult").addEventListener("click", () => {
        $("mainNumbers").value = "";
        $("specialNumbers").value = "";
        $("batchNumbers").value = "";
        $("checkResult").textContent = "已清空。";
        lastBatchRows = [];
      });
    }

    function validateTicket(mainNums, specialNums) {
      const areas = game().areas;
      const main = areas[0];
      const special = areas[1];
      if (mainNums.length !== main.count) return `${main.label}需要${main.count}个号码。`;
      if (special && specialNums.length !== special.count) return `${special.label}需要${special.count}个号码。`;
      if (!special && specialNums.length) return "这个彩种没有二区号码，第二栏请留空。";
      if (main.unique && new Set(mainNums).size !== mainNums.length) return `${main.label}不能重复。`;
      if (special && special.unique && new Set(specialNums).size !== specialNums.length) return `${special.label}不能重复。`;
      if (mainNums.some(value => value < main.min_number || value > main.max_number)) return `${main.label}超出范围。`;
      if (special && specialNums.some(value => value < special.min_number || value > special.max_number)) return `${special.label}超出范围。`;
      return "";
    }

    function checkTicket(mainNums, specialNums) {
      const groups = recordGroups(currentLottery, latest());
      if (game().areas.length === 1) {
        const exact = groups[0].length === mainNums.length && groups[0].every((value, index) => value === mainNums[index]);
        const orderedHits = mainNums.filter((value, index) => groups[0][index] === value).length;
        if (exact) return { level: currentLottery === "fc3d" || currentLottery === "pl3" ? "直选命中" : "命中开奖号码", mainHits: orderedHits, specialHits: 0 };
        if ((currentLottery === "fc3d" || currentLottery === "pl3") && [...groups[0]].sort().join(",") === [...mainNums].sort().join(",")) return { level:"组选参考命中", mainHits: orderedHits, specialHits: 0 };
        return { level:"未中奖", mainHits: orderedHits, specialHits: 0 };
      }
      const mainHits = mainNums.filter(value => groups[0].includes(value)).length;
      const specialHits = specialNums.filter(value => groups[1].includes(value)).length;
      const level = currentLottery === "ssq" ? checkSsq(mainHits, specialHits) : currentLottery === "dlt" ? checkDlt(mainHits, specialHits) : checkQlc(mainHits, specialHits);
      return { level, mainHits, specialHits };
    }

    function checkSsq(redHits, blueHits) {
      if (redHits === 6 && blueHits === 1) return "一等奖";
      if (redHits === 6) return "二等奖";
      if (redHits === 5 && blueHits === 1) return "三等奖";
      if (redHits === 5 || (redHits === 4 && blueHits === 1)) return "四等奖";
      if ((redHits === 4) || (redHits === 3 && blueHits === 1)) return "五等奖";
      if (blueHits === 1) return "六等奖";
      return "未中奖";
    }

    function checkDlt(frontHits, backHits) {
      if (frontHits === 5 && backHits === 2) return "一等奖";
      if (frontHits === 5 && backHits === 1) return "二等奖";
      if (frontHits === 5) return "三等奖";
      if (frontHits === 4 && backHits === 2) return "四等奖";
      if (frontHits === 4 && backHits === 1) return "五等奖";
      if (frontHits === 3 && backHits === 2) return "六等奖";
      if (frontHits === 4) return "七等奖";
      if ((frontHits === 3 && backHits === 1) || (frontHits === 2 && backHits === 2)) return "八等奖";
      if ((frontHits === 3) || (frontHits === 2 && backHits === 1) || (frontHits === 1 && backHits === 2) || (frontHits === 0 && backHits === 2)) return "九等奖";
      return "未中奖";
    }

    function checkQlc(mainHits, specialHits) {
      if (mainHits === 7 && specialHits === 1) return "一等奖";
      if (mainHits === 7) return "二等奖";
      if (mainHits === 6 && specialHits === 1) return "三等奖";
      if (mainHits === 6) return "四等奖";
      if (mainHits === 5 && specialHits === 1) return "五等奖";
      if ((mainHits === 5) || (mainHits === 4 && specialHits === 1)) return "六等奖";
      if (mainHits === 4) return "七等奖";
      return "未中奖";
    }

    function runSingleCheck() {
      const mainNums = parseNums($("mainNumbers").value);
      const specialNums = parseNums($("specialNumbers").value);
      const error = validateTicket(mainNums, specialNums);
      if (error) { $("checkResult").textContent = error; return; }
      const result = checkTicket(mainNums, specialNums);
      $("checkResult").textContent = `${game().name} ${latest().Issue}期：${result.level}\n一区/开奖号码命中 ${result.mainHits} 个${game().areas[1] ? `，二区命中 ${result.specialHits} 个` : ""}。\n提示：核验结果仅供参考，最终以官方兑奖规则为准。`;
    }

    function parseBatchLine(line) {
      const parts = line.split("+");
      if (parts.length === 2) return [parseNums(parts[0]), parseNums(parts[1])];
      const nums = parseNums(line);
      const mainCount = game().areas[0].count;
      return [nums.slice(0, mainCount), nums.slice(mainCount)];
    }

    function runBatchCheck() {
      const lines = $("batchNumbers").value.split(/\n+/).map(line => line.trim()).filter(Boolean);
      if (!lines.length) { $("checkResult").textContent = "请先粘贴要批量核验的号码。"; return; }
      lastBatchRows = [];
      const output = lines.map((line, index) => {
        const [mainNums, specialNums] = parseBatchLine(line);
        const error = validateTicket(mainNums, specialNums);
        if (error) {
          lastBatchRows.push([index + 1, line, "格式错误", error]);
          return `${index + 1}. 格式错误：${error}`;
        }
        const result = checkTicket(mainNums, specialNums);
        const hitText = game().areas[1] ? `一区${result.mainHits} 二区${result.specialHits}` : `按位命中${result.mainHits}`;
        lastBatchRows.push([index + 1, line, result.level, hitText]);
        return `${index + 1}. ${result.level}（${hitText}）`;
      });
      $("checkResult").textContent = output.join("\n");
    }

    function fillExample() {
      const groups = recordGroups(currentLottery, latest());
      $("mainNumbers").value = groups[0].map(fmt).join(" ");
      $("specialNumbers").value = groups[1] ? groups[1].map(fmt).join(" ") : "";
      $("batchNumbers").value = groups[1] ? `${groups[0].map(fmt).join(" ")} + ${groups[1].map(fmt).join(" ")}` : groups[0].map(fmt).join(" ");
      $("checkResult").textContent = "已填入最新开奖号作为示例。";
    }

    function exportCsv() {
      if (!lastBatchRows.length) runBatchCheck();
      if (!lastBatchRows.length) return;
      const csv = "序号,号码,结果,命中\n" + lastBatchRows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(",")).join("\n");
      const blob = new Blob(["\ufeff" + csv], { type:"text/csv;charset=utf-8" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${game().name}批量核验.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    }

    function renderStats() {
      const item = game();
      const blocks = item.areas.map((area, areaIndex) => {
        const counter = new Map();
        item.records.forEach(record => recordGroups(currentLottery, record)[areaIndex].forEach(value => counter.set(value, (counter.get(value) || 0) + 1)));
        const values = [];
        for (let value = area.min_number; value <= area.max_number; value++) values.push([value, counter.get(value) || 0]);
        const max = Math.max(...values.map(row => row[1]), 1);
        const avg = item.records.length * area.count / (area.max_number - area.min_number + 1);
        const rows = values.map(([value, count]) => {
          const tag = count >= avg * 1.08 ? "热" : count <= avg * 0.92 ? "冷" : "中";
          const css = ballClass(area);
          return `<div class="freq-row"><span class="mini-ball ${css}">${fmt(value)}</span><span class="track"><span class="fill ${css === "cool" ? "cool-fill" : ""}" style="width:${Math.round(count / max * 100)}%"></span></span><span>${count}次</span><span>${tag}</span></div>`;
        }).join("");
        return `<div class="panel"><div class="head"><h3>${item.name}${area.label}频率</h3><span class="muted">${area.min_number}-${area.max_number}</span></div><div class="freq-list" style="margin-top:12px">${rows}</div></div>`;
      }).join("");
      $("stats").innerHTML = `<div class="freq-grid">${blocks}</div>`;
    }

    function renderTrend() {
      const records = game().records.slice(-50);
      const values = records.map(record => recordGroups(currentLottery, record)[0].reduce((sum, value) => sum + value, 0));
      if (values.length < 2) { $("trend").innerHTML = '<div class="panel">暂无走势数据</div>'; return; }
      const width = 860, height = 260, left = 48, right = 18, top = 18, bottom = 36;
      const low = Math.min(...values) - 5, high = Math.max(...values) + 5, span = high - low || 1;
      const x = index => left + index / Math.max(1, values.length - 1) * (width - left - right);
      const y = value => top + (high - value) / span * (height - top - bottom);
      const path = values.map((value, index) => `${index ? "L" : "M"}${x(index).toFixed(1)},${y(value).toFixed(1)}`).join(" ");
      const avg = Math.round(values.reduce((a, b) => a + b, 0) / values.length * 10) / 10;
      const grid = [0,1,2,3,4].map(step => {
        const value = Math.round(low + (high - low) * step / 4);
        return `<line class="grid-line" x1="${left}" y1="${y(value).toFixed(1)}" x2="${width-right}" y2="${y(value).toFixed(1)}"></line><text class="axis" x="${left-8}" y="${y(value)+4}" text-anchor="end">${value}</text>`;
      }).join("");
      const dots = values.map((value, index) => `<circle class="trend-dot" cx="${x(index).toFixed(1)}" cy="${y(value).toFixed(1)}" r="3"><title>${records[index].Issue}期 ${records[index].Date}：${value}</title></circle>`).join("");
      $("trend").innerHTML = `<div class="panel"><div class="head"><h3>${game().name}近50期一区和值走势</h3><span class="muted">只看走势，不代表未来结果</span></div>
        <svg class="trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="近50期和值走势">${grid}<line class="avg-line" x1="${left}" y1="${y(avg)}" x2="${width-right}" y2="${y(avg)}"></line><text class="axis" x="${width-right-6}" y="${y(avg)-8}" text-anchor="end">均值 ${avg}</text><path class="trend-line" d="${path}"></path>${dots}</svg></div>`;
    }

    function renderRecommend() {
      const item = game();
      const parts = item.areas.map((area, areaIndex) => {
        const counter = new Map();
        item.records.forEach(record => recordGroups(currentLottery, record)[areaIndex].forEach(value => counter.set(value, (counter.get(value) || 0) + 1)));
        const sorted = [...counter.entries()].sort((a,b) => b[1] - a[1]).slice(0, area.count).map(row => fmt(row[0]));
        return `${area.label}：${sorted.join(" ")}`;
      });
      $("recommend").innerHTML = `<div class="panel"><div class="head"><h3>${item.name}统计参考</h3><span class="muted">不是预测</span></div>
        <div class="feature-grid" style="margin-top:12px">
          <div class="feature"><strong>参考组合 A</strong><p>${parts.join("　")}</p><small>依据：近期与历史频率混合观察。</small></div>
          <div class="feature"><strong>使用建议</strong><p class="muted">只适合做数据观察和娱乐参考。</p></div>
          <div class="feature"><strong>风险提示</strong><p class="muted">历史频率不能推出未来开奖号码。</p></div>
        </div></div>`;
    }

    function setSection(sectionId) {
      document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.section === sectionId));
      document.querySelectorAll(".section").forEach(section => section.classList.toggle("active", section.id === sectionId));
    }

    function runSearch() {
      const raw = $("globalSearch").value.trim();
      if (!raw) { $("detailPanel").scrollIntoView({ behavior:"smooth", block:"start" }); return; }
      const lower = raw.toLowerCase();
      const matchGame = ORDER.find(id => DATA.games[id].name.toLowerCase().includes(lower) || lower.includes(DATA.games[id].name.toLowerCase()));
      if (matchGame) selectLottery(matchGame, true);
      setSection("history");
      renderHistory(lower);
    }

    document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => setSection(tab.dataset.section)));
    $("searchBtn").addEventListener("click", runSearch);
    $("globalSearch").addEventListener("keydown", event => { if (event.key === "Enter") runSearch(); });

    renderHome();
    const initial = location.hash.replace("#", "");
    selectLottery(ORDER.includes(initial) ? initial : "ssq", false);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
