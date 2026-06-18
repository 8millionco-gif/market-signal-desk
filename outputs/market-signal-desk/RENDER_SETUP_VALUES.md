# Render 입력값

GitHub 업로드가 끝난 뒤 Render에서 Blueprint를 만들 때 아래 값을 기준으로 입력합니다.

## GitHub 저장소

```text
https://github.com/8millionco-gif/market-signal-desk
```

## Blueprint 기준 파일

현재 저장소 루트의 `render.yaml`을 사용합니다.

```text
render.yaml
```

이 파일은 앱 경로를 아래처럼 지정합니다.

```text
rootDir: outputs/market-signal-desk
```

## 서비스 설정

Render Blueprint가 자동으로 읽는 값입니다.

```text
Service Type: Web Service
Name: market-signal-desk
Runtime: Python
Plan: Free
Build Command: pip install -r requirements.txt
Start Command: python server.py
Health Check Path: /api/health
```

## 첫 배포에 반드시 넣을 비밀값

초기 배포에서는 아래 하나만 실제 값으로 넣습니다.

```text
ADMIN_TOKEN=직접_정한_긴_랜덤_문자열
```

권장 예시는 최소 24자 이상입니다. 브라우저에서 접속 후 같은 값을 관리자 토큰 입력창에 넣습니다.

## 첫 배포에서는 비워도 되는 비밀값

초기 스테이징에서는 아래 값은 비워두거나 나중에 Render Environment에서 추가합니다.

```text
TOSS_CLIENT_ID=
TOSS_CLIENT_SECRET=
DART_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
OPENAI_API_KEY=
```

## 첫 배포 기본 플래그

초기에는 외부 API 호출량을 막기 위해 아래 값이 `render.yaml`에서 꺼져 있습니다.
수동 Web Service 생성으로 `render.yaml` 값이 일부 적용되지 않더라도, 스케줄러와 GDELT 글로벌 뉴스는 코드 기본값도 꺼짐으로 둡니다.

```text
SIGNAL_SCHEDULER_ENABLED=0
TOSS_LIVE_PRICES=0
TOSS_LIVE_CANDLES=0
TOSS_LIVE_ORDERBOOK=0
TOSS_LIVE_TRADES=0
TOSS_LIVE_PORTFOLIO=0
DART_LIVE_DISCLOSURES=0
NAVER_LIVE_NEWS=0
GDELT_LIVE_NEWS=0
OPENAI_ANALYSIS_ENABLED=0
```

시장 지표와 환율은 첫 화면 확인을 위해 켜져 있습니다.

```text
MARKET_INDEX_LIVE=1
FX_LIVE_RATES=1
```

## 배포 후 확인 URL

배포 주소가 예를 들어 `https://market-signal-desk.onrender.com`이면 아래 순서로 확인합니다.

```text
https://market-signal-desk.onrender.com/api/health
https://market-signal-desk.onrender.com/api/auth/status
https://market-signal-desk.onrender.com
```

정상 기준:

```text
/api/health        ok: true
/api/auth/status   enabled: true
첫 화면             관리자 토큰 입력 후 후보 화면 표시
```

터미널에서는 아래 스크립트로 같은 검사를 한 번에 실행할 수 있습니다.

```powershell
.\test-render-deploy.ps1
```

관리자 토큰을 보안 입력으로 받은 뒤 헬스 체크, 인증 보호, 대시보드, 뉴스 상태, 스케줄러 상태를 확인합니다.

## 다음 활성화 순서

첫 화면이 정상인 뒤 아래 순서대로 하나씩 켭니다.

```text
0. DATABASE_URL / SIGNAL_STORAGE_BACKEND=auto
1. SIGNAL_AUTO_CANDIDATES_ENABLED=1
2. GDELT_LIVE_NEWS=1
3. NAVER_CLIENT_ID / NAVER_CLIENT_SECRET / NAVER_LIVE_NEWS=1
4. DART_API_KEY / DART_LIVE_DISCLOSURES=1
5. OPENAI_API_KEY / OPENAI_ANALYSIS_ENABLED=1
6. Toss 키와 Toss live flags
7. TOSS_LIVE_PORTFOLIO=1
8. SIGNAL_SCHEDULER_ENABLED=1
```

