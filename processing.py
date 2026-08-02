import os
import torch
import torchaudio
import config
import glob
import subprocess
from utils import extract_video_id
from logger import log
from demucs.separate import main as demucs_main
import shutil
from pathlib import Path

def download_original_audio(url, artist_name):
    """
    yt-dlp를 사용하여 원본 오디오를 임시 폴더에 다운로드합니다.
    """
    vid = extract_video_id(url)
    if not vid:
        log.error(f"  [오류] 올바르지 않은 유튜브 URL 형식입니다: {url}")
        return None, None

    artist_dir = os.path.join(config.DB_DIR, artist_name)
    temp_dir = os.path.join(artist_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    raw_path = os.path.join(artist_dir, f"raw_{vid}.mp3")
    # 최종 mp3 파일이 이미 있으면 임시 파일 다운로드를 건너뜁니다.
    if os.path.exists(raw_path):
        log.info(f"  [Download Skip] 최종 MP3 파일이 이미 존재합니다: {Path(raw_path).name}")
        return None, raw_path

    temp_path_template = os.path.join(temp_dir, f"temp_{vid}")
    
    # 임시 파일이 이미 있는지 확인
    existing_temp_files = glob.glob(f"{temp_path_template}.*")
    if existing_temp_files:
        log.info(f"  [Download Skip] 임시 파일이 이미 존재합니다: {Path(existing_temp_files[0]).name}")
        return existing_temp_files[0], raw_path

    log.info(f"  [Download] 원본 오디오 다운로드 시작: {url}")
    
    # 항상 안정적인 다운로드를 위해 URL을 정규화합니다.
    clean_url = f"https://www.youtube.com/watch?v={vid}"
    log.debug(f"  -> 정규화된 URL: {clean_url}")

    try:
        yt_dlp_command = [
            'yt-dlp', '-f', 'bestaudio/best',
            '-o', f"{temp_path_template}.%(ext)s", clean_url
        ]
        result = subprocess.run(yt_dlp_command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=300)
        log.debug(f"yt-dlp stdout: {result.stdout}")

        possible_files = glob.glob(f"{temp_path_template}.*")
        if not possible_files:
            raise FileNotFoundError("yt-dlp가 파일을 다운로드하지 못했습니다.")
        
        downloaded_file = possible_files[0]
        log.info(f"  -> 다운로드 완료: {Path(downloaded_file).name}")
        return downloaded_file, raw_path

    except FileNotFoundError as e:
        log.error(f"`yt-dlp` 실행 파일을 찾을 수 없습니다. PATH에 등록되었는지 확인하세요. 상세: {e}", exc_info=True)
    except subprocess.TimeoutExpired as e:
        log.error(f"  [오류] yt-dlp 시간 초과 (URL: {url}) | {e.stderr}", exc_info=True)
    except subprocess.CalledProcessError as e:
        log.error(f"  [오류] yt-dlp 실패 (URL: {url}) | {e.stderr}", exc_info=True)
    except Exception as e:
        log.error(f"  [오류] 다운로드 중 알 수 없는 오류 (URL: {url}) | {e}", exc_info=True)
    
    return None, raw_path


def convert_to_mp3(temp_path, raw_path):
    """
    임시 오디오 파일을 MP3로 변환합니다.
    """
    if not temp_path or not os.path.exists(temp_path):
        log.warning(f"  [Convert Skip] 변환할 임시 파일이 없습니다: {temp_path}")
        return None

    if os.path.exists(raw_path):
        log.info(f"  [Convert Skip] 최종 MP3 파일이 이미 존재합니다: {Path(raw_path).name}")
        # 변환이 이미 완료되었으므로 임시 파일 삭제
        os.remove(temp_path)
        log.debug(f"Cleaned up existing temp file: {temp_path}")
        return raw_path

    log.info(f"  [Convert] MP3로 변환 중: {Path(temp_path).name} -> {Path(raw_path).name}")
    try:
        ffmpeg_command = [
            'ffmpeg', '-y', '-i', temp_path,
            '-vn', '-ab', '192k', '-ar', str(config.SR), '-ac', '1',
            raw_path
        ]
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=180)
        log.info(f"  -> 변환 완료: {Path(raw_path).name}")
        return raw_path
    except FileNotFoundError:
        log.error("`ffmpeg` 실행 파일을 찾을 수 없습니다. PATH에 등록되었는지 확인하세요.", exc_info=True)
    except subprocess.TimeoutExpired as e:
        log.error(f"  [오류] FFmpeg 시간 초과 ({Path(temp_path).name}) | {e.stderr}", exc_info=True)
    except subprocess.CalledProcessError as e:
        log.error(f"  [오류] FFmpeg 실패 ({Path(temp_path).name}) | {e.stderr}", exc_info=True)
    except Exception as e:
        log.error(f"  [오류] 변환 중 알 수 없는 오류 ({Path(temp_path).name}) | {e}", exc_info=True)
    
    return None
    

