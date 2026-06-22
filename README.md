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

## 계산식 검증

레테를 포함한 KMS 48개 직업의 상세식, 환산 보정, 전투력 모델 커버리지를 확인합니다.
직업 상세식, 환산 배율, 전투력 모델, 내장 보정 근거의 직업 집합이 서로 같은지도 함께 검사합니다.

```powershell
python scripts\verify_calculation.py
```

로컬에 보정용 JSON 파일(`calibration-results.json`, `calibration-rankings.json`)이 있을 때는 직업별 보정 배율이 저장된 원사이트 샘플과 계속 맞는지도 확인할 수 있습니다.
앱 응답에는 각 직업에 적용된 내장 보정 표본, 원본 환산값, raw 환산값, 배율, 표본 오차가 함께 포함됩니다.
장비/어빌리티/하이퍼스탯 프리셋을 선택하면 해당 조합 기준의 개선 우선순위도 함께 표시됩니다.

```powershell
python scripts\verify_calibration_tables.py
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
