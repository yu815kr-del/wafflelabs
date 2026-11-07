# 운담 로또 결과 파일

앱이 읽는 고정 주소는 `https://yu815kr-del.github.io/wafflelabs/lotto/results-v1.json` 이다.

이 저장소의 GitHub Pages 원본은 `main` 브랜치의 `/` 이다(2026-11-07 확인). **pull request 는 공개 페이지를 바꾸지 않는다.** `main` 에 머지되고 Pages 배포가 끝난 뒤에만 위 주소의 본문이 바뀐다. 배포 전 확인 결과는 아래 「200 본문 검증」에 적었다.

번호는 만들지 않는다. 1249회는 이 파일에 없다. 이 준비에서는 1249회를 조회하거나 추정하지 않았다.

## 지금 파일

| 항목 | 값 |
|---|---|
| 경로 | `lotto/results-v1.json` |
| 내용 | 1248회 1건. 본번호 16, 18, 27, 36, 38, 42 / 보너스 22 / 추첨일 2026-10-31 |
| sha256 | `071db084275feb80269df2afaec0d294f7cd4c26fc4d1aab0e0bc89f8b1111d5` |
| 바이트 | 321 (끝에 개행 1개) |

저장소에 기존 `lotto/results-v1.json` 은 없었다. 첨부된 초기 파일을 그대로 넣었고, 다시 직렬화하지 않았다.

2026-11-07 공식 대조: `python3 lotto/compare_official.py lotto/results-v1.json` → `MATCH 1248 [16, 18, 27, 36, 38, 42] bonus 22 2026-10-31`. 조회 주소는 동행복권 `https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do?srchLtEpsd=1248` 이고, 응답의 `tm1WnNo`–`tm6WnNo`, `bnsWnNo`, `ltRflYmd=20261031` 과 같았다. 제3자 번호는 쓰지 않았다.

## 검사 규칙

`lotto/validate_feed.py` 는 표준 라이브러리만 쓰고 네트워크를 쓰지 않는다. 경로는 현재 작업 디렉터리 기준이다. 하나라도 어긋나면 종료코드 1 이다.

- 최상위 키: `schemaVersion`, `source`, `generatedAt`, `latestRound`, `draws`. 중복 키 거부.
- `schemaVersion` 은 정수 1. 참/거짓, 소수, 문자열 숫자는 정수가 아니다.
- `source` 는 공백이 아닌 문자열이고 300자 이하.
- `generatedAt` 은 시간대 오프셋이 있는 ISO-8601. 한국 표준시 현재보다 10분을 넘겨 미래이면 거부.
- 파일 512 KiB 이하. `draws` 는 1건 이상 5000건 이하.
- 각 회차 키는 `round`, `drawDate`, `numbers`, `bonus` 만.
- `round` 는 1 이상 100000 이하의 정수. 회차는 1씩 연속.
- `drawDate` 는 `YYYY-MM-DD` 이고 `2002-12-07 + 7일 × (round-1)` 인 토요일. `generatedAt` 의 한국 표준시 날짜보다 뒤이면 거부.
- `numbers` 는 1 이상 45 이하의 정수 6개, 오름차순, 중복 없음.
- `bonus` 는 1 이상 45 이하의 정수이고 본번호와 다르다.
- `latestRound` 는 마지막 회차와 같다.
- 예정 시각: 1회 추첨일 2002-12-07 부터 센 이번 토요일 회차는, 그 토요일 21:00(한국 표준시) 전이면 아직 아니다. 그보다 큰 회차는 거부.
- `--prev` 또는 `--known`: 겹치는 회차의 번호·보너스·날짜가 다르면 거부, 피드가 기준보다 이전으로 줄어들면 거부(회귀), 기준 최신과 피드 첫 회차 사이에 빈 회차가 있으면 거부. `--known` 은 앱 asset `lotto_dhlottery.json` 형식(`draws` 행 `[회차, 번호 6개, 보너스]`, 선택적 `drawDates`)이다. 그 asset 은 이 저장소에 없다.

## 명령

작업 디렉터리는 저장소 루트다. Python 3 과 curl 만 사용한다. `git push --force` 는 쓰지 않는다.

### 1. 공식 자료 대조

피드에 이미 있는 회차만 공식 조회와 비교한다. 파일을 수정하지 않는다.

```bash
python3 lotto/compare_official.py lotto/results-v1.json
```

`MATCH` 만 나오고 종료코드 0 이어야 한다. 사람이 동행복권 회차 결과 화면과 엑셀을 다시 보는 대조는 그대로 둔다. 이 명령은 그 번호의 기계 대조이고, 번호의 출처가 아니다.

새 회차를 넣기 전에, 공식 자료에서 확정한 회차 번호만 지정한다. 피드에 없으면 `MISSING` 을 출력하고 끝난다. 파일을 만들지 않는다.

```bash
python3 lotto/compare_official.py lotto/results-v1.json --round <확정한 회차>
```

### 2. 누적 병합

운영자가 확정한 회차만 `lotto/incoming.json` 에 같은 스키마로 적는다. 추정 번호는 적지 않는다. `incoming.json` 은 게시 파일이 아니므로 커밋하지 않는다.

직전 게시본을 먼저 복사한다.

```bash
cp lotto/results-v1.json /tmp/results-v1.prev.json
python3 lotto/merge_feed.py /tmp/results-v1.prev.json lotto/incoming.json \
  -o /tmp/results-v1.next.json \
  --generated-at 'YYYY-MM-DDTHH:MM:SS+09:00'
```

