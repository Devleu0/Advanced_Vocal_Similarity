import os
import torch
import torchaudio
import yt_dlp
import config
from utils import extract_video_id
from logger import log

import os
import torch
import torchaudio
import yt_dlp
import config
from utils import extract_video_id
from logger import log
from demucs.separate import main as demucs_main
import shutil
from pathlib import Path

def process_url(url, artist_name, classifier):
    vid = extract_video_id(url)
    if not vid:
        log.error(f"  [오류] 올바르지 않은 유튜브 URL 형식입니다: {url}")
        return

    artist_dir = os.path.join(config.DB_DIR, artist_name)
    os.makedirs(artist_dir, exist_ok=True)

    raw_path = os.path.join(artist_dir, f"raw_{vid}.mp3")
    vocal_path = os.path.join(artist_dir, f"vocal_{vid}.mp3")
    emb_path = os.path.join(artist_dir, f"emb_{vid}.pt")

    if os.path.exists(emb_path):
        log.info(f"  [Skip] 이미 추출된 지문이 존재합니다. (URL ID: {vid}) - PASS")
        return

    if not os.path.exists(vocal_path):
        if not os.path.exists(raw_path):
            log.info(f"  [Step 1] 다운로드 시작 (URL ID: {vid})")
            base_raw_path, _ = os.path.splitext(raw_path)
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f"{base_raw_path}.%(ext)s",
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'quiet': True,
                'no_warnings': True,
                'logtostderr': False,
                'noprogress': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                log.error(f"  [오류] 다운로드 실패 (URL ID: {vid}) | 사유: {e}", exc_info=True)
                return
        else:
            log.info(f"  [Step 1 Skip] 원본 오디오가 이미 존재합니다. (URL ID: {vid})")

        log.info(f"  [Step 2] 보컬 분리 중 (URL ID: {vid})")
        demucs_output_dir = os.path.join(artist_dir, "demucs_separated")
        try:
            # Note: demucs.separate.main is designed to be called from the command line.
            # We are using it programmatically here. It expects a list of string arguments.
            # We want to separate to vocals and other, and output as mp3.
            demucs_main([
                "--two-stems", "vocals",
                "--out", demucs_output_dir,
                "--mp3",
                raw_path
            ])
            
            # Find the separated vocal file. Default model is htdemucs.
            # The output path will be something like:
            # <demucs_output_dir>/htdemucs/raw_{vid}/vocals.mp3
            raw_filename = Path(raw_path).stem
            separated_vocal_file = Path(demucs_output_dir) / "htdemucs" / raw_filename / "vocals.mp3"

            if separated_vocal_file.exists():
                shutil.move(str(separated_vocal_file), vocal_path)
                log.info(f"  -> 보컬 파일 저장 완료: {vocal_path}")
            else:
                raise FileNotFoundError("Demucs에 의해 생성된 보컬 파일을 찾을 수 없습니다.")

            # Clean up
            if os.path.exists(raw_path):
                os.remove(raw_path)
                log.info(f"  -> 용량 확보: raw_{vid}.mp3 삭제 완료")
            if os.path.exists(demucs_output_dir):
                shutil.rmtree(demucs_output_dir)
                log.info(f"  -> 임시 분리 폴더 삭제 완료")

        except Exception as e:
            log.error(f"  [오류] 음원 분리 실패 (URL ID: {vid}): {e}", exc_info=True)
            # Clean up demucs dir on failure too
            if os.path.exists(demucs_output_dir):
                shutil.rmtree(demucs_output_dir)
            return
    else:
        log.info(f"  [Step 1-2 Skip] 분리된 보컬 오디오가 이미 존재합니다. (URL ID: {vid})")

    if not os.path.exists(vocal_path):
        log.error(f"  [오류] 분리된 보컬 파일을 찾을 수 없거나 생성되지 않았습니다. (URL ID: {vid})")
        return

    log.info(f"  [Step 3-4] 지문 추출 및 최적화 진행 중 (URL ID: {vid})")
    try:
        waveform, sr = torchaudio.load(vocal_path)
        if sr != config.SR:
            waveform = torchaudio.functional.resample(waveform, orig_freq=sr, new_freq=config.SR)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        waveform = waveform / (waveform.abs().max() + 1e-8)
        chunk_size = config.SR * config.CHUNK_SEC
        chunks = list(torch.split(waveform, chunk_size, dim=1))
        
        if chunks and chunks[-1].shape[1] < config.SR * 1:
            chunks = chunks[:-1]

        valid_chunks = [chunk for chunk in chunks if torch.sqrt(torch.mean(chunk ** 2)) >= config.VAD_RMS_THRESHOLD]

        if not valid_chunks:
            log.warning(f"  [주의] 유효한 오디오 구간이 없습니다. (URL ID: {vid})")
            return

        batch_chunks = torch.stack(valid_chunks).squeeze(1).to(config.DEVICE)
        
        with torch.no_grad():
            embs = classifier.encode_batch(batch_chunks)
            embs_tensor = embs.squeeze().cpu()
            if embs_tensor.dim() == 1:
                embs_tensor = embs_tensor.unsqueeze(0)

        mean_emb_temp = embs_tensor.mean(dim=0, keepdim=True)
        sims = torch.nn.functional.cosine_similarity(embs_tensor, mean_emb_temp)
        
        k = max(1, int(config.EMB_TOP_K_RATIO * len(embs_tensor)))
        top_indices = torch.topk(sims, k).indices
        refined_embs = embs_tensor[top_indices]
        
        final_embedding = refined_embs.mean(dim=0)
        torch.save(final_embedding, emb_path)
        log.info(f"  -> 최종 지문 저장 완료: emb_{vid}.pt")

    except Exception as e:
        log.error(f"  [오류] 지문 추출 실패 (URL ID: {vid}): {e}", exc_info=True)
    finally:
        if config.DEVICE == "cuda":
            torch.cuda.empty_cache()
