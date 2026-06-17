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
