import os
import glob
import re
import platform
import numpy as np
import torch
import torchaudio
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import yt_dlp
from audio_separator.separator import Separator
from speechbrain.inference.speaker import EncoderClassifier

# === [ OS별 한글 폰트 설정 ] ===
# 시각화 시 아티스트명 한글 깨짐 방지
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin': # Mac
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic') # Linux
plt.rcParams['axes.unicode_minus'] = False 


# === [ Configuration & Setup ] ===
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[*] 사용할 디바이스: {DEVICE}")

BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, "inputs")
DB_DIR = os.path.join(BASE_DIR, "database")

# 하이퍼파라미터 및 설정값
SR = 16000                # SpeechBrain 기본 Sample Rate
CHUNK_SEC = 5             # VRAM 최적화를 위한 5초 청킹
VAD_RMS_THRESHOLD = 0.01  # 무음 판단 임계값 (매직 넘버 분리)
EMB_TOP_K_RATIO = 0.8     # 아웃라이어 제거 시 상위 % 유지 비율 (매직 넘버 분리)

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# 1. SpeechBrain ECAPA-TDNN 모델 로드
print("[*] SpeechBrain 모델 로딩 중...")
classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    run_opts={"device": DEVICE},
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

# 2. Audio-Separator 설정
print("[*] 음원 분리(MDX-Net) 모델 설정 중...")
separator = Separator()
separator.load_model(model_filename='UVR-MDX-NET-Inst_HQ_3.onnx')

def extract_video_id(url):
    """유튜브 URL에서 11자리 비디오 ID 추출 (youtu.be 단축 링크 포함)"""
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None

def process_url(url, artist_name):
    vid = extract_video_id(url)
    if not vid:
        print(f"  [오류] 올바르지 않은 유튜브 URL 형식입니다: {url}")
        return

    artist_dir = os.path.join(DB_DIR, artist_name)
    os.makedirs(artist_dir, exist_ok=True)

    raw_path = os.path.join(artist_dir, f"raw_{vid}.mp3")
    vocal_path = os.path.join(artist_dir, f"vocal_{vid}.mp3")
    emb_path = os.path.join(artist_dir, f"emb_{vid}.pt")

    # [RESUMABLE LOGIC] 최종 지문이 있으면 전체 스킵
    if os.path.exists(emb_path):
        print(f"  [Skip] 이미 추출된 지문이 존재합니다. (URL ID: {vid}) - PASS")
        return

    # [RESUMABLE LOGIC] 보컬 파일이 없으면 다운로드 및 분리 시작
    if not os.path.exists(vocal_path):
        # Step 1: 다운로드 (yt-dlp Python API 적용)
        if not os.path.exists(raw_path):
            print(f"  [Step 1] 다운로드 시작 (URL ID: {vid})")
            
            # 파일명 버그 방지를 위해 확장자 부분을 안전하게 분리 적용
            base_raw_path, _ = os.path.splitext(raw_path)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f"{base_raw_path}.%(ext)s", 
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,        
                'no_warnings': True,  
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                print(f"  [오류] 다운로드 실패 (URL ID: {vid}) | 사유: {e}")
                return
        else:
            print(f"  [Step 1 Skip] 원본 오디오가 이미 존재합니다. (URL ID: {vid})")

        # Step 2: 음원 분리
        print(f"  [Step 2] 보컬 분리 중 (URL ID: {vid})")
        separator.output_dir = artist_dir
        separator.output_format = "MP3"
        
        try:
            primary_out, secondary_out = separator.separate(raw_path)
            
            for out_file in [primary_out, secondary_out]:
                if "Vocals" in out_file or "vocals" in out_file.lower():
                    os.rename(os.path.join(artist_dir, out_file), vocal_path)
                else:
                    os.remove(os.path.join(artist_dir, out_file))
            
            if os.path.exists(raw_path):
                os.remove(raw_path)
                print(f"  -> 용량 확보: raw_{vid}.mp3 삭제 완료")
        except Exception as e:
            print(f"  [오류] 음원 분리 실패 (URL ID: {vid}): {e}")
            return
            
    else:
        print(f"  [Step 1-2 Skip] 분리된 보컬 오디오가 이미 존재합니다. (URL ID: {vid})")

    # [예외 처리 강화] 보컬 파일이 정상 생성되었는지 최종 확인
    if not os.path.exists(vocal_path):
        print(f"  [오류] 분리된 보컬 파일을 찾을 수 없거나 생성되지 않았습니다. (URL ID: {vid})")
        return

    # Step 3 & 4: 정제(VAD), 청킹, 임베딩 추출
    print(f"  [Step 3-4] 지문 추출 및 최적화 진행 중 (URL ID: {vid})")
    try:
        waveform, sr = torchaudio.load(vocal_path)
        if sr != SR:
            waveform = torchaudio.functional.resample(waveform, orig_freq=sr, new_freq=SR)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
            
        # Volume Normalization 적용
        waveform = waveform / (waveform.abs().max() + 1e-8)

        chunk_size = SR * CHUNK_SEC
        chunks = list(torch.split(waveform, chunk_size, dim=1))
        
        if chunks[-1].shape[1] < SR * 1:
            chunks = chunks[:-1]

        valid_chunks = []
        for chunk in chunks:
            rms = torch.sqrt(torch.mean(chunk ** 2))
            if rms >= VAD_RMS_THRESHOLD:
                valid_chunks.append(chunk)

        if not valid_chunks:
            print(f"  [오류] 유효한 오디오 구간이 없습니다. (URL ID: {vid})")
            return

        # [성능 최적화] Batch 단위로 한 번에 추출하여 속도 극대화
        # shape: (Batch, 1, Length) -> squeeze(1) -> (Batch, Length)
        batch_chunks = torch.stack(valid_chunks).squeeze(1).to(DEVICE)
        
        with torch.no_grad():
            embs = classifier.encode_batch(batch_chunks) 
            embs_tensor = embs.squeeze().cpu()
            
            # Batch 사이즈가 1일 경우 차원이 줄어드는 것 방지
            if embs_tensor.dim() == 1:
                embs_tensor = embs_tensor.unsqueeze(0)

        # 평균값 대비 코사인 유사도를 활용한 상위 K개 아웃라이어 필터링
        mean_emb_temp = embs_tensor.mean(dim=0, keepdim=True)
        sims = torch.nn.functional.cosine_similarity(embs_tensor, mean_emb_temp)
        
        k = max(1, int(EMB_TOP_K_RATIO * len(embs_tensor)))
        top_indices = torch.topk(sims, k).indices
        refined_embs = embs_tensor[top_indices]
        
        final_embedding = refined_embs.mean(dim=0)
        torch.save(final_embedding, emb_path)
        print(f"  -> 최종 지문 저장 완료: emb_{vid}.pt")

    except Exception as e:
        print(f"  [오류] 지문 추출 실패 (URL ID: {vid}): {e}")
    finally:
        if DEVICE == "cuda":
            torch.cuda.empty_cache()

