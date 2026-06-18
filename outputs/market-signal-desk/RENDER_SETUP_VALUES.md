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
1. GDELT_LIVE_NEWS=1
2. NAVER_CLIENT_ID / NAVER_CLIENT_SECRET / NAVER_LIVE_NEWS=1
3. DART_API_KEY / DART_LIVE_DISCLOSURES=1
4. OPENAI_API_KEY / OPENAI_ANALYSIS_ENABLED=1
5. Toss 키와 Toss live flags
6. SIGNAL_SCHEDULER_ENABLED=1
```

GDELT는 요청 제한이 있으므로 처음에는 아래 기본값을 유지합니다.

```text
GDELT_NEWS_MAX_CANDIDATES=1
GDELT_REQUEST_TIMEOUT_SECONDS=20
GDELT_REQUEST_SPACING_SECONDS=5.2
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
