#!/usr/bin/env python3
"""피드에 있는 회차를 동행복권 공식 조회와 읽기 전용으로 대조한다.
번호를 만들거나 피드 파일을 쓰지 않는다. 표준 라이브러리와 curl 만 사용한다.
사용: python3 lotto/compare_official.py lotto/results-v1.json [--round N]
--round 를 생략하면 피드에 이미 있는 회차만 조회한다.
"""
import argparse, json, subprocess, sys

URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd={round}"

def official(rnd):
    raw = subprocess.check_output([
        "curl", "-sS", "--max-time", "20",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Referer: https://www.dhlottery.co.kr/lt645/result",
        URL.format(round=rnd),
    ])
    body = json.loads(raw.decode("utf-8"))
    rows = (body.get("data") or {}).get("list") or []
    if len(rows) != 1:
        raise ValueError(f"round {rnd}: expected 1 official row, got {len(rows)}")
    row = rows[0]
    if row.get("ltEpsd") != rnd:
        raise ValueError(f"round {rnd}: official ltEpsd {row.get('ltEpsd')}")
    nums = [row[f"tm{i}WnNo"] for i in range(1, 7)]
    ymd = str(row["ltRflYmd"])
    if len(ymd) != 8 or not ymd.isdigit():
        raise ValueError(f"round {rnd}: ltRflYmd")
    return nums, row["bnsWnNo"], f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("feed")
    ap.add_argument("--round", type=int, action="append", dest="rounds")
    a = ap.parse_args()
    feed = json.load(open(a.feed, encoding="utf-8"))
    by = {d["round"]: d for d in feed["draws"]}
    rounds = a.rounds or sorted(by)
    bad = False
    for r in rounds:
        nums, bonus, date = official(r)
        d = by.get(r)
        if d is None:
            print(f"MISSING in feed {r} official {nums} bonus {bonus} {date}")
            print("feed was not modified")
            bad = True
            continue
        if d["numbers"] != nums or d["bonus"] != bonus or d["drawDate"] != date:
            print(f"MISMATCH {r} feed {d['numbers']} bonus {d['bonus']} {d['drawDate']} official {nums} bonus {bonus} {date}")
            bad = True
        else:
            print(f"MATCH {r} {nums} bonus {bonus} {date}")
    return 1 if bad else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("REJECT:", e)
        sys.exit(1)