기존 회차의 번호, 보너스, 날짜가 다르면 덮어쓰지 않고 종료코드 1 이다. 새 회차는 직전 최신의 다음 번호부터 연속이어야 한다. 네트워크로 회차를 가져오지 않는다.

### 3. 전량 검사

```bash
python3 lotto/validate_feed.py /tmp/results-v1.next.json --prev /tmp/results-v1.prev.json
```

앱 asset 이 작업 디렉터리에서 보이는 상대 경로에 있을 때만 추가한다.

```bash
python3 lotto/validate_feed.py /tmp/results-v1.next.json \
  --prev /tmp/results-v1.prev.json \
  --known path/to/lotto_dhlottery.json
```

`OK` 와 종료코드 0 다음에만 교체한다.

```bash
cp /tmp/results-v1.next.json lotto/results-v1.json
python3 lotto/compare_official.py lotto/results-v1.json
python3 -c 'import hashlib; print(hashlib.sha256(open("lotto/results-v1.json","rb").read()).hexdigest())'
```

### 4. 정상 git 게시

공개 반영은 `main` 머지 후의 Pages 배포다. 결과 번호만 바꿀 때는 `lotto/results-v1.json` 만 스테이징한다.

```bash
git diff -- lotto/results-v1.json
git add lotto/results-v1.json
git commit -m "로또 결과 피드에 확정 회차를 추가"
git push origin HEAD
```

`--force` 를 붙이지 않는다. 루트 workflow 와 dependency 파일은 이 절차에서 변경하지 않는다. `main` 으로의 머지는 diff 와 CI 를 본 뒤 한다.

### 5. 200 본문 검증

`main` 배포 뒤에 실행한다. 받은 본문을 검사하고 sha256 을 출력한다. 쓰기는 없다.

```bash
./lotto/check_remote.sh
PREV=/tmp/results-v1.prev.json ./lotto/check_remote.sh
```

`HTTP 200` 다음에 `OK`, 그리고 로컬 파일과 같은 sha256 이어야 한다. `KNOWN` 과 `PREV` 는 현재 디렉터리 기준 상대 경로다. 생략하면 본문 형식만 본다. 스크립트 위치와 무관하게 `lotto/validate_feed.py` 를 찾는다.

2026-11-07 13:05:28 UTC 에 이 환경에서 `./lotto/check_remote.sh` 를 실행한 출력은 `HTTP 404 2026-11-07 13:05:28 UTC`, 종료코드 2 였다. 공개 주소에는 아직 이 파일이 없다.

## 롤백

형식 오류 파일은 검증기가 전체를 거부한다. 잘못된 게시본은 직전 정상 파일을 되돌리는 일반 커밋으로 교체한 뒤 5번을 다시 실행한다. force-push 로 되돌리지 않는다.

이미 앱이 받아 둔 회차의 번호를 나중에 고치면, 검증기는 `--prev` 대조에서 그 회차를 불일치로 거부한다. 앱 저장소는 이 작업 범위 밖이라 앱 코드를 다시 열지 않았다. 함께 온 운영 메모는, 이미 받은 기기 캐시는 파일만 바꿔서는 자동으로 고쳐지지 않고 앱 갱신이 따로 필요하다고 적는다.

## GitHub Pages 제한

2026-11-07 에 연 공식 문서 원문이다. 허용된다는 판단은 아니다.

[GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits):

> GitHub Pages is not intended for or allowed to be used as a free web-hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS). GitHub Pages sites shouldn't be used for sensitive transactions like sending passwords or credit card numbers.

같은 문서의 한도: 원본 저장소 권장 1 GB, 게시된 사이트 1 GB 이하, 배포 10분 초과 시 시간 초과, 대역폭 월 100 GB 소프트 한도, 시간당 빌드 10회 소프트 한도(사용자 지정 GitHub Actions workflow 로 빌드·게시하면 이 빌드 한도는 적용되지 않음), 속도 제한 시 HTTP `429`.

[GitHub Terms for Additional Products and Features](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features) (Version Effective Date: August 27, 2026) Pages:

> GitHub Pages is intended to host static web pages, but primarily as a showcase for personal and organizational projects.
>
> GitHub Pages is not intended for or allowed to be used as a free web hosting service to run your online business, e-commerce site, or any other website that is primarily directed at either facilitating commercial transactions or providing commercial software as a service (SaaS).

> If you have questions about whether your use or intended use falls into these categories, please contact us through the GitHub Support portal.

이 변경은 공개 추첨 결과 정적 JSON 한 개다. 결제, 비밀번호, 카드번호를 받지 않고 Pages 위에서 앱을 실행하지도 않는다. 공식 원문은 이 파일 형태를 금지 대상으로 지목하지 않는다. 동시에, 용도가 위 문장에 들어가는지는 Support 에 묻게 되어 있으므로 **허용을 보증하지 않는다.** 온라인 사업이나 SaaS 호스팅으로 보는 해석이 가능하면 게시 전에 그 판단을 따로 해야 한다. 원문이 이 용도를 명백히 금지한다고 보지는 않아 파일 준비는 중단하지 않았다.

## 호스트의 IP 기록

[What is GitHub Pages?](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages) Data collection 원문:

> When a GitHub Pages site is visited, the visitor's IP address is logged and stored for security purposes, regardless of whether the visitor has signed into GitHub or not.

결과 파일을 요청하면 호스트인 GitHub 가 방문자 IP 를 보안 목적으로 기록할 수 있다. 이 운영 절차는 그 로그를 받아 오지 않는다. `privacy/undam/` 한·영 최종 HTML 은 부모가 보내는 파일만 사용한다. 이 준비에서 개인정보 문안을 쓰거나 기존 방침을 고치지 않았다.
