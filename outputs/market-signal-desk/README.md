# Market Signal Desk

장 마감 후 후보 발굴, 장 시작 전 후보 압축, 장중 조건 확인을 위한 투자 판단 보조 MVP입니다.

## 실행

```powershell
python server.py
```

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:8787
```

이 환경에 기본 `python` 명령이 없으면 Codex 번들 Python으로 실행할 수 있습니다.

```powershell
& "C:\Users\doyeo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" server.py
```

## Render 스테이징 배포

Render에는 먼저 샘플/제한 모드로 배포해 화면, 라우팅, 성과 검증, 헬스 체크가 정상인지 확인합니다. 실제 Toss/Naver/OpenDART/OpenAI 키는 접근제어를 붙인 뒤 켜는 것을 권장합니다.

상세 순서는 [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)를 기준으로 진행합니다.
배포 후 상태 확인은 `test-render-deploy.ps1`로 실행할 수 있습니다.
네이버 뉴스 키를 Render에 넣은 뒤에도 같은 스크립트로 실제 검색 호출까지 확인합니다.

이 폴더를 Git 저장소 루트로 올리는 경우 `render.yaml`을 그대로 사용할 수 있습니다.

```text
Build Command: pip install -r requirements.txt
Start Command: python server.py
Health Check Path: /api/health
```

상위 폴더를 Git 저장소 루트로 올리는 경우 Render 서비스의 Root Directory를 다음처럼 지정합니다.

```text
outputs/market-signal-desk
```

현재 작업 폴더 전체를 Git 저장소 루트로 올릴 때를 대비해 상위 폴더에도 `rootDir: outputs/market-signal-desk`가 포함된 `render.yaml`을 준비했습니다.

현재 앱 폴더 안에서 작업 중이라면 다음 명령으로 상위 저장소 기준 GitHub 업로드 점검을 실행할 수 있습니다.

```powershell
.\prepare-github-upload.ps1
```

Render Web Service는 외부 요청을 받기 위해 `0.0.0.0`에 바인딩해야 합니다. `render.yaml`에는 다음 값이 포함되어 있습니다.

```text
HOST=0.0.0.0
```

`PORT`는 Render가 제공하는 값을 서버가 자동으로 읽습니다. 로컬에서는 기본 `8787`을 사용합니다.

초기 스테이징에서는 외부 API 호출량을 보호하기 위해 다음 값이 꺼져 있습니다.
수동 Web Service 생성으로 일부 값을 넣지 않아도 스케줄러와 GDELT 글로벌 뉴스는 코드 기본값이 꺼짐입니다.

```text
SIGNAL_SCHEDULER_ENABLED=0
TOSS_LIVE_PRICES=0
TOSS_LIVE_CANDLES=0
TOSS_LIVE_ORDERBOOK=0
TOSS_LIVE_TRADES=0
TOSS_LIVE_PORTFOLIO=0
DART_LIVE_DISCLOSURES=0
NAVER_LIVE_NEWS=0
OPENAI_ANALYSIS_ENABLED=0
```

실제 API 키는 Render Dashboard의 Environment에서 입력합니다. 키를 `render.yaml`에 직접 쓰지 마세요.

Render에서 스냅샷 히스토리와 성과 검증 데이터를 오래 보존하려면 Persistent Disk 또는 DB 연결이 필요합니다. 디스크/DB를 붙이기 전까지는 배포 재시작, 재배포, 인스턴스 교체 시 런타임 파일이 사라질 수 있습니다.

## 관리자 접근제어

공개 URL에서 API 호출량과 연결 키 사용을 보호하려면 `ADMIN_TOKEN`을 설정합니다. 값이 비어 있으면 로컬 개발처럼 보호가 꺼지고, 값이 있으면 `/api/health`와 `/api/auth/status`를 제외한 API가 보호됩니다.

```powershell
$env:ADMIN_TOKEN="long-random-admin-token"
```

Render에서는 Dashboard의 Environment에 `ADMIN_TOKEN`을 비밀값으로 입력합니다. 화면이 열리면 `관리자 토큰` 카드 또는 중앙 입력창에 같은 값을 한 번 입력하면 됩니다. 브라우저는 이후 API 요청에 다음 헤더를 붙입니다.

```text
X-Admin-Token: your-admin-token
```

직접 API를 호출할 때는 `Authorization: Bearer your-admin-token`도 사용할 수 있습니다.

## 토스증권 API 설정

실제 키는 코드나 저장소에 넣지 말고 실행 터미널의 환경변수로만 설정합니다.

가장 안전한 실행 방식은 프롬프트로 키를 입력하는 것입니다.

```powershell
.\run-with-toss.ps1
```

이 스크립트는 API Key와 Secret Key를 파일에 저장하지 않고, 실행 중인 PowerShell 세션에서만 환경변수로 설정합니다. 서버를 종료하면 기존 환경변수 값을 복원합니다.

스크립트는 OpenDART API Key, 네이버 뉴스 Client ID/Secret, OpenAI API Key도 선택적으로 입력받습니다. 입력하지 않으면 공시와 뉴스는 샘플 데이터를 사용하고, AI 분석은 로컬 규칙으로 대체합니다.

다른 포트로 실행하려면 다음처럼 실행합니다.

```powershell
.\run-with-toss.ps1 -Port 8791
```

직접 환경변수로 설정하려면 다음처럼 실행합니다.

```powershell
$env:TOSS_CLIENT_ID="your_toss_client_id"
$env:TOSS_CLIENT_SECRET="your_toss_client_secret"
$env:TOSS_ACCOUNT_SEQ="1"
$env:PORT="8787"
& "C:\Users\doyeo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" server.py
```

이미 발급된 access token을 임시로 쓰고 싶으면 다음 값을 추가할 수 있습니다.

```powershell
$env:TOSS_ACCESS_TOKEN="your_access_token"
```

토스증권 Open API는 `client_id`와 `client_secret`으로 OAuth 토큰을 발급한 뒤 API를 호출합니다. 라이브 키가 노출되면 재발급 후 기존 키를 폐기하세요.

토스증권 Open API 화면에서 허용 IP를 관리하는 경우, 서버를 실행하는 PC/서버의 외부 IP가 허용 IP에 등록되어 있어야 합니다. IP가 다르면 키와 시크릿이 맞아도 토큰 발급 또는 API 호출이 실패할 수 있습니다.
Render 배포 환경에서는 오른쪽 `Render 외부 IP` 카드 또는 `GET /api/network/outbound-ip`로 현재 외부 IP를 확인할 수 있습니다. Render 대시보드의 서비스 상세 `Connect > Outbound` 탭에서도 outbound IP 범위를 확인합니다.

환경변수가 설정되어 있으면 대시보드는 후보 종목의 현재가를 `GET /api/v1/prices`로 조회해 샘플 가격을 덮어씁니다. 또한 `GET /api/v1/candles` 일봉 데이터를 이용해 미니 차트와 전일 대비 등락률을 보강합니다.
검색창은 오늘 후보와 `data/candidate-universe.json` 감시 유니버스를 함께 자동완성합니다. `삼성`, `하닉`, `엔비`, `ㅅㅈ`, `AAPL`, `005930`처럼 종목명 일부, 별칭, 초성, 코드, 티커로 찾을 수 있고, 방향키와 Enter로 바로 선택할 수 있습니다. `005930`, `AAPL`처럼 후보 밖 종목코드나 티커를 입력하면 `GET /api/v1/stocks`로 종목 기본정보를 직접 조회합니다. 토스 Open API는 키워드 기반 전체 종목 검색이 아니라 `symbols` 기반 조회를 제공하므로, 시장 전체 종목명 자동완성은 별도 종목 마스터 데이터가 필요합니다.

호가와 최근 체결은 주문 API가 아니라 시장 데이터 API입니다. 화면은 `GET /api/v1/orderbook`과 `GET /api/v1/trades`를 이용해 호가 잔량, 스프레드, 최근 체결 방향을 수급 참고 지표로만 사용합니다. 주문 생성이나 매매 실행과는 연결하지 않습니다.
보유 자산 판단은 `TOSS_LIVE_PORTFOLIO=1`을 켠 뒤 계좌 목록, 보유 주식, 매수 가능 금액을 읽기 전용으로 조회합니다. 여러 계좌가 있으면 `TOSS_ACCOUNT_SEQ`를 지정하고, 지정하지 않으면 첫 계좌를 조회합니다. 이 기능도 주문 생성이나 자동 매매와 연결하지 않습니다.
Render에서는 토스 키와 live 플래그를 넣은 뒤 `test-render-deploy.ps1`로 토큰 발급 가능 상태, 대시보드 반영, 가격/차트/호가/체결/포트폴리오 API를 함께 확인합니다. 토스증권 허용 IP가 켜져 있으면 Render 서버 외부 IP가 등록되어 있어야 합니다.

API 호출량을 줄이기 위해 현재가는 기본 15초, 캔들은 기본 60초, 호가/체결은 기본 5초, 포트폴리오는 기본 30초, 종목 기본정보는 기본 1일 동안 캐시합니다.

```powershell
$env:TOSS_PRICE_CACHE_SECONDS="15"
$env:TOSS_CANDLE_CACHE_SECONDS="60"
$env:TOSS_ORDERBOOK_CACHE_SECONDS="5"
$env:TOSS_TRADES_CACHE_SECONDS="5"
$env:TOSS_PORTFOLIO_CACHE_SECONDS="30"
$env:TOSS_STOCK_CACHE_SECONDS="86400"
$env:TOSS_REQUEST_TIMEOUT_SECONDS="5"
$env:TOSS_CANDLE_MAX_CANDIDATES="2"
$env:TOSS_ORDERBOOK_MAX_CANDIDATES="2"
$env:TOSS_TRADES_MAX_CANDIDATES="2"
$env:TOSS_TRADES_COUNT="30"
$env:TOSS_CANDLE_MAX_STALENESS_DAYS="7"
```

화면의 가격 기준은 토스 현재가입니다. 초기 샘플 가격과 토스 현재가의 차이를 별도로 검수하고 싶을 때만 다음 옵션을 추가합니다.

```powershell
$env:TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT="50"
```

이 옵션을 켜면 샘플 가격과 토스 현재가의 차이가 위 비율보다 큰 종목에 `기준가 차이` 경고를 표시합니다.

라이브 현재가 반영을 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:TOSS_LIVE_PRICES="0"
$env:TOSS_LIVE_CANDLES="0"
$env:TOSS_LIVE_ORDERBOOK="0"
$env:TOSS_LIVE_TRADES="0"
$env:TOSS_LIVE_PORTFOLIO="0"
```

