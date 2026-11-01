import os
import glob
import config
from utils import setup_korean_font
from models import load_speech_brain_model
from processing import download_original_audio, convert_to_mp3, process_audio
from visualization import generate_and_visualize_similarity
from logger import log

def main():
    """
    전체 보컬 유사도 분석 파이프라인을 실행합니다.
    다운로드, 변환, 처리를 단계별로 분리하여 실행합니다.
    """
    # 1. 초기 설정
    log.info("="*50)
    log.info(" End-to-End Vocal Similarity Pipeline Started")
    log.info("="*50)
    log.info(f"[*] 사용할 디바이스: {config.DEVICE}")
    setup_korean_font()

    # 2. 모델 로드
    classifier = load_speech_brain_model()

    # 3. 모든 입력 파일에서 처리할 작업 목록 수집
    txt_files = glob.glob(os.path.join(config.INPUT_DIR, "*.txt"))
    if not txt_files:
        log.warning("\n[!] 'inputs' 폴더에 처리할 .txt 파일이 없습니다.")
        return

    tasks = []
    for txt_file in txt_files:
        artist_name = os.path.splitext(os.path.basename(txt_file))[0]
        with open(txt_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
            for url in urls:
                tasks.append({'artist_name': artist_name, 'url': url, 'temp_path': None, 'raw_path': None})

    if not tasks:
        log.warning("\n[!] 'inputs' 폴더의 .txt 파일 내에 처리할 URL이 없습니다.")
        return

    # 4. 단계 1a: 모든 원본 오디오 일괄 다운로드 (yt-dlp)
    log.info("\n" + "="*50)
    log.info(" STAGE 1a: BATCH ORIGINAL AUDIO DOWNLOAD (yt-dlp)")
    log.info("="*50)
    for i, task in enumerate(tasks):
        log.info(f"\n>> [{i+1}/{len(tasks)}] Artist: {task['artist_name']}")
        temp_path, raw_path = download_original_audio(task['url'], task['artist_name'])
        task['temp_path'] = temp_path
        task['raw_path'] = raw_path

    # 5. 단계 1b: 모든 오디오 일괄 변환 (ffmpeg)
    log.info("\n" + "="*50)
    log.info(" STAGE 1b: BATCH MP3 CONVERSION (ffmpeg)")
    log.info("="*50)
    for i, task in enumerate(tasks):
        log.info(f"\n>> [{i+1}/{len(tasks)}] Artist: {task['artist_name']}")
        final_raw_path = convert_to_mp3(task['temp_path'], task['raw_path'])
        # 변환 실패 시 raw_path를 None으로 설정하여 다음 단계 건너뛰게 함
        if not final_raw_path:
            task['raw_path'] = None

    # 6. 단계 2: 모든 오디오 처리 (보컬 분리 및 지문 추출)
    log.info("\n" + "="*50)
    log.info(" STAGE 2: BATCH AUDIO PROCESSING")
    log.info("="*50)
    for i, task in enumerate(tasks):
        log.info(f"\n>> [{i+1}/{len(tasks)}] Artist: {task['artist_name']}")
        if task['raw_path'] and os.path.exists(task['raw_path']):
            process_audio(task['raw_path'], classifier, task['artist_name'], task['url'])
        else:
            log.warning(f"  [Process Skip] 이전 단계에서 실패했거나 건너뛴 항목입니다: {task['url']}")

    # 7. 단계 3: 최종 분석 및 시각화
    log.info("\n" + "="*50)
    log.info(" STAGE 3: FINAL ANALYSIS & VISUALIZATION")
    log.info("="*50)
    generate_and_visualize_similarity()

    log.info("\n[*] 모든 파이프라인 처리가 완료되었습니다!")

if __name__ == "__main__":
    main()
