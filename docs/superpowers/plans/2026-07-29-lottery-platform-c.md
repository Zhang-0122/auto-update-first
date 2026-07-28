# Lottery Platform C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing 双色球 dashboard into a public, compliant, multi-lottery data tool using C 方案 while preserving current 双色球 functionality.

**Architecture:** Add focused modules for lottery configuration, source fetching, and prize-rule checking. Keep the current standalone HTML build path, but make it consume multi-lottery data and publish `release/index.html` as before.

**Tech Stack:** Python 3.12, requests, static HTML/CSS/JavaScript, GitHub Actions, Netlify static hosting.

---

## File Structure

- Create `double/lottery_config.py`: central lottery definitions for 双色球 and 大乐透; later lotteries can be added here without copying UI logic.
- Create `double/lottery_sources.py`: official/public source fetchers and normalization helpers; cache/debug files go under `D:\SKILL DOUBLE rewards\cashe`.
- Create `double/lottery_rules.py`: independent prize-rule engine for 双色球 and 大乐透.
- Modify `double/fetch_data.py`: keep existing 双色球 fetch behavior and add 大乐透 fetch/save with failure protection.
- Modify `double/build_dashboard.py`: generate C 方案 multi-lottery public page, preserving双色球 history/statistics/checker/recommendation features.
- Modify `scripts/sync_release.py`: continue copying the generated dashboard to `release/index.html`.
- Modify `.github/workflows/update-lottery-data.yml`: include new data file in commits.
- Modify `scripts/check_live_site.py`: check new readable Chinese labels instead of mojibake-only labels.
- Create `double/tests/test_lottery_rules.py`: verify 双色球 and 大乐透 prize checks.
- Create `double/tests/test_lottery_config.py`: verify config does not hard-code双色球 ranges into 大乐透.

---

### Task 1: Add 彩种配置

**Files:**
- Create: `double/lottery_config.py`
- Test: `double/tests/test_lottery_config.py`

- [ ] **Step 1: Write config tests**

```python
from lottery_config import LOTTERIES


def test_ssq_and_dlt_have_independent_ranges():
    assert LOTTERIES["ssq"].areas[0].max_number == 33
    assert LOTTERIES["ssq"].areas[1].max_number == 16
    assert LOTTERIES["dlt"].areas[0].max_number == 35
    assert LOTTERIES["dlt"].areas[1].max_number == 12


def test_each_lottery_has_source_and_disclaimer_name():
    assert LOTTERIES["ssq"].official_source == "中国福彩网"
    assert LOTTERIES["dlt"].official_source == "中国体彩网"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest double/tests/test_lottery_config.py -q`
Expected: FAIL because `lottery_config` does not exist yet.

- [ ] **Step 3: Implement config module**

Create dataclasses `NumberArea` and `LotteryConfig`, then define `LOTTERIES` with `ssq` and `dlt`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest double/tests/test_lottery_config.py -q`
Expected: PASS.

---

### Task 2: Add 中奖规则引擎

**Files:**
- Create: `double/lottery_rules.py`
- Test: `double/tests/test_lottery_rules.py`

- [ ] **Step 1: Write rule tests**

```python
from lottery_rules import check_prize


def test_ssq_first_and_sixth_prize():
    draw = {"Red": "01,02,03,04,05,06", "Blue": "07"}
    assert check_prize("ssq", draw, [[1,2,3,4,5,6], [7]])["level"] == "一等奖"
    assert check_prize("ssq", draw, [[8,9,10,11,12,13], [7]])["level"] == "六等奖"


def test_dlt_first_and_ninth_prize():
    draw = {"Front": "01,02,03,04,05", "Back": "06,07"}
    assert check_prize("dlt", draw, [[1,2,3,4,5], [6,7]])["level"] == "一等奖"
    assert check_prize("dlt", draw, [[1,2,8,9,10], [6,7]])["level"] == "九等奖"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest double/tests/test_lottery_rules.py -q`
Expected: FAIL because `lottery_rules` does not exist yet.

- [ ] **Step 3: Implement prize checker**

Implement `check_prize(lottery_id, draw, ticket)` with separate 双色球 and 大乐透 mapping tables.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest double/tests/test_lottery_rules.py -q`
Expected: PASS.

---

### Task 3: Add 大乐透 data fetch

**Files:**
- Create: `double/lottery_sources.py`
- Modify: `double/fetch_data.py`

- [ ] **Step 1: Implement 体彩 source fetcher**

Use `https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo=N` with `User-Agent` and `Referer` headers.

- [ ] **Step 2: Normalize 大乐透 records**

Record shape: `{"Issue":"26084","Date":"2026-07-27","Front":"13,25,30,32,33","Back":"04,05"}`.

- [ ] **Step 3: Save with failure protection**

Write to `double/dlt_data.json` only when at least one valid record exists; back up old data to `cashe` before overwriting.

- [ ] **Step 4: Run fetch command**

Run: `python -B double/fetch_data.py`
Expected: 双色球 remains available and 大乐透 data file exists or old data is preserved with clear warning.

---

### Task 4: Build C 方案 page

**Files:**
- Modify: `double/build_dashboard.py`

- [ ] **Step 1: Load multi-lottery data**

Load `ssq_data.json` and `dlt_data.json` if present; preserve current双色球 calculations.

- [ ] **Step 2: Add C 方案 top layout**

Add title “彩票开奖数据中心”, unified search, lottery cards, sync status, official source, and visible disclaimer.

- [ ] **Step 3: Preserve 双色球 functions**

Keep history table, red/blue frequency, trend, recommendation, single check, and batch check.

- [ ] **Step 4: Add 大乐透 display and checker**

Show latest 大乐透, history rows, front/back frequency, and basic prize checker.

---

### Task 5: Update release and workflows

**Files:**
- Modify: `scripts/check_live_site.py`
- Modify: `.github/workflows/update-lottery-data.yml`

- [ ] **Step 1: Update commit paths**

Add `double/dlt_data.json` to the workflow commit step.

- [ ] **Step 2: Update health checks**

Check for “彩票开奖数据中心”, “官方来源”, “免责声明”, “已同步到”, “双色球”, and “大乐透”.

- [ ] **Step 3: Sync release**

Run: `python scripts/sync_release.py`
Expected: `release/index.html` matches generated dashboard.

---

### Task 6: Verify locally

**Files:**
- Generated: `double/ssq_analyzer.html`
- Generated: `release/index.html`

- [ ] **Step 1: Run tests**

Run: `python -m pytest double/tests -q`
Expected: PASS.

- [ ] **Step 2: Build page**

Run: `python -B double/build_dashboard.py`
Expected: dashboard generated without errors.

- [ ] **Step 3: Sync release**

Run: `python scripts/sync_release.py`
Expected: release index updated.

- [ ] **Step 4: Check no scattered cache**

Run: `Get-ChildItem -Recurse cashe | Select-Object -First 20`
Expected: logs/debug/cache files are under `cashe`.

---

## Self-Review

- Spec coverage: C 方案, compliance, multi-lottery config, rule engine, auto update, cache directory, and preserving 双色球 are covered.
- Placeholder scan: no implementation step depends on an undefined future decision.
- Type consistency: `Issue`, `Date`, `Red`, `Blue`, `Front`, and `Back` are used consistently.
