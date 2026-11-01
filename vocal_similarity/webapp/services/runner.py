"""JobManager 에 주입되는 실제 파이프라인 runner.

SpeechBrain 모델은 첫 작업에서 한 번만 로드하고 이후 작업에서 재사용합니다.
무거운 모듈(torch, speechbrain, demucs)은 작업 실행 시점에 import 하므로
웹 서버 기동과 API 테스트는 이들 없이도 가볍게 동작합니다.
"""
from __future__ import annotations

import threading
from typing import List, Optional

from .jobs import CancelCheck, JobCancelled, ProgressCallback

STAGE_MODEL = "model"


class PipelineRunner:
    def __init__(self):
        self._classifier = None
        self._lock = threading.Lock()

    def _get_classifier(self):
        with self._lock:
            if self._classifier is None:
                from ...models import load_speech_brain_model
                self._classifier = load_speech_brain_model()
            return self._classifier

    def __call__(self, artists: Optional[List[str]],
                 on_progress: ProgressCallback, should_cancel: CancelCheck) -> None:
        from ... import config
        from ...logger import log
        from ...pipeline import PipelineCancelled, collect_tasks, run_pipeline
        from ...utils import setup_korean_font

        tasks = collect_tasks(config.INPUT_DIR, artists)
        if not tasks:
            raise ValueError("처리할 URL 이 없습니다. 아티스트와 URL 을 먼저 등록하세요.")

        log.info(f"[*] 작업 대상: {len(tasks)}개 URL / 디바이스: {config.DEVICE}")
        setup_korean_font()

        on_progress(STAGE_MODEL, 0, 1)
        classifier = self._get_classifier()
        on_progress(STAGE_MODEL, 1, 1)

        try:
            run_pipeline(tasks, classifier, on_progress=on_progress, should_cancel=should_cancel)
        except PipelineCancelled as e:
            raise JobCancelled() from e
        log.info("\n[*] 모든 파이프라인 처리가 완료되었습니다!")
