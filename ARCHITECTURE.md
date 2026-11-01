# Architecture

애플리케이션 코드는 `vocal_similarity/` 패키지에 모으고, 입력·산출물·모델 파일과
실행 스크립트는 저장소 루트에 둡니다. CLI 와 웹 UI 는 같은 오케스트레이션
(`vocal_similarity/pipeline.py`)을 공유하는 얇은 **프런트엔드**입니다.

```
main.py (호환 CLI 진입점)      web.py (웹 UI 진입점)
         \                      /
          vocal_similarity/
          ├─ main.py             CLI 실행 로직
          ├─ pipeline.py         단계 순서, 진행 콜백, 취소
          ├─ input_store.py      inputs/<아티스트>.txt 포맷·이름 검증
          ├─ processing.py       yt-dlp/ffmpeg/demucs I/O 및 임베딩 저장
          │   └─ fingerprint.py  순수 로직: 전처리, 청킹, VAD, 임베딩 집계
          ├─ visualization.py    임베딩 로드, 유사도 출력/시각화
          │   └─ similarity.py   순수 로직: 프로필·코사인 유사도 행렬
          └─ webapp/              FastAPI 라우터·서비스·정적 파일
```

- `fingerprint.py`, `similarity.py` 는 `config`/파일시스템에 의존하지 않고 인자만 받으므로 `tests/` 에서 합성 텐서로 단위 테스트합니다.
- 알고리즘(VAD, 이상치 제거, 유사도 계산)을 바꿀 때는 위 두 모듈과 해당 테스트만 수정하면 됩니다.
- 새 단계를 추가할 때는 순수 로직은 별도 모듈로 두고, `vocal_similarity/processing.py` 는 호출만 하도록 유지하세요.
  단계 순서는 `vocal_similarity.pipeline.run_pipeline` 에 추가하면 CLI·웹 UI 모두에 반영됩니다
  (웹 진행 표시는 `vocal_similarity/webapp/static/js/jobs.js` 의 `STAGES` 에 같은 키를 추가).

## Web UI (`vocal_similarity/webapp/`)

```
vocal_similarity/webapp/
├─ app.py            create_app(runner=None): 서비스 생성 → app.state, 라우터·정적 파일 등록
├─ dependencies.py   app.state 의 서비스를 FastAPI Depends 로 주입
├─ schemas.py        요청/응답 모델 (서비스 dataclass ↔ JSON)
├─ routers/          HTTP 계층: 검증·상태코드 변환만 (비즈니스 로직 없음)
│   ├─ artists.py      /api/artists
│   ├─ jobs.py         /api/jobs
│   └─ results.py      /api/results
├─ services/         도메인 계층 (FastAPI 비의존 → 단독 테스트 가능)
│   ├─ artists.py      입력 관리 + URL 별 처리 상태(database/ 파일 존재 여부)
│   ├─ jobs.py         JobManager: 단일 백그라운드 작업, 진행률, 스레드별 로그 수집, 취소
│   ├─ runner.py       실제 파이프라인 runner (모델 1회 로드 후 재사용, 무거운 import 지연)
│   └─ results.py      유사도 행렬 JSON/CSV, 클러스터맵 경로
└─ static/           빌드 단계 없는 프런트엔드
    ├─ index.html
    ├─ css/style.css
    └─ js/  main.js(패널 연결) · api.js(HTTP) · dom.js(유틸) · artists.js · jobs.js · results.js
```

설계 원칙

- **의존 방향**: `routers → services → (pipeline, input_store, visualization)`. 서비스는 FastAPI 를 모르고,
  코어 모듈은 웹을 모릅니다.
- **주입 가능한 runner**: `JobManager(runner)` 는 `runner(artists, on_progress, should_cancel)` 만 호출합니다.
  테스트는 `create_app(runner=fake)` 로 torch/speechbrain/demucs 없이 API 를 검증합니다.
- **동시 실행 1개**: 파이프라인은 GPU·같은 산출물 파일을 공유하므로 실행 중 새 작업 요청은 409 를 반환합니다.
- **경로는 호출 시점의 `config` 값 사용**: 테스트에서 `vocal_similarity.config.INPUT_DIR`/`DB_DIR` 를 패치해 격리합니다.
- **프런트엔드는 패널별 ES 모듈**: 서버 호출은 `api.js` 한 곳에서만, DOM 텍스트는 `textContent` 로만 삽입(XSS 방지).
