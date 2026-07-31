import logging
import os
from logging.handlers import RotatingFileHandler
import config

LOG_FILE = os.path.join(config.BASE_DIR, 'pipeline.log')

def setup_logger():
    """
    콘솔과 파일에 모두 로그를 남기는 로거를 설정합니다.
    - 콘솔: INFO 레벨 이상, 간단한 포맷
    - 파일: DEBUG 레벨 이상, 상세한 포맷, 5MB마다 파일 교체
    """
    logger = logging.getLogger("VocalSimilarityPipeline")
    if logger.hasHandlers():
        return logger # 이미 설정된 경우 중복 방지

    logger.setLevel(logging.DEBUG)

    # 포맷터 설정
    console_formatter = logging.Formatter('%(message)s')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 설정 (Rotating)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# 전역 로거 인스턴스
log = setup_logger()
