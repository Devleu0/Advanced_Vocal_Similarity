# Advanced Vocal Similarity (음성 유사도 분석)

[![Python CI](https://github.com/dnlwj/Advanced_Vocal_Similarity/actions/workflows/ci.yml/badge.svg)](https://github.com/dnlwj/Advanced_Vocal_Similarity/actions/workflows/ci.yml)

**Advanced Vocal Similarity**는 여러 유튜브 영상에 등장하는 인물들의 목소리를 분석하여 서로 얼마나 유사한지 측정하고 시각화하는 파이프라인입니다. 딥러닝 기반의 음성 분석 모델을 사용하여 각 영상의 오디오에서 보컬 "지문(fingerprint)"을 추출하고, 이를 상호 비교하여 유사도 점수를 계산합니다.

## ✨ 주요 기능

- **유튜브 영상 지원**: 유튜브 URL만 제공하면 자동으로 오디오를 다운로드합니다.
- **자동 보컬 분리**: Demucs 모델을 사용하여 배경 음악이나 잡음에서 보컬 목소리만 정확하게 분리합니다.
- **음성 지문 추출**: 최신 음성 인식 모델(ECAPA-TDNN)을 통해 각 보컬의 고유한 특징을 벡터(Embedding)로 추출합니다.
- **유사도 분석 및 시각화**: 추출된 모든 음성 지문을 상호 비교하여 코사인 유사도를 계산하고, 결과를 히트맵으로 시각화하여 한눈에 파악할 수 있도록 돕습니다.
- **설정 유연성**: `config.py` 파일을 통해 VAD(음성 감지), 이상치 제거, 오디오 품질 등 다양한 처리 옵션을 쉽게 조정할 수 있습니다.

## ⚙️ 작동 방식 (Pipeline)

프로젝트는 다음 4단계의 자동화된 파이프라인으로 구성됩니다.

1.  **입력 (Input)**: `inputs` 폴더에 `아티스트명.txt` 파일을 생성하고, 그 안에 분석할 유튜브 영상 URL 목록을 넣습니다.
2.  **다운로드 및 변환 (Download & Convert)**: `yt-dlp`와 `ffmpeg`을 사용하여 각 URL에서 오디오를 다운로드하고, 표준 형식(MP3, 16kHz, mono)으로 변환합니다.
3.  **처리 (Processing)**:
    - **보컬 분리**: `demucs`를 이용해 오디오에서 보컬 트랙을 분리합니다.
    - **지문 추출**: 분리된 보컬 트랙을 작은 조각(chunk)으로 나누고, `SpeechBrain` 모델로 각 조각의 임베딩을 추출한 뒤, 평균을 내어 해당 영상의 최종 음성 지문을 생성합니다.
4.  **분석 및 시각화 (Analysis & Visualization)**: 모든 음성 지문 간의 코사인 유사도를 계산하고, `seaborn`과 `matplotlib`을 사용해 결과를 히트맵(`similarity_matrix.png`)으로 저장합니다.

## 📂 프로젝트 구조

```
.
├── inputs/            # 분석할 유튜브 URL 목록 (txt 파일)을 이곳에 추가
│   └── artist_A.txt
├── database/          # 처리 과정에서 생성된 파일들이 저장되는 공간
│   └── artist_A/
│       ├── raw_{vid}.mp3       # 원본 오디오
│       ├── vocal_{vid}.mp3     # 분리된 보컬
│       └── emb_{vid}.pt        # 추출된 음성 지문 (임베딩)
├── config.py          # 프로젝트의 모든 설정을 관리하는 파일
├── main.py            # 메인 파이프라인 실행 스크립트
├── run.bat            # Windows 사용자를 위한 간편 실행 스크립트
├── requirements.txt   # 필요한 Python 라이브러리 목록
└── similarity_matrix.png # 최종 결과물인 유사도 행렬 이미지
```

## 🚀 설치

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
git clone https://github.com/your-username/Advanced_Vocal_Similarity.git
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

## ▶️ 사용법

1.  `inputs` 폴더 안에 `아티스트명.txt` 형식의 텍스트 파일을 생성합니다. (예: `iu.txt`)
2.  해당 파일 안에 분석하고 싶은 유튜브 영상의 URL을 한 줄에 하나씩 추가합니다.
3.  `run.bat`를 실행하거나, 터미널에서 `python main.py` 명령을 실행합니다.
4.  처리가 완료되면 프로젝트 루트 디렉토리에 결과물인 `similarity_matrix.png` 파일이 생성됩니다.

## 🔧 설정 (Configuration)

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

## 🧑‍💻 개발 및 테스트

이 프로젝트에 기여하고 싶은 개발자는 다음 가이드를 참고하세요.

### 개발 환경 설정

`requirements-dev.txt` 파일에는 `ruff` (린터), `pytest` (테스터) 등 개발에 필요한 도구가 포함되어 있습니다.

```bash
# 개발용 라이브러리 설치
pip install -r requirements-dev.txt
```

### 코드 스타일 검사 (Linting)

코드를 커밋하기 전, `ruff`를 사용하여 코드 스타일과 잠재적인 오류를 검사하세요.

```bash
ruff check .
```

### 테스트 실행

`pytest`를 사용하여 `tests/` 폴더에 있는 모든 테스트를 실행할 수 있습니다.

```bash
python -m pytest tests/
```

## 📜 라이선스

이 프로젝트는 [MIT License](LICENSE)에 따라 배포됩니다. (라이선스 파일을 추가해주세요)

## 🙏 감사의 말

이 프로젝트는 다음과 같은 훌륭한 오픈소스 라이브러리들 덕분에 가능했습니다.

- [PyTorch](https://pytorch.org/)
- [SpeechBrain](https://speechbrain.github.io/)
- [Demucs](https://github.com/facebookresearch/demucs)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