def master_profile_and_visualization():
    print("\n" + "="*50)
    print("[*] [Step 5] 전체 마스터 프로필 생성 및 시각화 시작")
    print("="*50)
    
    artist_dirs = [d for d in glob.glob(os.path.join(DB_DIR, "*")) if os.path.isdir(d)]
    master_profiles = {}

    for adir in artist_dirs:
        artist_name = os.path.basename(adir)
        emb_files = glob.glob(os.path.join(adir, "emb_*.pt"))
        if not emb_files:
            continue
        
        embs = [torch.load(f, weights_only=True) for f in emb_files]
        master_emb = torch.stack(embs).mean(dim=0)
        master_emb = torch.nn.functional.normalize(master_emb, p=2, dim=0)
        master_profiles[artist_name] = master_emb
    
    if len(master_profiles) < 2:
        print("[!] 비교할 가수가 2명 이상이어야 시각화가 가능합니다.")
        return

    artists = list(master_profiles.keys())
    matrix = torch.zeros((len(artists), len(artists)))

    for i, a1 in enumerate(artists):
        for j, a2 in enumerate(artists):
            sim = torch.nn.functional.cosine_similarity(
                master_profiles[a1].unsqueeze(0), 
                master_profiles[a2].unsqueeze(0)
            )
            matrix[i, j] = sim.item()

    df = pd.DataFrame(matrix.numpy(), index=artists, columns=artists)
    
    txt_path = os.path.join(DB_DIR, "vocal_similarities.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== Vocal Similarity Matrix ===\n")
        f.write(df.to_string())
    print(f"  -> 텍스트 결과물 저장: {txt_path}")

    # [시각화 개선] 아티스트 수에 비례하여 이미지 크기 조정 및 가독성 좋은 colormap(mako) 적용
    fig_size = max(8, len(artists))
    g = sns.clustermap(
        df, 
        annot=True, 
        fmt=".2f", 
        cmap="mako", 
        vmin=0.0, 
        vmax=1.0,
        figsize=(fig_size, fig_size)
    )
    g.fig.suptitle("Vocal Similarity Clustermap", y=1.05)
    
    png_path = os.path.join(DB_DIR, "vocal_clustermap.png")
    g.savefig(png_path, dpi=300, bbox_inches='tight') 
    plt.close('all') 
    print(f"  -> 시각화 결과물 저장: {png_path}")

def main():
    print("="*50)
    print(" End-to-End Vocal Similarity Pipeline Started")
    print("="*50)

    txt_files = glob.glob(os.path.join(INPUT_DIR, "*.txt"))
    if not txt_files:
        print("[!] 'inputs' 폴더에 처리할 .txt 파일이 없습니다.")
        return

    for txt_file in txt_files:
        artist_name = os.path.splitext(os.path.basename(txt_file))[0]
        print(f"\n>> 처리 중인 아티스트: [{artist_name}]")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        for idx, url in enumerate(urls, 1):
            print(f"  [{idx}/{len(urls)}] Processing: {url}")
            process_url(url, artist_name)
    
    master_profile_and_visualization()
    print("\n[*] 모든 파이프라인 처리가 완료되었습니다!")

if __name__ == "__main__":
    main()