import os
import torch

# === [ Path Configuration ] ===
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
DB_DIR = os.path.join(BASE_DIR, "database")
PRETRAINED_MODELS_DIR = os.path.join(BASE_DIR, "pretrained_models")

# === [ Hardware Configuration ] ===
DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"

# === [ Model & Processing Hyperparameters ] ===
SR = 16000                # SpeechBrain 기본 Sample Rate
CHUNK_SEC = 5             # VRAM 최적화를 위한 5초 청킹

# === [ Processing Options ] ===
# VAD (Voice Activity Detection) 설정
USE_VAD = True            # True일 경우, RMS 기반의 간단한 VAD를 사용하여 음성이 없는 청크를 제거합니다.
VAD_RMS_THRESHOLD = 0.01  # 무음 판단 임계값 (USE_VAD가 True일 때만 사용)

VAD_RELATIVE_RATIO = 0.0  # >0 이면 파일 내 90백분위 RMS 대비 이 비율 미만 청크도 제거 (예: 0.1). 0 이면 비활성화.
CHUNK_HOP_SEC = None      # None 이면 겹침 없음. CHUNK_SEC 보다 작게(예: 2.5) 주면 청크가 겹쳐 임베딩 수가 늘어납니다.
ENCODE_BATCH_SIZE = 32    # 임베딩 추출 시 한 번에 처리할 청크 수 (긴 영상의 메모리 보호)

# Outlier 제거 설정
USE_OUTLIER_REMOVAL = True # True일 경우, 평균 임베딩과 코사인 유사도가 가장 낮은 일부 청크를 아웃라이어로 간주하고 제거합니다.
EMB_TOP_K_RATIO = 0.8     # 아웃라이어 제거 시 상위 % 유지 비율 (USE_OUTLIER_REMOVAL이 True일 때만 사용)

# 유사도 계산 설정
USE_CENTERING = True      # 아티스트 공통 성분을 빼 아티스트 간 대비를 키웁니다 (아티스트가 CENTERING_MIN_ARTISTS 명 이상일 때만 적용).
CENTERING_MIN_ARTISTS = 5

# 오디오 품질 설정
DOWNLOAD_AUDIO_QUALITY = "bestaudio/best" # yt-dlp 다운로드 품질. 'bestaudio/best' 또는 'worstaudio/worst'
MP3_BITRATE = "192k"      # FFmpeg MP3 변환 비트레이트. 예: '128k', '192k', '256k'

# Demucs 보컬 분리 모델 설정
DEMUCS_MODEL = "mdx_extra" # 보컬 분리에 사용할 모델. 추천: htdemucs_ft, hdemucs_mmi, mdx_extra


# === [ File Management ] ===
DOWNLOAD_WORKERS = 4      # 동시 다운로드 수
CLEANUP_RAW_AUDIO = False # True로 설정 시, 처리 후 원본 raw_*.mp3 파일을 삭제합니다.

# === [ Embedding Model ] ===
# 선택 가능: "ecapa"(기본) | "wavlm-sv"(추천) | "resnet"   (설명: python main.py --list-models)
# 환경변수 VOCAL_EMBEDDING_MODEL 또는 `python main.py --model <key>` 로도 지정할 수 있습니다.
# 모델마다 임베딩 공간이 달라 파일이 따로 저장되며, 서로 섞어 비교하지 않습니다.
EMBEDDING_MODEL = os.environ.get("VOCAL_EMBEDDING_MODEL", "ecapa")
SPEECHBRAIN_MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

# === [ Directory Setup ] ===
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
