import glob
import os
from concurrent.futures import ThreadPoolExecutor

import cli
import config
from logger import log
from models import EMBEDDING_MODELS, format_model_list, load_embedding_model
from processing import convert_to_mp3, download_original_audio, process_audio
from utils import setup_korean_font
from visualization import generate_and_visualize_similarity


def configure(argv=None):
    """인자를 해석해 config 를 덮어쓰고 (models, args) 를 반환합니다. 목록 출력 옵션이면 models=None."""
    args = cli.build_parser(EMBEDDING_MODELS.keys()).parse_args(argv)
    if args.list_models:
        print(format_model_list())
        return None, args
    if args.list_presets:
        print(cli.format_presets())
        return None, args
    overrides = cli.build_overrides(args.preset, cli.explicit_from_args(args), args.set_pairs)
    cli.apply_overrides(config, overrides)
    cli.validate(config, list(EMBEDDING_MODELS))
    os.makedirs(config.INPUT_DIR, exist_ok=True)
    os.makedirs(config.DB_DIR, exist_ok=True)
    return list(config.ENSEMBLE_MODELS or [config.EMBEDDING_MODEL]), args


def collect_tasks():
    tasks = []
    for txt_file in glob.glob(os.path.join(config.INPUT_DIR, "*.txt")):
        artist_name = os.path.splitext(os.path.basename(txt_file))[0]
        with open(txt_file, 'r', encoding='utf-8') as f:
            for url in (line.strip() for line in f if line.strip()):
                tasks.append({'artist_name': artist_name, 'url': url, 'temp_path': None, 'raw_path': None})
    return tasks


def banner(title):
    log.info("\n" + "=" * 50)
    log.info(f" {title}")
    log.info("=" * 50)


def main(argv=None):
    """
    전체 보컬 유사도 분석 파이프라인을 실행합니다.
    다운로드, 변환, 처리를 단계별로 분리하여 실행합니다.
    """
    models, args = configure(argv)
    if models is None:
        return

    banner("End-to-End Vocal Similarity Pipeline Started")
    log.info(f"[*] 사용할 디바이스: {config.DEVICE}")
    log.info(f"[*] 임베딩 모델: {models} | preset={args.preset or 'custom'}")
    setup_korean_font()

    # 모델 로드 (앙상블이면 여러 개)
    classifiers = {m: load_embedding_model(m) for m in models}

    tasks = collect_tasks()
    if not tasks:
        log.warning("\n[!] 'inputs' 폴더에 처리할 URL(.txt)이 없습니다.")
        return

    banner("STAGE 1a: BATCH ORIGINAL AUDIO DOWNLOAD (yt-dlp)")

    def _download(task):
        task['temp_path'], task['raw_path'] = download_original_audio(task['url'], task['artist_name'])

    with ThreadPoolExecutor(max_workers=config.DOWNLOAD_WORKERS) as pool:
        list(pool.map(_download, tasks))

    banner("STAGE 1b: BATCH MP3 CONVERSION (ffmpeg)")
    for i, task in enumerate(tasks):
        log.info(f"\n>> [{i+1}/{len(tasks)}] Artist: {task['artist_name']}")
        if not convert_to_mp3(task['temp_path'], task['raw_path']):
            task['raw_path'] = None  # 변환 실패 시 다음 단계 건너뜀

    banner("STAGE 2: BATCH AUDIO PROCESSING")
    for i, task in enumerate(tasks):
        log.info(f"\n>> [{i+1}/{len(tasks)}] Artist: {task['artist_name']}")
        if task['raw_path'] and os.path.exists(task['raw_path']):
            for m in models:
                process_audio(task['raw_path'], classifiers[m], task['artist_name'], task['url'], model=m)
        else:
            log.warning(f"  [Process Skip] 이전 단계에서 실패했거나 건너뛴 항목입니다: {task['url']}")

    banner("STAGE 3: FINAL ANALYSIS & VISUALIZATION")
    generate_and_visualize_similarity(models)

    log.info("\n[*] 모든 파이프라인 처리가 완료되었습니다!")


if __name__ == "__main__":
    main()