## OpenDART 공시 설정

OpenDART API Key가 있으면 국내 후보 종목의 공식 공시를 조회합니다. 키는 코드에 저장하지 않고 환경변수로만 설정합니다.

```powershell
$env:DART_API_KEY="your_opendart_api_key"
$env:DART_DISCLOSURE_LOOKBACK_DAYS="7"
$env:DART_DISCLOSURE_CACHE_SECONDS="300"
$env:DART_REQUEST_TIMEOUT_SECONDS="6"
$env:DART_DISCLOSURE_MAX_CANDIDATES="2"
```

OpenDART는 종목코드와 DART 고유번호가 다르기 때문에, 서버가 `corpCode.xml`을 받아 `data/dart-corp-codes.json`으로 캐시합니다. 이후 `list.json`으로 최근 공시를 조회합니다.
Render에서는 `DART_API_KEY`와 `DART_LIVE_DISCLOSURES=1`을 넣은 뒤 `test-render-deploy.ps1`로 고유번호와 공시 조회를 함께 확인합니다.

공시 조회를 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:DART_LIVE_DISCLOSURES="0"
```

## 시장 지표 설정

상단 시장 지표는 지수와 환율을 각각 외부 API로 갱신합니다. 실패하면 샘플 값으로 대체하고 화면과 오른쪽 `시장 지표 상태`에 샘플 여부를 표시합니다.

```powershell
$env:MARKET_INDEX_LIVE="1"
$env:MARKET_INDEX_PROVIDER="naver"
$env:MARKET_INDEX_NAVER_DOMESTIC_URL_TEMPLATE="https://polling.finance.naver.com/api/realtime/domestic/index/{symbol}"
$env:MARKET_INDEX_NAVER_WORLD_URL_TEMPLATE="https://polling.finance.naver.com/api/realtime/worldstock/index/{symbol}"
$env:MARKET_INDEX_KOSPI_SYMBOL="KOSPI"
$env:MARKET_INDEX_KOSDAQ_SYMBOL="KOSDAQ"
$env:MARKET_INDEX_NASDAQ_SYMBOL=".IXIC"
$env:MARKET_INDEX_CACHE_SECONDS="60"
$env:MARKET_INDEX_REQUEST_TIMEOUT_SECONDS="5"

