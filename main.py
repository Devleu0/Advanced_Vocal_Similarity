import config
from logger import log
from models import load_speech_brain_model
from pipeline import collect_tasks, run_pipeline
from utils import setup_korean_font


def main():
    """
    전체 보컬 유사도 분석 파이프라인을 CLI 로 실행합니다.
    단계 실행 순서는 `pipeline.run_pipeline` 에 정의되어 있습니다 (웹 UI 와 공용).
    """
    log.info("=" * 50)
    log.info(" End-to-End Vocal Similarity Pipeline Started")
    log.info("=" * 50)
    log.info(f"[*] 사용할 디바이스: {config.DEVICE}")
    setup_korean_font()

    tasks = collect_tasks(config.INPUT_DIR)
    if not tasks:
        log.warning("\n[!] 'inputs' 폴더에 처리할 .txt 파일 또는 URL 이 없습니다.")
        return

    classifier = load_speech_brain_model()
    run_pipeline(tasks, classifier)

    log.info("\n[*] 모든 파이프라인 처리가 완료되었습니다!")


if __name__ == "__main__":
    main()
