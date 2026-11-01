# Advanced Vocal Similarity (음성 유사도 분석)

[![Python CI](https://github.com/Devleu0/Advanced_Vocal_Similarity/actions/workflows/ci.yml/badge.svg)](https://github.com/Devleu0/Advanced_Vocal_Similarity/actions/workflows/ci.yml)

**Advanced Vocal Similarity**는 여러 유튜브 영상에 등장하는 인물들의 목소리를 분석하여 서로 얼마나 유사한지 측정하고 시각화하는 파이프라인입니다. 딥러닝 기반의 음성 분석 모델을 사용하여 각 영상의 오디오에서 보컬 "지문(fingerprint)"을 추출하고, 이를 상호 비교하여 유사도 점수를 계산합니다.

## 주요 기능

- **유튜브 영상 지원**: 유튜브 URL만 제공하면 자동으로 오디오를 다운로드합니다.
- **자동 보컬 분리**: Demucs 모델을 사용하여 배경 음악이나 잡음에서 보컬 목소리만 정확하게 분리합니다.
- **음성 지문 추출**: 최신 음성 인식 모델(ECAPA-TDNN)을 통해 각 보컬의 고유한 특징을 벡터(Embedding)로 추출합니다.
- **유사도 분석 및 시각화**: 추출된 모든 음성 지문을 상호 비교하여 코사인 유사도를 계산하고, 결과를 히트맵으로 시각화하여 한눈에 파악할 수 있도록 돕습니다.
- **웹 UI**: 브라우저에서 아티스트/URL 등록, 분석 실행·진행률·로그 확인, 유사도 히트맵·클러스터맵 조회까지 할 수 있습니다. ([웹 UI 사용법](#-웹-ui))
- **설정 유연성**: `config.py` 파일을 통해 VAD(음성 감지), 이상치 제거, 오디오 품질 등 다양한 처리 옵션을 쉽게 조정할 수 있습니다.

## 작동 방식 (Pipeline)

프로젝트는 다음 4단계의 자동화된 파이프라인으로 구성됩니다.

1.  **입력 (Input)**: `inputs` 폴더에 `아티스트명.txt` 파일을 생성하고, 그 안에 분석할 유튜브 영상 URL 목록을 넣습니다.
2.  **다운로드 및 변환 (Download & Convert)**: `yt-dlp`와 `ffmpeg`을 사용하여 각 URL에서 오디오를 다운로드하고, 표준 형식(MP3, 16kHz, mono)으로 변환합니다.
3.  **처리 (Processing)**:
    - **보컬 분리**: `demucs`를 이용해 오디오에서 보컬 트랙을 분리합니다.
    - **지문 추출**: 분리된 보컬 트랙을 작은 조각(chunk)으로 나누고, `SpeechBrain` 모델로 각 조각의 임베딩을 추출한 뒤, 평균을 내어 해당 영상의 최종 음성 지문을 생성합니다.
4.  **분석 및 시각화 (Analysis & Visualization)**: 모든 음성 지문 간의 코사인 유사도를 계산하고, `seaborn`과 `matplotlib`을 사용해 결과를 히트맵(`database/vocal_clustermap.png`)으로 저장합니다.

## 📂 프로젝트 구조

모듈 책임과 협업 가이드는 [ARCHITECTURE.md](ARCHITECTURE.md) 를 참고하세요.

```
.
├── inputs/            # 분석할 유튜브 URL 목록 (txt 파일)을 이곳에 추가
│   └── artist_A.txt
├── database/          # 처리 과정에서 생성된 파일들이 저장되는 공간
│   ├── artist_A/
│   │   ├── raw_{vid}.mp3       # 원본 오디오
│   │   ├── vocal_{vid}.mp3     # 분리된 보컬
│   │   └── emb_{vid}.pt        # 추출된 음성 지문 (임베딩)
│   ├── vocal_similarities.txt  # 유사도 행렬 (텍스트)
│   └── vocal_clustermap.png    # 최종 결과물 (클러스터맵)
├── config.py          # 프로젝트의 모든 설정을 관리하는 파일
├── main.py            # CLI 진입점 (pipeline.run_pipeline 호출)
├── web.py             # 웹 UI 진입점 (python web.py)
├── pipeline.py        # 단계 오케스트레이션 (CLI·웹 공용, 진행 콜백/취소 지원)
├── input_store.py     # inputs/<아티스트>.txt 읽기·쓰기·이름 검증
├── processing.py      # 다운로드/변환/보컬 분리 (I/O 오케스트레이션)
├── fingerprint.py     # 청킹·VAD·임베딩 집계 등 순수 함수 (테스트 용이)
├── similarity.py      # 마스터 프로필 / 유사도 행렬 계산 (순수 함수)
├── visualization.py   # 임베딩 로드 및 히트맵·텍스트 출력
├── models.py          # SpeechBrain 모델 로더
├── utils.py           # 한글 폰트 설정, 비디오 ID 추출
├── logger.py          # 로깅 설정
├── webapp/            # 웹 UI (FastAPI + 정적 프런트엔드)
│   ├── app.py         #   앱 팩토리 (create_app)
│   ├── routers/       #   HTTP 엔드포인트 (artists / jobs / results)
│   ├── services/      #   도메인 로직 (입력 관리, 백그라운드 작업, 결과 조회)
│   └── static/        #   HTML/CSS/ES 모듈 (빌드 단계 없음)
├── tests/             # pytest 단위 테스트 (tests/web: 웹 계층)
├── run.bat            # Windows 사용자를 위한 간편 실행 스크립트 (CLI)
├── run_web.bat        # Windows 용 웹 UI 실행 스크립트
├── requirements.txt   # 필요한 Python 라이브러리 목록
└── requirements-web.txt # 웹 UI 추가 의존성 (fastapi, uvicorn)
```

## 설치

### 필수 요구사항

- **Python 3.9 이상**
- **FFmpeg**: 시스템 PATH에 등록되어 있어야 합니다.
- **yt-dlp**: 시스템 PATH에 등록되어 있어야 합니다.

### 설치 과정

#### Windows 사용자

프로젝트에 포함된 `run.bat` 스크립트를 실행하면 가상 환경 생성, 라이브러리 설치, 파이프라인 실행까지 모든 과정이 자동으로 진행됩니다.

```bash
run.bat
```

#### macOS / Linux 사용자

수동으로 가상 환경을 설정하고 필요한 라이브러리를 설치해야 합니다.

```bash
# 1. Git 저장소를 복제합니다.
git clone https://github.com/Devleu0/Advanced_Vocal_Similarity.git
cd Advanced_Vocal_Similarity

# 2. Python 가상 환경을 생성하고 활성화합니다.
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. PyTorch를 먼저 설치합니다. (CPU 버전 기준)
# CUDA 지원 GPU가 있다면 공식 홈페이지(https://pytorch.org/)를 참고하여 GPU 버전을 설치하세요.
pip install torch torchaudio

# 4. 나머지 라이브러리를 설치합니다.
pip install -r requirements.txt
```

## 사용법

1.  `inputs` 폴더 안에 `아티스트명.txt` 형식의 텍스트 파일을 생성합니다. (예: `iu.txt`)
2.  해당 파일 안에 분석하고 싶은 유튜브 영상의 URL을 한 줄에 하나씩 추가합니다.
3.  `run.bat`를 실행하거나, 터미널에서 `python main.py` 명령을 실행합니다.
4.  처리가 완료되면 `database/vocal_clustermap.png` 와 `database/vocal_similarities.txt` 가 생성됩니다.

## 🌐 웹 UI

터미널 대신 브라우저에서 전체 파이프라인을 사용할 수 있습니다.

```bash
pip install -r requirements-web.txt   # 최초 1회 (requirements.txt 설치 후)
python web.py                         # http://localhost:8000
# 다른 PC 에서 접속하려면: python web.py --host 0.0.0.0 --port 8000
```

Windows 에서는 `run_web.bat` 을 실행하면 설치 → 서버 실행 → 브라우저 열기까지 자동으로 진행됩니다.

| 패널 | 기능 |
| --- | --- |
| **1. 아티스트 & URL** | 아티스트 추가/수정/삭제 (`inputs/<이름>.txt` 와 동일), URL 별 처리 상태(대기 → 다운로드됨 → 보컬 분리됨 → 지문 완료) 표시 |
| **2. 분석 실행** | 선택한 아티스트(또는 전체) 분석 시작, 단계별 진행률·실시간 로그, 취소 |
| **3. 유사도 결과** | 아티스트 간 유사도 히트맵 표, 클러스터맵 이미지, CSV 다운로드 |

- 웹 UI 와 CLI(`python main.py`)는 같은 `inputs/`, `database/` 폴더와 같은 파이프라인 코드(`pipeline.py`)를 사용하므로 섞어서 사용해도 됩니다.
- 분석 작업은 GPU·파일을 공유하므로 **동시에 하나만** 실행됩니다. SpeechBrain 모델은 첫 작업에서 한 번만 로드되어 이후 작업에서 재사용됩니다.
- API 문서(Swagger)는 `http://localhost:8000/docs` 에서 볼 수 있습니다.

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/api/artists` | 아티스트 목록 + URL 별 처리 상태 |
| `PUT` | `/api/artists/{name}` | 아티스트 생성/URL 목록 덮어쓰기 (`{"urls": [...]}`) |
| `DELETE` | `/api/artists/{name}?purge=true` | 삭제 (`purge` 시 `database/<이름>` 도 삭제) |
| `POST` | `/api/jobs` | 분석 시작 (`{"artists": [...]}`, 생략 시 전체). 실행 중이면 409 |
| `GET` | `/api/jobs/{id}?log_offset=N` | 진행 상태 + N번째 줄 이후 로그 |
| `POST` | `/api/jobs/{id}/cancel` | 취소 (처리 중인 URL 완료 후 중단) |
| `GET` | `/api/results/similarity` | 유사도 행렬 JSON (`.csv` 도 지원) |
| `GET` | `/api/results/clustermap.png` | 마지막 실행에서 생성된 클러스터맵 |

> ⚠️ 웹 UI 에는 인증 기능이 없습니다. `--host 0.0.0.0` 으로 외부에 공개할 때는 신뢰할 수 있는 네트워크에서만 사용하세요.

## 설정 (Configuration)

`config.py` 파일에서 파이프라인의 세부 동작을 조정할 수 있습니다.

| 설정 항목                 | 설명                                                                                                | 기본값                  |
| ------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------- |
| `DEVICE`                  | 모델 연산에 사용할 장치 (`"cuda:0"` 또는 `"cpu"`)                                                     | 자동 감지               |
| `SR`                      | 오디오 처리 시 사용할 샘플 레이트 (Sample Rate)                                                       | `16000`                 |
| `CHUNK_SEC`               | 음성 지문 추출 시 오디오를 나눌 조각(chunk)의 길이 (초)                                               | `5`                     |
| `USE_VAD`                 | 음성이 없는 부분을 제거하는 VAD(Voice Activity Detection) 기술 사용 여부                              | `True`                  |
| `VAD_RMS_THRESHOLD`       | VAD에서 무음으로 판단할 RMS 임계값                                                                    | `0.01`                  |
| `USE_OUTLIER_REMOVAL`     | 평균에서 크게 벗어나는 이상치(outlier) 임베딩을 제거할지 여부                                         | `True`                  |
| `EMB_TOP_K_RATIO`         | 이상치 제거 시, 평균과 가장 유사한 상위 몇 %의 임베딩을 사용할지 결정                                 | `0.8` (상위 80%)        |
| `DOWNLOAD_AUDIO_QUALITY`  | `yt-dlp`로 다운로드할 오디오의 품질                                                                   | `"bestaudio/best"`      |
| `MP3_BITRATE`             | `ffmpeg`으로 변환할 MP3 파일의 비트레이트                                                             | `"192k"`                |
| `DEMUCS_MODEL`            | 보컬 분리에 사용할 Demucs 모델. (`htdemucs_ft`, `mdx_extra` 등)                                        | `"mdx_extra"`           |
| `CLEANUP_RAW_AUDIO`       | 처리 완료 후 변환된 원본 오디오(`raw_*.mp3`)를 삭제할지 여부                                          | `False`                 |

## 개발 및 테스트

이 프로젝트에 기여하고 싶은 개발자는 다음 가이드를 참고하세요.

### 개발 환경 설정

`requirements-dev.txt` 파일에는 `ruff` (린터), `pytest` (테스터) 등 개발에 필요한 도구가 포함되어 있습니다.

```bash
# 개발용 라이브러리 설치
pip install -r requirements-web.txt -r requirements-dev.txt
```

### 코드 스타일 검사 (Linting)

```bash
ruff check .
```

### 테스트 실행

```bash
python -m pytest tests/
```

- 알고리즘 로직(`fingerprint.py`, `similarity.py`)은 합성 텐서로 테스트합니다.
- `pipeline.py` 테스트는 각 단계를 mock 하여 실행 순서·진행 콜백·취소만 검증합니다.
- `tests/web/` 은 가짜 runner 를 주입한 `create_app(runner=...)` 으로 HTTP API 와 작업 상태 전이를 검증합니다 (모델·demucs 불필요).
- `processing.py` 테스트는 `subprocess`/`torchaudio` 를 mock 하며, demucs 가 없어도 `tests/conftest.py` 의 스텁으로 실행됩니다.

## 라이선스

이 프로젝트는 [MIT License](LICENSE)에 따라 배포됩니다.

## 감사의 말

이 프로젝트는 다음과 같은 훌륭한 오픈소스 라이브러리들 덕분에 가능했습니다.

- [PyTorch](https://pytorch.org/)
- [SpeechBrain](https://speechbrain.github.io/)
- [Demucs](https://github.com/facebookresearch/demucs)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
