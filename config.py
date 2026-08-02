import os
import torch

# === [ Path Configuration ] ===
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
DB_DIR = os.path.join(BASE_DIR, "database")
PRETRAINED_MODELS_DIR = os.path.join(BASE_DIR, "pretrained_models")

# === [ Hardware Configuration ] ===
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === [ Model & Processing Hyperparameters ] ===
SR = 16000                # SpeechBrain 기본 Sample Rate
CHUNK_SEC = 5             # VRAM 최적화를 위한 5초 청킹
VAD_RMS_THRESHOLD = 0.01  # 무음 판단 임계값
EMB_TOP_K_RATIO = 0.8     # 아웃라이어 제거 시 상위 % 유지 비율

# === [ Model Sources ] ===
SPEECHBRAIN_MODEL_SOURCE = "speechbrain/spkrec-ecapa-voxceleb"

# === [ Directory Setup ] ===
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