def process_audio(raw_path, classifier, artist_name, url):
    """
    raw 오디오 파일에서 보컬을 분리하고 지문을 추출합니다.
    """
    vid = extract_video_id(url)
    if not raw_path or not os.path.exists(raw_path):
        log.error(f"  [Process Error] 원본 오디오 파일이 없습니다: {raw_path}")
        return

    artist_dir = os.path.join(config.DB_DIR, artist_name)
    vocal_path = os.path.join(artist_dir, f"vocal_{vid}.mp3")
    emb_path = os.path.join(artist_dir, f"emb_{vid}.pt")

    if os.path.exists(emb_path):
        log.info(f"  [Process Skip] 이미 추출된 지문이 존재합니다: {Path(emb_path).name}")
        return

    # 1. 보컬 분리 (Vocal Separation)
    if not os.path.exists(vocal_path):
        log.info(f"  [Process 1/2] 보컬 분리 중: {Path(raw_path).name}")
        demucs_output_dir = os.path.join(artist_dir, "demucs_separated")
        temp_raw_path = None
        try:
            temp_raw_path = raw_path + ".tmp"
            shutil.copy2(raw_path, temp_raw_path)
            demucs_args = ["--two-stems", "vocals", "--out", demucs_output_dir, "--mp3", temp_raw_path]
            demucs_main(demucs_args)

            separated_vocal_file = next(Path(demucs_output_dir).rglob("vocals.mp3"), None)
            if separated_vocal_file and separated_vocal_file.exists():
                shutil.move(str(separated_vocal_file), vocal_path)
                log.info(f"  -> 보컬 파일 저장 완료: {Path(vocal_path).name}")
            else:
                raise FileNotFoundError("Demucs에 의해 생성된 보컬 파일을 찾을 수 없습니다.")
            
            if config.CLEANUP_RAW_AUDIO:
                os.remove(raw_path)
                log.info(f"  -> 용량 확보: {Path(raw_path).name} 삭제 완료")
            else:
                log.info(f"  -> 원본 파일 보존: {Path(raw_path).name}")

        except Exception as e:
            log.error(f"  [오류] 음원 분리 실패 ({Path(raw_path).name}): {e}", exc_info=True)
            return
        finally:
            # 임시 파일 및 폴더 정리
            if temp_raw_path and os.path.exists(temp_raw_path):
                os.remove(temp_raw_path)
            if os.path.exists(demucs_output_dir):
                shutil.rmtree(demucs_output_dir)
            # 변환 후 남은 임시 원본 파일(webm, m4a 등)이 있다면 삭제
            temp_dir = os.path.join(artist_dir, "temp")
            temp_file_path = os.path.join(temp_dir, f"temp_{vid}")
            existing_temp_files = glob.glob(f"{temp_file_path}.*")
            for f in existing_temp_files:
                if os.path.exists(f):
                    os.remove(f)
                    log.debug(f"Cleaned up temp source file: {f}")

    else:
        log.info(f"  [Process 1/2 Skip] 분리된 보컬 오디오가 이미 존재합니다: {Path(vocal_path).name}")

    if not os.path.exists(vocal_path):
        log.error(f"  [오류] 분리된 보컬 파일을 찾을 수 없어 지문 추출을 진행할 수 없습니다.")
        return

    # 2. 지문 추출 (Fingerprint Extraction)
    log.info(f"  [Process 2/2] 지문 추출 및 최적화 진행 중: {Path(vocal_path).name}")
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
            log.warning(f"  [주의] 유효한 오디오 구간이 없습니다 ({Path(vocal_path).name}).")
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
        log.info(f"  -> 최종 지문 저장 완료: {Path(emb_path).name}")

    except Exception as e:
        log.error(f"  [오류] 지문 추출 실패 ({Path(vocal_path).name}): {e}", exc_info=True)
    finally:
        if config.DEVICE == "cuda":
            torch.cuda.empty_cache()