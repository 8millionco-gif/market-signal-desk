# Render 배포 체크리스트

이 문서는 Market Signal Desk를 Render에 올릴 때 사용하는 순서입니다. 첫 배포는 안전하게 스테이징 모드로 시작하고, 확인이 끝난 뒤 외부 API를 하나씩 켭니다.

## 1. 어떤 폴더를 Git에 올릴지 결정

### 앱 폴더만 올리는 경우

`outputs/market-signal-desk` 폴더를 Git 저장소 루트로 올립니다. 이 경우 앱 폴더 안의 `render.yaml`을 그대로 사용합니다.

### 현재 작업 폴더 전체를 올리는 경우

현재 상위 작업 폴더를 Git 저장소 루트로 올립니다. 이 경우 루트의 `render.yaml`이 `rootDir: outputs/market-signal-desk`를 사용해 앱 폴더만 빌드합니다.

## 2. Render에서 Blueprint 생성

1. Render Dashboard에서 New를 선택합니다.
2. Blueprint를 선택합니다.
3. GitHub 저장소 `https://github.com/8millionco-gif/market-signal-desk`를 연결합니다.
4. 서비스 이름이 `market-signal-desk`인지 확인합니다.
5. 초기 생성 중 `sync: false`로 표시된 비밀값을 입력합니다.

초기에는 `ADMIN_TOKEN`만 반드시 입력하고, 나머지 API 키는 비워도 됩니다.

화면에 입력할 값은 [RENDER_SETUP_VALUES.md](RENDER_SETUP_VALUES.md)에 따로 정리했습니다.

## 3. 1차 스테이징 환경변수

초기 배포는 외부 API 호출량을 보호하기 위해 아래 상태로 시작합니다.
수동 Web Service 생성으로 환경변수를 일부 빠뜨려도 스케줄러와 GDELT 글로벌 뉴스는 코드 기본값이 꺼짐입니다.

```text
ADMIN_TOKEN=긴_랜덤_문자열
HOST=0.0.0.0
SIGNAL_SCHEDULER_ENABLED=0
TOSS_LIVE_PRICES=0
TOSS_LIVE_CANDLES=0
TOSS_LIVE_ORDERBOOK=0
TOSS_LIVE_TRADES=0
DART_LIVE_DISCLOSURES=0
NAVER_LIVE_NEWS=0
GDELT_LIVE_NEWS=0
OPENAI_ANALYSIS_ENABLED=0
MARKET_INDEX_LIVE=1
FX_LIVE_RATES=1
```

## 4. 배포 직후 확인

배포 URL이 나오면 아래 순서로 확인합니다.

```text
https://your-service.onrender.com/api/health
https://your-service.onrender.com/api/auth/status
https://your-service.onrender.com
```

정상 기준은 다음과 같습니다.

- `/api/health`가 `ok: true`를 반환합니다.
- `/api/auth/status`가 `enabled: true`를 반환합니다.
- 첫 화면에서 관리자 토큰 입력창이 보입니다.
- 관리자 토큰 입력 후 후보 화면이 열립니다.
- API 키를 켜기 전에도 샘플 후보가 표시됩니다.

## 5. 외부 API 활성화 순서

한 번에 모두 켜지 말고 아래 순서대로 켭니다.

```text
1. ADMIN_TOKEN 확인
2. MARKET_INDEX_LIVE, FX_LIVE_RATES 확인
3. GDELT_LIVE_NEWS=1
4. NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NAVER_LIVE_NEWS=1
5. DART_API_KEY, DART_LIVE_DISCLOSURES=1
6. OPENAI_API_KEY, OPENAI_ANALYSIS_ENABLED=1
7. TOSS_CLIENT_ID, TOSS_CLIENT_SECRET, Toss live flags
```

토스증권 API는 허용 IP 정책이 있을 수 있으므로 Render의 외부 송신 IP 문제가 생기면 마지막에 별도로 확인합니다.

## 6. 스케줄러와 데이터 보존

`SIGNAL_SCHEDULER_ENABLED=1`은 마지막에 켭니다. Render 무료 플랜은 서버가 잠들 수 있어 장전/장마감 자동 실행이 안정적이지 않을 수 있습니다.

스냅샷 히스토리를 장기간 보존하려면 Persistent Disk 또는 DB를 붙여야 합니다. 디스크/DB 없이 시작하면 재배포나 인스턴스 교체 시 `data/runs`의 런타임 파일이 사라질 수 있습니다.

## 7. 운영 전환 기준

아래가 모두 확인되면 스테이징에서 운영으로 전환해도 됩니다.

- 관리자 토큰 보호가 켜져 있습니다.
- 화면 접속, 새로고침, 성과 화면이 정상입니다.
- 뉴스/공시/OpenAI/Toss 중 켠 API의 상태 카드가 정상입니다.
- 잘못된 가격/환율이 나오면 해당 소스가 샘플인지 실시간인지 구분됩니다.
- 자동 실행은 최소 하루 이상 테스트 후 켭니다.
