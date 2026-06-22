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

브라우저 접속:

```text
http://127.0.0.1:4176/
```

## 검증

Python/JavaScript 문법 검사:

```powershell
python -m py_compile app\calc.py app\server.py app\nexon.py scripts\verify_calculation.py scripts\verify_calibration_tables.py scripts\verify_goal_readiness.py scripts\verify_official_job_catalog.py scripts\verify_nexon_endpoint_contract.py scripts\verify_fetch_character_contract.py
node --check app\static\app.js
```

계산 검증:

```powershell
python scripts\verify_calculation.py
python scripts\verify_calibration_tables.py
python scripts\verify_goal_readiness.py
python scripts\verify_official_job_catalog.py
python scripts\verify_nexon_endpoint_contract.py
python scripts\verify_fetch_character_contract.py
```

`verify_official_job_catalog.py`는 Nexon 공식 직업소개 페이지와 로컬 직업별 계산식 목록을 비교합니다.
`verify_nexon_endpoint_contract.py`는 실제 조회하는 Nexon API 섹션과 계산 입력 계약이 일치하는지 확인합니다.
`verify_fetch_character_contract.py`는 필수 API 실패는 중단하고 선택 API 실패는 진단 상태로 계산을 유지하는지 확인합니다.

## Render 배포

이 저장소에는 Render Blueprint 설정인 `render.yaml`이 포함되어 있습니다.

1. GitHub 저장소를 Render에 연결합니다.
2. Render Dashboard에서 `New > Blueprint`를 선택합니다.
3. 이 저장소를 선택하면 Render가 `render.yaml`을 읽어 Python Web Service를 생성합니다.
4. 환경변수 입력 단계에서 `NEXON_API_KEY`에 Nexon Open API 키를 넣습니다.
5. 배포가 끝나면 `https://서비스이름.onrender.com` 주소로 접속합니다.

중요:

- `.env` 파일은 `.gitignore`에 포함되어 있으므로 GitHub에 올라가지 않습니다.
- 서버에서는 `.env` 대신 Render 환경변수 `NEXON_API_KEY`를 사용합니다.
- Render 무료 플랜은 일정 시간 사용하지 않으면 잠들 수 있어 첫 접속이 느릴 수 있습니다.
- 여러 사람이 동시에 조회하면 같은 Nexon API 키의 호출 한도를 함께 사용합니다.

## Render 직접 설정값

Blueprint 대신 Web Service를 직접 만들 경우 아래 값으로 설정합니다.

```text
Runtime: Python
Build Command: pip install -r requirements.txt
Start Command: python app/server.py
Health Check Path: /api/health
Environment Variables:
  HOST=0.0.0.0
  PORT=10000
  NEXON_API_KEY=your_key
```
