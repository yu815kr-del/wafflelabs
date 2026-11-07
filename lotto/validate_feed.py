#!/usr/bin/env python3
"""운담 로또 결과 파일(results-v1.json) 검증기 — 앱 LottoFeed.parse/merge 와 같은 규칙.
사용: python3 lotto/validate_feed.py FEED.json [--known lotto_dhlottery.json] [--prev prev.json]
경로는 현재 작업 디렉터리 기준 상대 경로. 표준 라이브러리만 사용. 종료코드 0=통과, 1=거부. 네트워크 사용 안 함."""
import json, sys, datetime as dt, argparse
MAX_BYTES, MAX_DRAWS = 512*1024, 5000
R1 = dt.date(2002, 12, 7)
def exp(r): return R1 + dt.timedelta(weeks=r-1)
def nodup(pairs):
    d = {}
    for k, v in pairs:
        if k in d: raise ValueError(f"duplicate key {k}")
        d[k] = v
    return d
def isint(v): return type(v) is int  # bool/float/str 거부
def load(path):
    b = open(path, 'rb').read()
    if len(b) > MAX_BYTES: raise ValueError("size > 512KiB")
    return json.loads(b.decode('utf-8'), object_pairs_hook=nodup, parse_float=lambda s: float(s), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
def check(o):
    req = ["schemaVersion", "source", "generatedAt", "latestRound", "draws"]
    for k in req:
        if k not in o: raise ValueError(f"missing {k}")
    if not isint(o["schemaVersion"]) or o["schemaVersion"] != 1: raise ValueError("schemaVersion")
    if not isinstance(o["source"], str) or not o["source"].strip() or len(o["source"]) > 300: raise ValueError("source")
    g = dt.datetime.fromisoformat(o["generatedAt"])
    if g.tzinfo is None: raise ValueError("generatedAt needs offset")
    gday = g.astimezone(dt.timezone(dt.timedelta(hours=9))).date()
    ds = o["draws"]
    if not isinstance(ds, list) or not (1 <= len(ds) <= MAX_DRAWS): raise ValueError("draws count")
    prev = None
    for i, d in enumerate(ds):
        if not isinstance(d, dict) or set(d) != {"round", "drawDate", "numbers", "bonus"}: raise ValueError(f"draw[{i}] keys")
        r = d["round"]
        if not isint(r) or not 1 <= r <= 100000: raise ValueError(f"draw[{i}] round")
        date = dt.date.fromisoformat(d["drawDate"])
        if len(d["drawDate"]) != 10 or date != exp(r) or date.weekday() != 5: raise ValueError(f"draw[{i}] date rule")
        if date > gday: raise ValueError(f"draw[{i}] after generatedAt")
        n = d["numbers"]
        if not isinstance(n, list) or len(n) != 6 or not all(isint(x) and 1 <= x <= 45 for x in n) or any(a >= b for a, b in zip(n, n[1:])): raise ValueError(f"draw[{i}] numbers")
        b = d["bonus"]
        if not isint(b) or not 1 <= b <= 45 or b in n: raise ValueError(f"draw[{i}] bonus")
        if prev is not None and r != prev + 1: raise ValueError(f"draw[{i}] sequence")
        prev = r
    if not isint(o["latestRound"]) or o["latestRound"] != prev: raise ValueError("latestRound != max(draws)")
    # 현재 시각(KST) 상한: 토 21:00 전 회차·미래 generatedAt 거부(앱과 동일)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    if g > now + dt.timedelta(minutes=10): raise ValueError("generatedAt in future")
    due = (now.date() - R1).days // 7 + 1
    if now.date() == exp(due) and now.time() < dt.time(21, 0): due -= 1
    if prev > due: raise ValueError(f"round {prev} not yet due (due {due})")
    return {d["round"]: (d["numbers"], d["bonus"], d["drawDate"]) for d in ds}
def known_from_asset(path):
    j = json.load(open(path, encoding='utf-8'))
    return {r[0]: (r[1:7], r[7], j.get("drawDates", {}).get(str(r[0]))) for r in j["draws"]}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("feed"); ap.add_argument("--known"); ap.add_argument("--prev")
    a = ap.parse_args()
    try:
        m = check(load(a.feed))
        for label, path, loader in (("known", a.known, known_from_asset), ("prev", a.prev, lambda p: check(load(p)))):
            if not path: continue
            k = loader(path); kl = max(k)
            if min(m) > kl + 1: raise ValueError(f"gap vs {label} (latest {kl})")
            if max(m) < kl: raise ValueError(f"regression vs {label}")
            for r, v in m.items():
                if r in k and (k[r][0] != v[0] or k[r][1] != v[1] or (k[r][2] and k[r][2] != v[2])): raise ValueError(f"mismatch round {r} vs {label}")
        print(f"OK rounds {min(m)}..{max(m)} ({len(m)}) bytes={len(open(a.feed,'rb').read())}")
        return 0
    except Exception as e:
        print("REJECT:", e); return 1
if __name__ == "__main__": sys.exit(main())
