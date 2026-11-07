#!/usr/bin/env python3
"""직전 피드 뒤에, 운영자가 이미 확정한 회차만 이어 붙인다.
번호를 만들거나 추정하거나 네트워크를 쓰지 않는다. 기존 회차의 번호·보너스·날짜가 다르면 덮어쓰지 않고 거부한다.
사용: python3 lotto/merge_feed.py PREV.json INCOMING.json -o OUT.json --generated-at 'YYYY-MM-DDTHH:MM:SS+09:00'
쓴 뒤에는 validate_feed.py OUT.json --prev PREV.json 으로 전량 검사한다.
"""
import argparse, datetime as dt, json, pathlib, sys

def nodup(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key {k}")
        d[k] = v
    return d

def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"), object_pairs_hook=nodup)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prev")
    ap.add_argument("incoming")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--generated-at", required=True)
    a = ap.parse_args()
    g = dt.datetime.fromisoformat(a.generated_at)
    if g.tzinfo is None:
        raise ValueError("generated-at needs offset")
    prev = load(a.prev)
    inc = load(a.incoming)
    if prev.get("schemaVersion") != 1 or inc.get("schemaVersion") != 1:
        raise ValueError("schemaVersion")
    if not isinstance(prev.get("source"), str) or not prev["source"].strip():
        raise ValueError("source")
    pmap, imap = {}, {}
    for label, rows, dest in (("prev", prev.get("draws"), pmap), ("incoming", inc.get("draws"), imap)):
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{label} draws")
        for d in rows:
            r = d["round"]
            if r in dest:
                raise ValueError(f"duplicate round {r} in {label}")
            dest[r] = d
    for r, d in imap.items():
        if r not in pmap:
            continue
        old = pmap[r]
        if old["numbers"] != d["numbers"] or old["bonus"] != d["bonus"] or old["drawDate"] != d["drawDate"]:
            raise ValueError(f"existing round {r} differs; refuse overwrite")
    news = sorted(r for r in imap if r not in pmap)
    if not news:
        raise ValueError("no new rounds")
    last = max(pmap)
    expect = last
    for r in news:
        expect += 1
        if r != expect:
            raise ValueError(f"new rounds must continue from {last + 1}, got {r}")
    out = {
        "schemaVersion": 1,
        "source": prev["source"],
        "generatedAt": a.generated_at,
        "latestRound": news[-1],
        "draws": list(prev["draws"]) + [imap[r] for r in news],
    }
    text = json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n"
    pathlib.Path(a.output).write_text(text, encoding="utf-8")
    print(f"appended {news[0]}..{news[-1]} ({len(news)}) -> {a.output}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("REJECT:", e)
        sys.exit(1)
