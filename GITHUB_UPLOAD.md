# GitHub 업로드 준비

## 권장 방식

현재 작업 폴더 전체를 GitHub 저장소로 올리는 방식을 권장합니다.

이유:

- 루트 `render.yaml`이 이미 `rootDir: outputs/market-signal-desk`로 설정되어 있습니다.
- Toss API 분석 문서와 앱 코드를 함께 보관할 수 있습니다.
- Render Blueprint 연결 시 별도 Root Directory 설정 실수가 줄어듭니다.

## 업로드 전 점검

1. 실제 API 키가 파일에 들어가지 않았는지 확인합니다.
2. `.env` 파일이 있다면 업로드하지 않습니다.
3. `data/runs`, `watchlist.json`, `dart-corp-codes.json`은 런타임 파일이므로 업로드하지 않습니다.
4. GitHub 저장소는 처음에는 private로 만드는 것을 권장합니다.

## 로컬에서 Git 저장소로 만들기

준비 검사는 스크립트로 실행할 수 있습니다.

```powershell
.\prepare-github-upload.ps1
```

현재 위치가 `outputs/market-signal-desk`라면 앱 폴더 안의 같은 이름 스크립트가 상위 저장소 기준으로 실행합니다.

문제가 없으면 커밋까지 실행합니다.

```powershell
.\prepare-github-upload.ps1 -Commit
```

원격 저장소까지 연결하려면 GitHub에서 저장소를 만든 뒤 URL을 넣습니다.

```powershell
.\prepare-github-upload.ps1 -Commit -RemoteUrl "https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git"
```

푸시까지 한 번에 실행하려면 다음처럼 실행합니다.

```powershell
.\prepare-github-upload.ps1 -Commit -RemoteUrl "https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git" -Push
```

첫 업로드에는 아직 커밋이 없으므로 `-Push`만 붙이지 말고 반드시 `-Commit`도 함께 붙입니다.

직접 실행하려면 아래 명령을 사용합니다.

```powershell
git init
git add .
git status
git commit -m "Initial Market Signal Desk MVP"
```

`git status`에서 실제 키, 실행 로그, 런타임 스냅샷이 올라가지 않는지 한 번 더 확인합니다.

## GitHub 원격 저장소 연결

GitHub에서 새 저장소를 만든 뒤 아래처럼 연결합니다.

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

## Render 연결

1. Render Dashboard에서 New를 선택합니다.
2. Blueprint를 선택합니다.
3. GitHub 저장소를 연결합니다.
4. 루트 `render.yaml`을 사용합니다.
5. 첫 배포에서는 `ADMIN_TOKEN`만 입력하고 나머지 외부 API는 꺼둡니다.

배포 후 상세 확인은 다음 문서를 따릅니다.

```text
outputs/market-signal-desk/RENDER_DEPLOYMENT.md
```
