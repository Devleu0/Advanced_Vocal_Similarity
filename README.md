# 🎙️ Vocal Similarity Pipeline (보컬 유사도 분석 파이프라인)

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2B-EE4C2C.svg)
![OS](https://img.shields.io/badge/OS-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green.svg)

유튜브 링크만으로 가수의 음색(Vocal)을 추출하고, 가수들 간의 보컬 유사도를 N:N으로 비교·분석하여 히트맵으로 시각화하는 완전 자동화 데이터 파이프라인입니다. 

본 프로젝트는 외부 실행 파일(`yt-dlp.exe`) 종속성을 제거하고 순수 파이썬 생태계로 통합하여 크로스 플랫폼(Windows, macOS, Linux)에서 원클릭으로 구동할 수 있도록 설계되었습니다.

---

## ✨ 핵심 기능 (Key Features)

*   **End-to-End 자동화 및 Pythonic 패키징:** 외부 바이너리 의존성 없이 `yt-dlp` 파이썬 패키지를 직접 호출합니다. 유튜브 링크 리스트만 제공하면 `음원 다운로드 ➔ 보컬 분리 ➔ 정제 ➔ 지문 추출 ➔ 시각화` 전 과정을 스스로 수행합니다.
*   **완벽한 이어하기 (Resumable Logic):** 예기치 않은 오류(네트워크 단절, VRAM 부족 등)로 프로그램이 종료되어도 재실행 시 완료된 지점(다운로드, 보컬 분리, 지문 추출 등)을 자동 파악하여 멈춘 부분부터 다시 시작합니다.
*   **VRAM 최적화 및 고속 배치 추론:** 5초 단위의 청킹(Chunking)과 `Batch` 단위 추론을 결합하여, RTX 3050(4GB) 등 제한된 GPU 환경에서도 OOM(Out of Memory) 없이 빠르고 안정적으로 동작합니다.
*   **아웃라이어 필터링 알고리즘:** 코러스, 기계음, 숨소리가 포함된 불량 조각들을 VAD(Voice Activity Detection)와 코사인 유사도 상위 K% 추출 기법으로 자동 제거하여 극강의 정확도를 보장합니다.
*   **OS 독립적 한글 폰트 지원:** 윈도우(`Malgun Gothic`), 맥(`AppleGothic`), 리눅스(`NanumGothic`) 환경을 자동 감지하여 시각화 결과물에 한글이 깨지지 않도록 방지합니다.

---

## 💻 사전 요구 사항 (Prerequisites)

1.  **Python 3.11 이상**
2.  **NVIDIA GPU 및 CUDA Toolkit (11.8 이상 권장)** 
3.  **FFmpeg (필수):** 오디오 파일 변환 및 처리를 위해 반드시 시스템 환경 변수(`PATH`)에 등록되어 있어야 합니다.

---

## 🚀 퀵 스타트 가이드 (Quick Start)

### STEP 1. 설치 및 환경 세팅
프로젝트를 다운로드하고 기본 설정된 `run.bat` (Windows 기준) 파일을 실행하면 가상환경 구축과 필수 라이브러리 설치가 자동으로 진행됩니다.

수동으로 세팅할 경우 아래 명령어를 사용하세요:
```bash
python -m venv venv
source venv/Scripts/activate  # (Windows의 경우 venv\Scripts\activate)
pip install -r requirements.txt

```

### STEP 2. 입력 데이터 준비 (`inputs/`)

프로젝트 최상위 경로에 `inputs` 폴더를 생성하고, 분석하고 싶은 **가수(또는 그룹)의 이름을 파일명**으로 하여 `.txt` 파일을 만듭니다.
파일 내부에 분석할 유튜브 영상의 주소를 **한 줄에 하나씩** 입력하고 저장합니다.

**`inputs/아이유.txt` 예시:**

```text
[https://www.youtube.com/watch?v=abcd1234efg](https://www.youtube.com/watch?v=abcd1234efg)
[https://youtu.be/xyz9876qwer](https://youtu.be/xyz9876qwer)

```

### STEP 3. 파이프라인 실행

제공된 `run.bat`을 더블 클릭하거나 터미널에서 메인 스크립트를 실행합니다.

```bash
python main.py

```

### STEP 4. 결과물 확인 (`database/`)

실행이 완료되면 자동으로 생성된 `database` 폴더 내부에 다음 2개의 최종 결과물이 생성됩니다.

* **`vocal_clustermap.png`:** 가수의 수에 비례하여 동적으로 크기가 조절되며, 가독성 높은 `mako` 컬러맵이 적용된 유사도 히트맵 및 계층적 군집(Dendrogram) 이미지.
* **`vocal_similarities.txt`:** 정확한 유사도 수치(0.00 ~ 1.00)가 기록된 매트릭스 텍스트 파일.

---

## 📁 프로젝트 구조 (Directory Structure)

```text
vocal-similarity/
│
├── main.py            # 파이프라인 실행 메인 스크립트
├── run.bat                # 원클릭 실행 및 가상환경 세팅 배치 파일
├── requirements.txt       # 파이썬 의존성 패키지 목록
├── README.md              # 프로젝트 설명서
│
├── inputs/                # [사용자 영역] 입력 데이터 폴더 (직접 생성 필요)
│   ├── 가수A.txt          # 유튜브 URL 목록 (엔터로 구분)
│   └── 가수B.txt 
│
└── database/              # [자동 생성] 작업 진행 및 최종 결과물 폴더
    ├── 가수A/             # 아티스트별 임시 파일 및 최종 지문(.pt) 저장 공간
    ├── vocal_clustermap.png    # [최종 결과물] 유사도 히트맵 이미지
    └── vocal_similarities.txt  # [최종 결과물] 수치형 텍스트 매트릭스

```

---

## ⚙️ 상세 설정 및 튜닝 (Configuration)

`pipeline.py` 상단에 분리된 하이퍼파라미터 설정값을 수정하여 환경에 맞게 튜닝할 수 있습니다.

| 변수명 | 기본값 | 설명 및 튜닝 가이드 |
| --- | --- | --- |
| `SR` | `16000` | 오디오 샘플링 레이트. (SpeechBrain 모델의 기본값이므로 변경하지 않는 것을 권장합니다.) |
| `CHUNK_SEC` | `5` | 오디오를 쪼개는 단위(초). VRAM 오버플로우를 막는 핵심 변수입니다. VRAM이 넉넉하다면 `10` 정도로 늘려 처리 속도를 높일 수 있습니다. |
| `VAD_RMS_THRESHOLD` | `0.01` | 무음/숨소리를 판단하는 데시벨 임계값. 값이 클수록 미세한 소리는 모두 무시(삭제)됩니다. |
| `EMB_TOP_K_RATIO` | `0.8` | 최종 지문 생성 시 사용할 상위 데이터의 비율(0.1 ~ 1.0). `0.8`은 추출된 전체 오디오 조각 중 노이즈로 추정되는 하위 20%를 버린다는 뜻입니다. |

---

## ❓ 트러블슈팅 및 FAQ (Troubleshooting)

* **Q. `FFmpegExtractAudioError` 관련 에러가 발생해요.**
* 시스템(OS)에 FFmpeg가 설치되지 않았거나 환경 변수에 등록되지 않아서 발생합니다. FFmpeg를 설치하고 `PATH`에 등록한 뒤 시스템(터미널)을 재시작해 주세요.


* **Q. 진행 중 `CUDA out of memory` 에러가 납니다.**
* GPU의 VRAM이 부족하여 발생합니다. `pipeline.py` 상단의 `CHUNK_SEC` 값을 `5`에서 `3` 또는 `2`로 줄여서 다시 실행해 보세요. 진행된 내역은 자동 저장되므로 재실행 시 멈춘 부분부터 이어서 진행됩니다.


* **Q. 중간에 유튜브 링크를 추가/수정하고 싶어요.**
* 언제든 `inputs/*.txt` 파일을 수정하셔도 됩니다. 파이프라인을 재실행하면, 기존에 추출이 완료된(최종 `.pt` 파일이 존재하는) 영상은 자동으로 `[Skip]` 처리되고 새로 추가된 URL만 똑똑하게 추출 및 처리합니다.

