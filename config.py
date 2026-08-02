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

# Outlier 제거 설정
USE_OUTLIER_REMOVAL = True # True일 경우, 평균 임베딩과 코사인 유사도가 가장 낮은 일부 청크를 아웃라이어로 간주하고 제거합니다.
EMB_TOP_K_RATIO = 0.8     # 아웃라이어 제거 시 상위 % 유지 비율 (USE_OUTLIER_REMOVAL이 True일 때만 사용)

# 오디오 품질 설정
DOWNLOAD_AUDIO_QUALITY = "bestaudio/best" # yt-dlp 다운로드 품질. 'bestaudio/best' 또는 'worstaudio/worst'
MP3_BITRATE = "192k"      # FFmpeg MP3 변환 비트레이트. 예: '128k', '192k', '256k'

# Demucs 보컬 분리 모델 설정
DEMUCS_MODEL = "mdx_extra" # 보컬 분리에 사용할 모델. 추천: htdemucs_ft, hdemucs_mmi, mdx_extra


# === [ File Management ] ===
CLEANUP_RAW_AUDIO = False # True로 설정 시, 처리 후 원본 raw_*.mp3 파일을 삭제합니다.

# === [ Model Sources ] ===
SPEECHBRAIN_MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

# === [ Directory Setup ] ===
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
