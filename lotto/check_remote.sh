#!/bin/bash
# 읽기 전용 원격 확인. 게시, 커밋, force-push 를 하지 않는다.
# 저장소 루트에서 상대 경로로 실행한다.
#   ./lotto/check_remote.sh
#   KNOWN=path/to/lotto_dhlottery.json PREV=lotto/prev.json ./lotto/check_remote.sh
# KNOWN, PREV 를 생략하면 받은 본문의 형식만 검사한다. 경로는 현재 작업 디렉터리 기준이다.
set -u
URL="https://yu815kr-del.github.io/wafflelabs/lotto/results-v1.json"
D=$(cd "$(dirname "$0")" && pwd)
T=$(mktemp)
cleanup() { rm -f "$T"; }
trap cleanup EXIT
if ! code=$(curl -sS --max-time 15 --max-filesize 524288 -o "$T" -w '%{http_code}' "$URL"); then
  echo "curl failed $(date '+%F %T %Z')" >&2
  exit 2
fi
echo "HTTP $code $(date '+%F %T %Z')"
if [ "$code" != "200" ]; then
  exit 2
fi
args=()
if [ -n "${KNOWN:-}" ]; then
  args+=(--known "$KNOWN")
fi
if [ -n "${PREV:-}" ]; then
  args+=(--prev "$PREV")
fi
python3 "$D/validate_feed.py" "$T" "${args[@]}"
r=$?
python3 -c 'import hashlib,sys; p=sys.argv[1]; print(hashlib.sha256(open(p,"rb").read()).hexdigest(), p)' "$T"
exit "$r"