## DB 저장소 활성화

실전 운영 전에는 파일 저장소 대신 Postgres DB를 먼저 연결합니다. Render Postgres 또는 Supabase Postgres에서 발급한 연결 문자열을 Render Environment에 추가합니다.

```text
SIGNAL_STORAGE_BACKEND=auto
DATABASE_URL=postgresql://...
SIGNAL_DB_AUTO_MIGRATE=1
SIGNAL_DB_MIGRATE_RUN_LIMIT=200
```

앱은 DB 연결이 가능하면 `signal_kv`, `signal_snapshots` 테이블을 자동 생성합니다. `SIGNAL_DB_AUTO_MIGRATE=1`이면 기존 파일 저장소에 남은 후보 풀, 최신 발굴 결과, 최근 스냅샷을 DB에 한 번 자동 이관합니다.

DB에 저장되는 데이터:

```text
candidate_pool          후보 풀
discovery_latest        상시 발굴 봇 최신 결과
signal_snapshots        장전/장마감/장중 스냅샷과 성과 검증 기준 데이터
```

DB가 연결되지 않으면 기존처럼 `data/*.json`, `data/runs/*.json` 파일 저장소로 대체됩니다. Render 무료 웹 서비스의 파일 저장소는 재배포/재시작 시 유지가 보장되지 않으므로, 후보 풀과 성과 기록을 운영에 쓰려면 `DATABASE_URL` 연결이 필요합니다.

GDELT는 요청 제한이 있으므로 처음에는 아래 기본값을 유지합니다.

```text
GDELT_NEWS_MAX_CANDIDATES=1
GDELT_REQUEST_TIMEOUT_SECONDS=20
GDELT_REQUEST_SPACING_SECONDS=5.2
```

자동 후보 생성 기본값은 아래처럼 둡니다. 네이버 뉴스 활성화 전에는 유니버스 기본 점수로 후보를 구성하고, 네이버 뉴스 활성화 후에는 뉴스 스캔 결과가 후보 선정에 반영됩니다. 종목명, 티커, 별칭이 제목이나 요약에 맞지 않는 뉴스는 제외되며 화면의 `오늘의 후보` 아래에 제외 건수가 표시됩니다.

```text
SIGNAL_AUTO_CANDIDATES_ENABLED=1
SIGNAL_AUTO_CANDIDATE_LIMIT=20
SIGNAL_DOMESTIC_CANDIDATE_LIMIT=10
SIGNAL_OVERSEAS_CANDIDATE_LIMIT=10
SIGNAL_DISCOVERY_MAX_SYMBOLS=40
SIGNAL_DISCOVERY_NEWS_DISPLAY=3
SIGNAL_DISCOVERY_CACHE_SECONDS=600
SIGNAL_DISCOVERY_BOT_ENABLED=1
SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS=600
SIGNAL_DISCOVERY_BOT_MODE=intraday
```

화면에서 `뉴스 소스 상태 > 글로벌 출처`가 `제한`으로 표시되면 GDELT 요청 제한입니다. 몇 분 뒤 새로고침하거나 후보 조회 수를 1로 유지한 상태에서 다시 확인합니다.

## 네이버 뉴스 활성화

GDELT가 확인되면 Render Environment에 아래 값을 추가합니다.

```text
NAVER_CLIENT_ID=네이버_애플리케이션_Client_ID
NAVER_CLIENT_SECRET=네이버_애플리케이션_Client_Secret
NAVER_LIVE_NEWS=1
```

저장 후 재배포가 끝나면 아래 스크립트를 실행합니다.

```powershell
.\test-render-deploy.ps1
```

정상 기준:

```text
Naver news status      ready=True
Naver dashboard source source=naver
Naver search API       items=1개 이상
Candidate source       auto-news
```

## OpenDART 공시 활성화

네이버 뉴스까지 확인되면 Render Environment에 아래 값을 추가합니다.

```text
DART_API_KEY=OpenDART_API_Key
DART_LIVE_DISCLOSURES=1
```

선택값은 기본값을 그대로 사용해도 됩니다.