$env:FX_LIVE_RATES="1"
$env:FX_RATE_URL="https://open.er-api.com/v6/latest/USD"
$env:FX_RATE_FALLBACK_URL="https://api.frankfurter.app/latest?from=USD&to=KRW"
$env:FX_RATE_CACHE_SECONDS="1800"
$env:FX_REQUEST_TIMEOUT_SECONDS="5"
```

지수나 환율 갱신을 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:MARKET_INDEX_LIVE="0"
$env:FX_LIVE_RATES="0"
```

## 네이버 뉴스 설정

네이버 뉴스 검색 API가 있으면 후보 종목명으로 최신 뉴스를 조회해 상세 화면의 근거 리스트에 반영합니다. 참조 기본 경로는 `https://openapi.naver.com/v1/search/news`이고, 서버는 JSON 응답을 받기 위해 실제 호출 시 `https://openapi.naver.com/v1/search/news.json`으로 보정합니다. `query`, `display`, `start`, `sort` 파라미터를 보내고, 요청 헤더에 Client ID와 Client Secret을 포함합니다. 검색 API의 하루 호출 한도는 25,000회입니다.

발급 직후에는 앱 서버를 켜기 전에 네이버 뉴스 API만 단독으로 테스트할 수 있습니다.

```powershell
.\test-naver-news.ps1 -Query "삼성전자" -Display 5
```

