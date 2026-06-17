# Market Signal Desk Workspace

이 저장소는 토스증권 Open API 문서 분석 결과와 주식 후보 분석 MVP인 Market Signal Desk를 함께 보관합니다.

## 메인 앱

앱 위치:

```text
outputs/market-signal-desk
```

로컬 실행:

```powershell
cd outputs/market-signal-desk
python server.py
```

브라우저:

```text
http://127.0.0.1:8787
```

## Render 배포

현재 루트의 `render.yaml`은 이 작업 폴더 전체를 GitHub 저장소로 올리는 경우를 기준으로 합니다. 앱 폴더만 빌드하도록 `rootDir: outputs/market-signal-desk`가 설정되어 있습니다.

앱 폴더만 별도 저장소로 올리는 경우에는 `outputs/market-signal-desk/render.yaml`을 사용하면 됩니다.

배포 절차는 다음 문서를 따릅니다.

```text
outputs/market-signal-desk/RENDER_DEPLOYMENT.md
```

Render 화면 입력값은 다음 문서에 정리되어 있습니다.

```text
outputs/market-signal-desk/RENDER_SETUP_VALUES.md
```

## 보안 메모

실제 API 키는 저장소에 넣지 않습니다.

- Toss API Key/Secret
- Naver Client ID/Secret
- OpenDART API Key
- OpenAI API Key
- ADMIN_TOKEN

Render에서는 Environment Variables에 비밀값으로 입력합니다.

## GitHub 업로드 전 확인

업로드 전 아래 파일과 폴더는 포함하지 않습니다.

```text
.env
outputs/market-signal-desk/data/runs/
outputs/market-signal-desk/data/watchlist.json
outputs/market-signal-desk/data/dart-corp-codes.json
outputs/market-signal-desk/__pycache__/
work/*test-runs/
```

`.gitignore`에 이미 반영되어 있습니다.