```text
DART_DISCLOSURE_LOOKBACK_DAYS=7
DART_DISCLOSURE_MAX_CANDIDATES=2
DART_REQUEST_TIMEOUT_SECONDS=6
DART_CORP_CODE_TIMEOUT_SECONDS=10
```

저장 후 재배포가 끝나면 아래 스크립트를 실행합니다.

```powershell
.\test-render-deploy.ps1
```

정상 기준:

```text
OpenDART status           ready=True
OpenDART dashboard source source=opendart
OpenDART corp code        symbol=005930
OpenDART disclosures API  source=opendart
```

## OpenAI 분석 활성화

OpenDART 공시까지 확인되면 Render Environment에 아래 값을 추가합니다.

```text
OPENAI_API_KEY=OpenAI_API_Key
OPENAI_ANALYSIS_ENABLED=1
OPENAI_MODEL=gpt-5.4
```

선택값은 처음에는 보수적으로 둡니다.

```text
OPENAI_ANALYSIS_MAX_CANDIDATES=1
OPENAI_ANALYSIS_CACHE_SECONDS=900
OPENAI_REQUEST_TIMEOUT_SECONDS=30
```

저장 후 재배포가 끝나면 아래 스크립트를 실행합니다.

```powershell
.\test-render-deploy.ps1
```

정상 기준:

```text
OpenAI status           ready=True
OpenAI dashboard source source=openai
OpenAI analyze API      source=openai
```

모델 권한이나 모델명이 맞지 않으면 화면은 자동으로 로컬 분석을 사용하고, 테스트 결과에 OpenAI 오류 사유가 표시됩니다. 이 경우 `OPENAI_MODEL`을 계정에서 사용 가능한 모델명으로 바꾼 뒤 다시 배포합니다.

## Toss 실시간 시세 활성화

OpenAI 분석까지 확인되면 Render Environment에 아래 값을 추가합니다.

```text
TOSS_CLIENT_ID=토스증권_API_Key
TOSS_CLIENT_SECRET=토스증권_Secret_Key
TOSS_LIVE_PRICES=1
TOSS_LIVE_CANDLES=1
TOSS_LIVE_ORDERBOOK=1
TOSS_LIVE_TRADES=1
TOSS_LIVE_PORTFOLIO=0
```

선택값은 처음에는 후보 수를 작게 둡니다.

```text
TOSS_CANDLE_MAX_CANDIDATES=2
TOSS_ORDERBOOK_MAX_CANDIDATES=2
TOSS_TRADES_MAX_CANDIDATES=2
TOSS_TRADES_COUNT=30
TOSS_PORTFOLIO_CACHE_SECONDS=30
TOSS_STOCK_CACHE_SECONDS=86400
TOSS_REQUEST_TIMEOUT_SECONDS=8
TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT=50
```

토스증권 Open API에서 허용 IP를 관리한다면 Render 서버의 외부 IP가 허용 IP에 등록되어 있어야 합니다. IP가 맞지 않으면 테스트에서 `Toss prices API` 또는 토큰 발급 단계가 `CHECK`로 표시됩니다.

Render의 outbound IP는 서비스 상세 화면에서 `Connect` 드롭다운을 열고 `Outbound` 탭에서 확인합니다. 앱 화면의 `Render 외부 IP` 카드와 `test-render-deploy.ps1`의 `Render outbound IP` 항목은 현재 서버가 외부에서 보이는 IP를 보여줍니다.

Toss가 CIDR 범위를 허용하면 Render `Outbound` 탭의 IP 범위를 등록합니다. Toss가 단일 IP만 허용하면 앱에 표시된 현재 IP를 먼저 등록해 테스트하고, 안정 운영에는 Render Dedicated Outbound IP 또는 고정 IP 프록시가 필요할 수 있습니다.

저장 후 재배포가 끝나면 아래 스크립트를 실행합니다.

```powershell
.\test-render-deploy.ps1
```

정상 기준:

```text
Toss status              ready=True
Toss dashboard prices    source=toss
Toss dashboard candles   source=toss
Toss dashboard orderbook source=toss
Toss dashboard trades    source=toss
Toss prices API          items=1개 이상
Toss candles API         items=1개 이상
Toss orderbook API       symbol=005930
Toss trades API          items=1개 이상
```