성공하면 검색 총 건수와 최신 뉴스 제목이 출력됩니다. 403 오류가 나면 네이버 개발자 센터에서 해당 애플리케이션의 API 설정에 `검색`이 포함되어 있는지 확인하세요.

```powershell
$env:NAVER_CLIENT_ID="your_naver_client_id"
$env:NAVER_CLIENT_SECRET="your_naver_client_secret"
$env:NAVER_NEWS_BASE_URL="https://openapi.naver.com/v1/search/news"
$env:NAVER_NEWS_DISPLAY="5"
$env:NAVER_NEWS_CACHE_SECONDS="300"
$env:NAVER_NEWS_MAX_CANDIDATES="3"
$env:NAVER_REQUEST_TIMEOUT_SECONDS="5"
```

뉴스 조회를 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:NAVER_LIVE_NEWS="0"
```

## 글로벌 뉴스 설정

GDELT DOC 2.0 API는 별도 키 없이 글로벌 뉴스 기사 목록을 조회할 수 있어 해외 종목과 글로벌 테마 보강에 사용합니다. 기본 호출은 `mode=artlist`, `format=json`, `sort=datedesc`이며, 후보별 영문 종목명과 티커를 검색어로 사용합니다.

```powershell
$env:GDELT_LIVE_NEWS="1"
$env:GDELT_DOC_BASE_URL="https://api.gdeltproject.org/api/v2/doc/doc"
$env:GDELT_NEWS_DISPLAY="5"
$env:GDELT_NEWS_TIMESPAN="1week"
$env:GDELT_NEWS_CACHE_SECONDS="300"
$env:GDELT_NEWS_MAX_CANDIDATES="1"
$env:GDELT_REQUEST_TIMEOUT_SECONDS="20"
$env:GDELT_REQUEST_SPACING_SECONDS="5.2"
```

GDELT는 짧은 시간에 연속 요청하면 제한에 걸릴 수 있어 기본 조회 후보 수를 1개로 둡니다. 더 많은 후보를 조회하려면 `GDELT_NEWS_MAX_CANDIDATES`를 늘리되 응답 시간이 길어질 수 있습니다.
화면에서 `글로벌 출처`가 `제한`으로 표시되면 GDELT 요청 제한에 걸린 상태이므로 몇 분 뒤 새로고침해 확인합니다.

연결 테스트는 기존 뉴스 검색 API에 `provider=gdelt`를 붙이면 됩니다.

```powershell
Invoke-RestMethod "http://127.0.0.1:8787/api/integrations/news/search?provider=gdelt&query=NVIDIA&display=3"
```

글로벌 뉴스 보강을 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:GDELT_LIVE_NEWS="0"
```

## OpenAI 분석 설정

OpenAI API Key가 있으면 뉴스, 공시, 시세 반응을 묶어 후보별 이벤트 성격, 영향도, 리스크, 진입 조건, 금지 조건을 구조화합니다. 결과는 매수·매도 추천이 아니라 관찰 조건 정리입니다.

