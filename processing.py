import os
import torch
import torchaudio
import config
import glob
import subprocess
from utils import extract_video_id
import cache
from fingerprint import (
    prepare_waveform, split_into_chunks, filter_silent_chunks, filter_by_speech_ratio,
    make_silero_ratio_fn, encode_chunks, aggregate_embeddings,
)
from embedding_store import embedding_path, chunk_cache_path
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
            'yt-dlp', '-f', config.DOWNLOAD_AUDIO_QUALITY,
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
        ffmpeg_command = ['ffmpeg', '-y', '-i', temp_path]
        if config.MAX_AUDIO_SEC:
            ffmpeg_command += ['-t', str(config.MAX_AUDIO_SEC)]
        ffmpeg_command += [
            '-vn', '-ab', config.MP3_BITRATE, '-ar', str(config.SR), '-ac', '1',
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
    

def separation_settings():
    """보컬 분리 결과에 영향을 주는 설정."""
    return {"demucs_model": config.DEMUCS_MODEL, "demucs_shifts": config.DEMUCS_SHIFTS}


def extraction_settings(model):
    """청크 임베딩(집계 이전)에 영향을 주는 설정."""
    return {
        "model": model, "sr": config.SR, "chunk_sec": config.CHUNK_SEC,
        "hop_sec": config.CHUNK_HOP_SEC, "use_vad": config.USE_VAD,
        "vad_backend": config.VAD_BACKEND, "vad_rms": config.VAD_RMS_THRESHOLD,
        "vad_relative": config.VAD_RELATIVE_RATIO,
        "silero_ratio": config.SILERO_MIN_SPEECH_RATIO, "separation": separation_settings(),
    }


def aggregation_settings(model):
    """최종 지문에 영향을 주는 설정 (추출 설정 + 집계 설정)."""
    return {
        **extraction_settings(model),
        "outlier_removal": config.USE_OUTLIER_REMOVAL, "top_k_ratio": config.EMB_TOP_K_RATIO,
        "multi_speaker": config.MULTI_SPEAKER_FILTER, "split_cos": config.MULTI_SPEAKER_SPLIT_COS,
    }


def _separate_vocals(raw_path, vocal_path, artist_dir, vid):
    """Demucs 로 보컬을 분리해 vocal_path 에 저장합니다. 성공 여부를 반환합니다."""
    log.info(f"  [Process 1/2] 보컬 분리 중: {Path(raw_path).name}")
    demucs_output_dir = os.path.join(artist_dir, "demucs_separated")
    temp_raw_path = None
    try:
        temp_raw_path = raw_path + ".tmp"
        shutil.copy2(raw_path, temp_raw_path)

        demucs_args = [
            "-n", config.DEMUCS_MODEL,
            "--two-stems", "vocals",
            "--out", demucs_output_dir,
            "--mp3",
        ]
        if config.DEMUCS_SHIFTS:
            demucs_args += ["--shifts", str(config.DEMUCS_SHIFTS)]
        demucs_args.append(temp_raw_path)
        log.info(f"  -> Demucs 모델: {config.DEMUCS_MODEL} (shifts={config.DEMUCS_SHIFTS})")
        demucs_main(demucs_args)

        separated_vocal_file = next(Path(demucs_output_dir).rglob("vocals.mp3"), None)
        if separated_vocal_file and separated_vocal_file.exists():
            shutil.move(str(separated_vocal_file), vocal_path)
            cache.write_meta(vocal_path, separation_settings())
            log.info(f"  -> 보컬 파일 저장 완료: {Path(vocal_path).name}")
        else:
            raise FileNotFoundError("Demucs에 의해 생성된 보컬 파일을 찾을 수 없습니다.")

        if config.CLEANUP_RAW_AUDIO:
            os.remove(raw_path)
            log.info(f"  -> 용량 확보: {Path(raw_path).name} 삭제 완료")
        else:
            log.info(f"  -> 원본 파일 보존: {Path(raw_path).name}")
        return True

    except Exception as e:
        log.error(f"  [오류] 음원 분리 실패 ({Path(raw_path).name}): {e}", exc_info=True)
        return False
    finally:
        # 임시 파일 및 폴더 정리
        if temp_raw_path and os.path.exists(temp_raw_path):
            os.remove(temp_raw_path)
        if os.path.exists(demucs_output_dir):
            shutil.rmtree(demucs_output_dir)
        # 변환 후 남은 임시 원본 파일(webm, m4a 등)이 있다면 삭제
        temp_file_path = os.path.join(artist_dir, "temp", f"temp_{vid}")
        for f in glob.glob(f"{temp_file_path}.*"):
            if os.path.exists(f):
                os.remove(f)
                log.debug(f"Cleaned up temp source file: {f}")


def _extract_chunk_embeddings(vocal_path, classifier):
    """보컬 파일 → VAD 를 통과한 청크들의 (N, D) 임베딩. 유효 구간이 없으면 None."""
    waveform, sr = torchaudio.load(vocal_path)
    waveform = prepare_waveform(waveform, sr, config.SR)
    chunks = split_into_chunks(
        waveform, config.SR, config.CHUNK_SEC, hop_sec=config.CHUNK_HOP_SEC
    )

    if config.USE_VAD:
        valid_chunks = filter_silent_chunks(
            chunks, config.VAD_RMS_THRESHOLD, config.VAD_RELATIVE_RATIO
        )
        if config.VAD_BACKEND == "silero" and valid_chunks:
            valid_chunks = filter_by_speech_ratio(
                valid_chunks, make_silero_ratio_fn(config.SR), config.SILERO_MIN_SPEECH_RATIO
            )
        log.info(f"  -> VAD({config.VAD_BACKEND}) 적용 후 청크 수: {len(chunks)} -> {len(valid_chunks)}")
    else:
        valid_chunks = chunks
        log.info("  -> VAD 비활성화, 모든 청크 사용")

    if not valid_chunks:
        return None
    return encode_chunks(valid_chunks, classifier, config.DEVICE, config.ENCODE_BATCH_SIZE)


def process_audio(raw_path, classifier, artist_name, url, model=None):
    """
    raw 오디오에서 보컬을 분리하고 지문을 추출합니다.

    단계별 산출물은 생성 설정과 함께 저장되어(cache.py), 설정이 같으면 재사용하고
    바뀌었으면 해당 단계부터 다시 만듭니다.
    """
    model = model or config.EMBEDDING_MODEL
    vid = extract_video_id(url)
    if not raw_path or not os.path.exists(raw_path):
        log.error(f"  [Process Error] 원본 오디오 파일이 없습니다: {raw_path}")
        return

    artist_dir = os.path.join(config.DB_DIR, artist_name)
    vocal_path = os.path.join(artist_dir, f"vocal_{vid}.mp3")
    emb_path = embedding_path(artist_dir, vid, model)
    chunks_path = chunk_cache_path(artist_dir, vid, model)

    if cache.is_fresh(emb_path, aggregation_settings(model)):
        log.info(f"  [Process Skip] 설정이 같은 지문이 이미 존재합니다: {Path(emb_path).name}")
        return

    # 1. 보컬 분리 (이전 버전이 만든 메타 없는 파일은 재사용)
    if cache.is_fresh(vocal_path, separation_settings(), allow_legacy=True):
        log.info(f"  [Process 1/2 Skip] 분리된 보컬 오디오 재사용: {Path(vocal_path).name}")
    elif not _separate_vocals(raw_path, vocal_path, artist_dir, vid):
        return

    if not os.path.exists(vocal_path):
        log.error("  [오류] 분리된 보컬 파일을 찾을 수 없어 지문 추출을 진행할 수 없습니다.")
        return

    # 2. 청크 임베딩 (모델 추론: 무거움 → 캐시) → 집계 (가벼움)
    log.info(f"  [Process 2/2] 지문 추출 진행 중 ({model}): {Path(vocal_path).name}")
    try:
        extraction = extraction_settings(model)
        if cache.is_fresh(chunks_path, extraction):
            embs_tensor = torch.load(chunks_path, weights_only=True)
            log.info(f"  -> 청크 임베딩 캐시 사용: {Path(chunks_path).name}")
        else:
            embs_tensor = _extract_chunk_embeddings(vocal_path, classifier)
            if embs_tensor is None:
                log.warning(f"  [주의] 유효한 오디오 구간이 없습니다 ({Path(vocal_path).name}).")
                return
            torch.save(embs_tensor, chunks_path)
            cache.write_meta(chunks_path, extraction)

        final_embedding, kept = aggregate_embeddings(
            embs_tensor, config.USE_OUTLIER_REMOVAL, config.EMB_TOP_K_RATIO,
            config.MULTI_SPEAKER_FILTER, config.MULTI_SPEAKER_SPLIT_COS,
        )
        log.info(f"  -> 임베딩 집계: {kept}/{len(embs_tensor)}개 사용")

        torch.save(final_embedding, emb_path)
        cache.write_meta(emb_path, aggregation_settings(model))
        log.info(f"  -> 최종 지문 저장 완료: {Path(emb_path).name}")

    except Exception as e:
        log.error(f"  [오류] 지문 추출 실패 ({Path(vocal_path).name}): {e}", exc_info=True)
    finally:
        if str(config.DEVICE).startswith("cuda"):
            torch.cuda.empty_cache()