현재가만 먼저 확인하고 싶으면 `TOSS_LIVE_PRICES=1`만 켜고 나머지 live 플래그는 `0`으로 둡니다. 화면 가격이 안정적으로 맞으면 차트, 호가, 체결 순서로 하나씩 켭니다.

가격, 차트, 호가, 체결이 안정적으로 확인된 뒤 내 보유 종목을 판단에 반영하려면 Render Environment에서 `TOSS_LIVE_PORTFOLIO=1`을 추가합니다. 여러 계좌가 있으면 `TOSS_ACCOUNT_SEQ`도 함께 지정합니다. 이 단계는 계좌 목록, 보유 주식, 매수 가능 금액만 읽으며 주문 실행은 하지 않습니다.

정상 기준:

```text
Toss portfolio API      account=****1234, holdings=보유 종목 수, readOnly=True
화면 포트폴리오 상태     자산 조회 읽기 가능
```

화면에서 `토큰 발급 준비됨`, `시세 조회 가능`인데도 가격/차트/호가/체결 출처가 `샘플`이면 live 플래그가 꺼져 있는 상태일 가능성이 큽니다. 이때는 먼저 `TOSS_LIVE_PRICES=1`만 켜고 재배포한 뒤 가격 출처가 `토스`로 바뀌는지 확인합니다.

화면에서 가격/차트/호가/체결 출처가 `오류`로 나오면 재배포 후 `.\test-render-deploy.ps1`을 실행해 상세 사유를 확인합니다.

```text
HTTP 401 또는 토큰/키 확인   API Key / Secret Key 값 확인
HTTP 403 또는 IP/권한 확인   토스증권 허용 IP에 Render 서버 IP 등록 필요
HTTP 404 또는 경로 확인      토스증권 Open API 문서의 endpoint 변경 여부 확인
HTTP 5xx                    토스증권 API 또는 네트워크 일시 장애 가능성 확인
```

## 자동 실행 전 수동 스냅샷 검증

Toss 가격, 차트, 호가, 체결 출처가 모두 `toss`로 확인되면 자동 실행을 켜기 전에 수동 스냅샷을 1회 저장합니다.

화면에서는 `자동 실행 준비도` 카드의 `장마감 수동 실행` 버튼을 누르면 됩니다.

```powershell
.\test-render-deploy.ps1 -RunSchedulerMode close
```

정상 기준:

```text
scheduler manual run ok=True
snapshot history      latest=...
snapshot detail       candidates=6
performance report    runs=1 이상
```

화면에서는 오른쪽 `스냅샷 히스토리`에 새 장마감 스냅샷이 생기고, 상단 `성과` 버튼에서 관측 대상이 표시됩니다.
오른쪽 `자동 실행 준비도` 카드에서 `판정`이 `활성화 가능`으로 바뀌면 자동 실행을 켜도 되는 상태입니다.

오른쪽 `스냅샷 저장소` 카드도 함께 확인합니다.

```text
쓰기 가능    가능
최근 기록    1건 이상
보존성       임시 보존 또는 영구 설정
```

`보존성`이 `임시 보존`이면 자동 실행 테스트는 가능하지만, 재배포/재시작 뒤 기록 보존을 장담하기 어렵습니다.
운영 기록을 장기간 남기려면 Render 영구 저장소나 외부 DB를 붙인 뒤 자동 실행을 고정 운영합니다.

수동 스냅샷까지 확인한 뒤 Render Environment에서 자동 실행을 켭니다.

```text
SIGNAL_SCHEDULER_ENABLED=1
SIGNAL_PREOPEN_RUN_TIME=08:40
SIGNAL_CLOSE_RUN_TIME=16:40
SIGNAL_SCHEDULER_INTERVAL_SECONDS=30
```

자동 실행을 켠 뒤에는 장전/장마감 시간이 지난 후 `스냅샷 히스토리`에 `자동` 실행 기록이 쌓이는지 확인합니다.
화면의 `스케줄러 상태` 카드에서는 `다음 실행` 시간이 표시되고, `최근 실행`에는 `수동` 또는 `자동` 구분이 함께 표시됩니다.
