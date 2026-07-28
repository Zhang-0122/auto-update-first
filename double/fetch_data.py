#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双色球历史数据采集 (Python版) — python fetch_data.py"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests, json, re, os, shutil, time
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
CACHE_DIR = os.path.join(PROJECT_ROOT, "cashe")
LOG_DIR = os.path.join(CACHE_DIR, "logs")
OUT = os.path.join(DIR, "ssq_data.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
TIMEOUT = 20

os.makedirs(LOG_DIR, exist_ok=True)


def log(message):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "fetch_data.log"), "a", encoding="utf-8") as file:
        file.write(f"[{stamp}] {message}\n")


def normalize_red(red):
    return ",".join(f"{int(value):02d}" for value in str(red).replace("，", ",").split(",") if value.strip())


def normalize_blue(blue):
    return f"{int(str(blue).strip()):02d}"


def validate_record(record):
    try:
        reds = [int(value) for value in record["Red"].split(",")]
        blue = int(record["Blue"])
        datetime.strptime(record["Date"], "%Y-%m-%d")
    except (KeyError, TypeError, ValueError):
        return False
    return len(reds) == 6 and len(set(reds)) == 6 and reds == sorted(reds) and all(1 <= value <= 33 for value in reds) and 1 <= blue <= 16


def load_existing():
    if not os.path.exists(OUT):
        return []
    with open(OUT, "r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []

def fetch_500(start, end):
    print(f"[1/3] 500.com {start}~{end} ...", end=" ")
    url = f"https://datachart.500.com/ssq/history/newinc/history.php?start={start}&end={end}"
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    resp.raise_for_status()
    resp.encoding = "gb2312"
    html = resp.text
    # 必须先删掉 HTML 注释，否则 <!--<td>2</td>--> 里的行号会被误当作期号
    html = re.sub(r"<!--.*?-->", "", html)
    rows = re.findall(r'<tr class="t_tr1">.*?<td>(\d+)</td>(.*?)</tr>', html, re.DOTALL)
    recs = []
    for issue, row in rows:
        reds = re.findall(r't_cfont2">(\d+)</td>', row)
        blue = re.search(r't_cfont4">(\d+)</td>', row)
        date = re.search(r'(\d{4}-\d{2}-\d{2})', row)
        if len(reds) >= 6 and blue and date:
            recs.append({"Issue": issue, "Date": date.group(1),
                         "Red": normalize_red(",".join(reds[:6])), "Blue": normalize_blue(blue.group(1))})
    print(f"OK {len(recs)} records")
    return recs

def fetch_cwl():
    print("[2/3] cwl.gov.cn ...", end=" ")
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=300"
    resp = requests.get(url, headers={"User-Agent": UA, "Referer": "https://www.cwl.gov.cn/"}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    recs = []
    if data.get("state") == 0:
        for item in data["result"]:
            issue = item["code"][-5:]
            recs.append({"Issue": issue,
                         "Date": item["date"].split("(")[0],
                         "Red": normalize_red(item["red"]), "Blue": normalize_blue(item["blue"])})
    else:
        raise RuntimeError(f"cwl.gov.cn 返回异常: {data.get('message', '未知错误')}")
    print(f"OK {len(recs)} records")
    return recs


def fetch_cwl_latest():
    print("[0/3] cwl.gov.cn latest ...", end=" ")
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=1"
    resp = requests.get(url, headers={"User-Agent": UA, "Referer": "https://www.cwl.gov.cn/"}, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if data.get("state") != 0 or not data.get("result"):
        raise RuntimeError(f"cwl.gov.cn 最新开奖结果查询异常: {data.get('message', '未知错误')}")
    item = data["result"][0]
    latest = {
        "Issue": item["code"][-5:],
        "Date": item["date"].split("(")[0],
        "Red": normalize_red(item["red"]),
        "Blue": normalize_blue(item["blue"]),
    }
    print(f"OK {latest['Issue']} {latest['Date']}")
    return latest


def save_records(records):
    valid = [record for record in records if validate_record(record)]
    if len(valid) != len(records):
        print(f"  注意：过滤无效记录 {len(records) - len(valid)} 条")
    if not valid:
        raise RuntimeError("没有拿到有效开奖记录，已保留原数据")
    valid = sorted(valid, key=lambda x: x["Date"])
    if os.path.exists(OUT):
        backup = os.path.join(CACHE_DIR, f"ssq_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(OUT, backup)
        log(f"已备份旧数据: {backup}")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(valid, f, ensure_ascii=False)
    return valid

def main():
    t0 = time.time()
    print("=" * 50)
    print("  双色球数据采集 v2.0 (Python)")
    print("=" * 50)
    try:
        latest_official = fetch_cwl_latest()
        existing = load_existing()
        if existing:
            current_latest = existing[-1]
            if (
                current_latest.get("Issue") == latest_official["Issue"]
                and current_latest.get("Date") == latest_official["Date"]
                and current_latest.get("Red") == latest_official["Red"]
                and current_latest.get("Blue") == latest_official["Blue"]
            ):
                print("[1/3] 官方最新开奖未变化，跳过同步。")
                print(f"  当前已同步到: {current_latest['Issue']}期 {current_latest['Date']}")
                log(f"无需同步: 当前已是最新 {current_latest['Issue']}期 {current_latest['Date']}")
                return
        current_year = datetime.now().year % 100
        end_issue = f"{current_year:02d}200"
        a = fetch_500("03001", end_issue)
        time.sleep(0.5)
        b = fetch_cwl()
        # 以期号为键去重
        seen = {}
        for r in a + b:
            seen[r["Issue"]] = r
        merged = save_records(seen.values())
        print(f"[3/3] 合并保存: {len(merged)} records -> {OUT}")
        print("=" * 50)
        print(f"  {merged[0]['Date']} ~ {merged[-1]['Date']}  共 {len(merged)} 期")
        print(f"  耗时 {time.time()-t0:.1f}s")
        print("=" * 50)
        log(f"刷新成功: {merged[0]['Date']} ~ {merged[-1]['Date']} 共 {len(merged)} 期")
    except Exception as exc:
        existing = load_existing()
        print("")
        print("刷新失败，但原有数据已保留，不影响继续使用。")
        if existing:
            print(f"当前仍可使用本地数据: {existing[0]['Date']} ~ {existing[-1]['Date']} 共 {len(existing)} 期")
        print(f"失败原因: {exc}")
        print(f"日志位置: {os.path.join(LOG_DIR, 'fetch_data.log')}")
        log(f"刷新失败: {exc}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