```powershell
$env:OPENAI_API_KEY="your_openai_api_key"
$env:OPENAI_ANALYSIS_ENABLED="1"
$env:OPENAI_MODEL="gpt-5.4"
$env:OPENAI_ANALYSIS_CACHE_SECONDS="900"
$env:OPENAI_ANALYSIS_MAX_CANDIDATES="1"
$env:OPENAI_REQUEST_TIMEOUT_SECONDS="20"
```

키가 없거나 호출이 실패하면 서버가 로컬 규칙 분석으로 자동 대체합니다. OpenAI 분석을 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:OPENAI_ANALYSIS_ENABLED="0"
```

구현 기준은 OpenAI Responses API와 Structured Outputs입니다. 기본 모델은 응답 안정성을 우선해 `gpt-5.4`로 두고, 모델은 환경변수로 바꿀 수 있습니다.
Render에서는 OpenAI 키를 넣은 뒤 `test-render-deploy.ps1`로 상태, 대시보드 반영, 단일 종목 분석 API 출처가 `openai`인지 확인합니다.

첫 화면이 외부 API 때문에 오래 멈추지 않도록, 기본값은 후보 일부만 라이브 조회하고 나머지는 샘플/로컬 분석으로 대체합니다. 더 많은 후보를 실시간 분석하려면 `*_MAX_CANDIDATES` 값을 단계적으로 늘리면 됩니다.

## 후보 자동 생성 설정

대시보드는 `data/candidate-universe.json`의 감시 유니버스를 기준으로 오늘 후보를 자동 구성합니다. 네이버 뉴스가 준비되어 있으면 유니버스 종목별 최신 뉴스를 먼저 스캔하고, 뉴스 건수·관심 가중치·관심 등록 여부를 반영해 상위 후보를 고릅니다. 뉴스 제목이나 요약에 종목명, 티커, 별칭이 맞지 않는 검색 결과는 제외하고 후보 점수에 반영하지 않습니다. 네이버 뉴스가 꺼져 있으면 유니버스 기본 점수와 기존 샘플 후보 정보를 이용해 후보를 구성합니다.

기본 후보 목표는 국내 10개와 해외 10개입니다. 관련 뉴스가 확인된 1차 후보를 우선 선별하고, 부족한 경우 유니버스 관심도와 가격 반응을 확인할 보조 후보로 채웁니다. 화면의 `진입` 탭은 전체 후보 중에서도 현재가, 준비도, 리스크, 과열도를 다시 통과한 후보만 보여 주므로 목록이 적거나 비어 있을 수 있습니다.

```powershell
$env:SIGNAL_AUTO_CANDIDATES_ENABLED="1"
$env:SIGNAL_AUTO_CANDIDATE_LIMIT="20"
$env:SIGNAL_DOMESTIC_CANDIDATE_LIMIT="10"
$env:SIGNAL_OVERSEAS_CANDIDATE_LIMIT="10"
$env:SIGNAL_DISCOVERY_MAX_SYMBOLS="40"
$env:SIGNAL_DISCOVERY_NEWS_DISPLAY="3"
$env:SIGNAL_DISCOVERY_CACHE_SECONDS="600"
```

임시로 유니버스에 종목을 더 넣고 싶으면 쉼표로 구분해 추가합니다.

```powershell
$env:SIGNAL_DISCOVERY_SYMBOLS="TSLA,AMD,064350"
```

화면의 `오늘의 후보` 아래에는 `자동 뉴스 선정`, `자동 유니버스 선정`, `샘플 후보` 중 어떤 기준으로 후보가 만들어졌는지 표시됩니다. 후보 자동 생성은 주문이나 자동매매와 연결되지 않고, 이후 기존 시세·뉴스·공시·AI 분석 단계로 넘겨지는 시작 목록만 바꿉니다.

## DB 저장소 설정

기본값은 파일 저장소입니다. `DATABASE_URL`이 설정되면 Postgres DB를 우선 사용하고, 연결 실패 시 기존 JSON 파일 저장소로 안전하게 대체합니다.

DB에 저장되는 핵심 데이터는 다음과 같습니다.

- 후보 풀: `candidate_pool`
- 상시 발굴 봇 최신 결과: `discovery_latest`
- 장전/장마감/장중 스냅샷: `signal_snapshots`
- 시세·공시·뉴스 원천 이벤트: `signal_raw_events`

Render Postgres 또는 Supabase Postgres를 연결한 뒤 아래 값을 설정합니다.

```powershell
$env:SIGNAL_STORAGE_BACKEND="auto"
$env:DATABASE_URL="postgresql://..."
$env:SIGNAL_DB_AUTO_MIGRATE="1"
$env:SIGNAL_DB_MIGRATE_RUN_LIMIT="200"
$env:SIGNAL_RAW_EVENT_STORAGE_ENABLED="1"
$env:SIGNAL_RAW_EVENT_PAYLOAD_LIMIT="40"
$env:SIGNAL_RAW_EVENT_FILE_LIMIT="500"
```

앱은 시작 후 첫 저장/조회 시 `signal_kv`, `signal_snapshots`, `signal_raw_events` 테이블을 자동 생성합니다. `SIGNAL_DB_AUTO_MIGRATE=1`이면 기존 `data/candidate-pool.json`, `data/discovery-latest.json`, `data/runs/*.json` 기록을 DB에 한 번 자동 이관합니다. 운영에서는 이 값을 연결해야 후보 풀과 성과 검증 기록이 재배포 후에도 유지됩니다.

`signal_raw_events`에는 Toss 시세/캔들/호가/체결, OpenDART 공시, 네이버/GDELT 뉴스 응답이 저장됩니다. 원천 payload는 `SIGNAL_RAW_EVENT_PAYLOAD_LIMIT` 범위로 잘라 저장하므로, 판단 근거 추적은 가능하게 두면서 DB가 불필요하게 커지는 것을 막습니다.

DB 연결이 없을 때 원천 이벤트는 `data/raw-events.json`에 제한 개수만 보관됩니다. Render 무료 웹 서비스의 파일 저장소는 재배포/재시작 후 유지가 보장되지 않으므로 운영에서는 DB 저장을 기준으로 봅니다.

후보 판단에는 `원천 신뢰도`가 별도로 반영됩니다. 현재가, 차트, 호가/체결, 뉴스 관련성, 공식 공시, 원천 저장 가능 여부를 각각 점수화하고, 점수가 낮으면 `매수 가능` 후보가 `근거 보강 대기` 또는 `오늘 제외`로 내려갑니다. 화면의 후보 배지와 상세 판단 영역에서 `원천` 점수와 보강 사유를 확인할 수 있습니다.

가격 반응은 별도 게이트로 검증합니다. 뉴스·공시 재료가 있어도 현재가, 거래량, 호가, 체결이 따라오지 않으면 `반응대기` 또는 `반응차단`으로 내려가며, 핵심 후보와 매수 가능 판단에서 제외됩니다.

DB 연결 후 설정 화면의 `스냅샷 저장소` 카드에서 `DB 이관 실행`을 눌러 파일 저장소 기록을 다시 확인할 수 있습니다. 기존 DB 데이터는 덮어쓰지 않고, 아직 DB에 없는 스냅샷만 추가합니다.

```powershell
.\test-render-deploy.ps1 -RunDatabaseMigration
```

후보 풀은 단순 저장 기록이 아니라 상시 감시 대상입니다. 봇이 발견한 종목은 풀에 누적되고, 상태가 `진입 후보`, `검증중`, `눌림 대기`, `관찰중`으로 관리됩니다. 각 종목에는 근거 점수, 가격 반응, 신뢰도, 후보 풀 성과를 묶은 `재검토 우선도`가 붙고, 이 점수가 높은 종목은 다음 스캔 때 다시 분석됩니다. 최종 후보 압축과 정렬에는 후보 풀 누적 점수, 관측 횟수, 최근 개선/약화 흐름, 사후 성과가 제한 가중치로 반영됩니다. 리스크, 데이터 신뢰도, 가격 반응 기준은 후보 풀 가중치보다 우선합니다.

성과 검증이 실행되면 저장된 스냅샷 후보의 기준가와 현재가를 비교하고, 연결된 후보 풀 종목에는 관측 횟수, 승률, 평균 변화율, 최근 성과가 누적됩니다. 이 값은 같은 종목을 다시 볼지, 더 낮출지 판단하는 보조 신호이며 단독 매수 신호로 쓰지 않습니다.

웹 화면의 기본 `/api/dashboard` 조회는 DB의 최신 발굴 결과 또는 스냅샷을 먼저 사용합니다. 외부 API 지연으로 화면이 비는 것을 줄이기 위한 읽기 전용 경로이며, 새 후보 분석을 강제로 실행하려면 `/api/dashboard?mode=close&refresh=1` 또는 화면의 새로고침 버튼을 사용합니다.

종목 검색 자동완성은 후보/감시 유니버스뿐 아니라 OpenDART 기업코드 캐시와 주요 ETF 보조 마스터를 함께 사용합니다. 따라서 국내 일반 종목명, 종목코드, 한글 별칭, `TIGER200` 같은 붙여쓴 ETF 별칭을 검색할 수 있습니다.

```powershell
$env:SIGNAL_CANDIDATE_POOL_ENABLED="1"
$env:SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT="8"
$env:SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE="58"
$env:SIGNAL_CANDIDATE_POOL_TOP_LIMIT="5"
```

## 상시 발굴 봇 설정

상시 발굴 봇은 장마감/장전 스냅샷과 별도로 최신 후보를 주기적으로 갱신하고 마지막 발굴 결과를 저장합니다. DB가 연결되어 있으면 `signal_kv`에, 없으면 `data/discovery-latest.json`에 저장합니다. 이 봇은 투자 판단 보조용이며 주문이나 자동매매와 연결되지 않습니다.

```powershell
$env:SIGNAL_DISCOVERY_BOT_ENABLED="1"
$env:SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS="600"
$env:SIGNAL_DISCOVERY_BOT_MODE="intraday"
```

상태 확인과 수동 실행 API는 다음과 같습니다.

```text
GET  /api/discovery/status
GET  /api/discovery/latest
POST /api/discovery/run
```

## 스케줄러 설정

서버가 켜져 있으면 장전과 장마감에 후보 분석을 자동 실행하고 스냅샷을 저장합니다. DB가 연결되어 있으면 `signal_snapshots`에, 없으면 `data/runs` 폴더에 JSON 파일로 저장합니다. 이 기능은 분석 저장용이며 주문이나 매매 실행과 연결되지 않습니다.

```powershell
$env:SIGNAL_SCHEDULER_ENABLED="1"
$env:SIGNAL_SCHEDULER_INTERVAL_SECONDS="30"
$env:SIGNAL_PREOPEN_RUN_TIME="08:40"
$env:SIGNAL_PREOPEN_RUN_WINDOW_MINUTES="80"
$env:SIGNAL_CLOSE_RUN_TIME="16:40"
$env:SIGNAL_CLOSE_RUN_WINDOW_MINUTES="360"
$env:SIGNAL_RUN_HISTORY_LIMIT="12"
```

자동 실행을 잠시 끄려면 다음 값을 설정합니다.

```powershell
$env:SIGNAL_SCHEDULER_ENABLED="0"
```

화면의 `스케줄러 상태` 카드에서 장마감/장전 분석을 수동으로 실행할 수도 있습니다.
Render 배포에서는 자동 실행을 켜기 전에 아래처럼 수동 스냅샷 저장, 히스토리 조회, 성과 리포트 연결을 먼저 확인합니다.
화면에서는 `자동 실행 준비도` 카드의 `장마감 수동 실행` 버튼으로 같은 검증을 시작할 수 있습니다.

```powershell
.\test-render-deploy.ps1 -RunSchedulerMode close
```

화면의 `자동 실행 준비도` 카드에서 `판정`이 `활성화 가능`이면 `SIGNAL_SCHEDULER_ENABLED=1`로 전환합니다.
자동 실행을 켠 뒤에는 `스케줄러 상태` 카드의 `다음 실행`과 `최근 실행`을 같이 봅니다. `최근 실행`에는 수동/자동 구분이 표시되며, 예약 시간이 지나면 `스냅샷 히스토리`에 `자동` 기록이 쌓여야 합니다.

## 성과 검증 설정

상단 `성과` 버튼은 저장된 스냅샷의 상위 후보와 현재 가격을 비교합니다. 실제 매수·매도 체결 손익이 아니라, 후보 선정 이후 가격 방향이 얼마나 맞았는지 보는 검증 화면입니다. 측정된 결과는 후보 풀에도 반영되어 각 종목의 사후 승률과 평균 변화가 다음 후보 선별에 제한적으로 사용됩니다.

```powershell
$env:SIGNAL_PERFORMANCE_RUN_LIMIT="12"
$env:SIGNAL_PERFORMANCE_TOP_CANDIDATES="3"
$env:SIGNAL_PERFORMANCE_AUTO_UPDATE="1"
$env:SIGNAL_PERFORMANCE_MIN_AGE_MINUTES="60"
$env:SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT="1"
```

기본값은 최근 12개 스냅샷의 상위 3개 후보를 비교하고, 저장 후 60분 이상 지난 스냅샷만 성과 관측 대상으로 삼습니다. 현재가가 스냅샷 당시 가격보다 1% 이상 높으면 상승 관측으로 분류합니다. 스냅샷이 저장되면 오래된 스냅샷의 성과 검증을 자동 실행해 후보 풀 성과를 갱신합니다.

## 알림 설정

화면의 `브라우저 알림` 카드에서 알림 권한을 켤 수 있습니다. 알림은 후보 점수와 진입 준비도만 보지 않고, 화면의 가격 행동 기준을 함께 사용합니다. `관찰 매수 구간`, `눌림 대기`, `반등 확인`, `위험 기준`, `분할매도 점검` 중 실제 감시할 조건이 생겼을 때 표시됩니다. 새 스냅샷이 저장됐을 때도 별도 알림을 보낼 수 있습니다. 주문이나 매매 실행과는 연결되지 않습니다.

브라우저 알림은 페이지가 열려 있고 브라우저 권한이 허용된 상태에서만 동작합니다. 권한을 차단했다면 브라우저 사이트 설정에서 다시 허용해야 합니다.

## 현재 구현

- 장마감/장전/장중 모드별 후보 정렬
- 뉴스, 시세, 지수, 공시 신호 기반 후보 점수 재계산
- 장전/장마감 자동 실행 및 분석 스냅샷 저장
- 다음 자동 실행 예정 시간 표시
- 저장된 스냅샷 히스토리 조회
- 스냅샷 저장소 쓰기/보존 상태 점검
- 저장된 스냅샷 후보의 성과 검증 화면
- 가격 행동 기준 기반 브라우저 알림 연결
- 관리자 토큰 기반 API 접근 보호
- 종목 후보 피드
- 진입, 눌림, 숨은 기회, 모멘텀, 보유 대응, 제외 후보 탭 분류
- 진입 조건, 진입 금지 조건, 손절 기준
- 후보별 선정 기준 메모
- 뉴스/공시 메모, 트렌드 지표, 연관 종목
- 관심 종목 저장
- 백엔드 API
- 토스증권 현재가 반영 및 연결 상태 표시
- 토스증권 호가/최근 체결 기반 수급 지표 반영
- 토스증권 보유 자산 읽기 전용 조회 및 포트폴리오 상태 표시
- USD/KRW 환율 갱신 및 출처 표시
- OpenDART 공시 조회 및 연결 상태 표시
- 네이버 뉴스 검색 및 연결 상태 표시
- GDELT 글로벌 뉴스 보강 및 해외 뉴스 상태 표시
- OpenAI 후보 분석 및 로컬 분석 대체

## API

```text
GET  /api/health
GET  /api/auth/status
GET  /api/dashboard?mode=close|preopen|intraday
GET  /api/signals/{symbol}
GET  /api/integrations/toss/status
GET  /api/integrations/market/status
GET  /api/integrations/toss/prices?symbols=005930,AAPL
GET  /api/integrations/toss/candles?symbol=005930&interval=1d&count=20
GET  /api/integrations/toss/orderbook?symbol=005930
GET  /api/integrations/toss/trades?symbol=005930&count=30
GET  /api/portfolio/status
GET  /api/integrations/dart/status
GET  /api/integrations/dart/corp-code?symbol=005930
GET  /api/integrations/dart/disclosures?symbol=005930&days=7
GET  /api/integrations/news/status
GET  /api/integrations/news/search?query=삼성전자&display=5&sort=date
GET  /api/integrations/news/search?provider=gdelt&query=NVIDIA&display=3&timespan=1week
GET  /api/integrations/openai/status
GET  /api/integrations/openai/analyze?symbol=005930
GET  /api/scheduler/status
GET  /api/storage/status
GET  /api/scheduler/runs?limit=12
GET  /api/scheduler/runs/{id}
GET  /api/performance?limit=12&top=3
POST /api/scheduler/run
POST /api/storage/migrate
POST /api/watchlist
```

## 다음 개발

1. 후보 선정 기준 튜닝 화면 추가
2. 외부 알림 채널 확장
3. 관심 종목별 상세 히스토리 추가
4. Render 스테이징 배포와 운영 환경 점검
