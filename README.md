# Maple Live Scout

Nexon Open API 기반 메이플스토리 캐릭터 조회 및 환산 계산기입니다.

## 로컬 실행

프로젝트 루트에 `.env` 파일을 만들고 Nexon Open API 키를 넣습니다.

```env
NEXON_API_KEY=your_key
```

서버 실행:

```powershell
python app\server.py
```

브라우저:

```text
http://127.0.0.1:4176/
```

## Render 배포

1. 이 폴더를 GitHub 저장소에 올립니다.
2. Render에서 `New > Blueprint`를 선택하고 저장소를 연결합니다.
3. `NEXON_API_KEY` 값을 물어보면 Nexon Open API 키를 입력합니다.
4. 배포가 끝나면 `https://서비스이름.onrender.com` 주소로 접속할 수 있습니다.

배포 설정은 `render.yaml`에 들어 있습니다.

중요: `.env` 파일은 `.gitignore`에 포함되어 있으므로 GitHub에 올리면 안 됩니다. 서버에는 Render 환경변수로만 API 키를 넣습니다.

## 배포 명령 직접 입력 방식

Blueprint를 쓰지 않고 Render Web Service를 직접 만들 경우:

```text
Language: Python 3
Build Command: pip install -r requirements.txt
Start Command: python app/server.py
Environment Variables:
  HOST=0.0.0.0
  PORT=10000
  NEXON_API_KEY=your_key
Health Check Path: /api/health
```
