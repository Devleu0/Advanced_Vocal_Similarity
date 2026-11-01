"""파이프라인 오케스트레이션 (CLI·웹 UI 공용).

단계 실행 순서만 책임지며, 실제 I/O 는 `processing.py`, 분석/시각화는
`visualization.py` 에 위임합니다. 진행 상황 콜백(`on_progress`)과 취소 함수
(`should_cancel`)를 받을 수 있어 웹 UI 등 다른 프런트엔드에서 재사용할 수 있습니다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

import config
from input_store import list_artists
from logger import log
from processing import convert_to_mp3, download_original_audio, process_audio
from visualization import generate_and_visualize_similarity

# 단계 식별자 (진행 콜백의 stage 값). UI 는 이 값으로 단계 이름을 표시합니다.
STAGE_DOWNLOAD = "download"
STAGE_CONVERT = "convert"
STAGE_PROCESS = "process"
STAGE_ANALYZE = "analyze"
STAGES = (STAGE_DOWNLOAD, STAGE_CONVERT, STAGE_PROCESS, STAGE_ANALYZE)

ProgressCallback = Callable[[str, int, int], None]
CancelCheck = Callable[[], bool]


class PipelineCancelled(Exception):
    """사용자 요청으로 파이프라인이 중단됨."""


@dataclass
class Task:
    artist_name: str
    url: str
    temp_path: Optional[str] = None
    raw_path: Optional[str] = None


def collect_tasks(input_dir: Optional[str] = None,
                  artists: Optional[Iterable[str]] = None) -> List[Task]:
    """입력 폴더의 `<아티스트>.txt` 들로부터 작업 목록을 만듭니다.

    artists 가 주어지면 해당 아티스트만 포함합니다.
    """
    input_dir = input_dir or config.INPUT_DIR
    selected = set(artists) if artists else None
    tasks: List[Task] = []
    for artist_name, urls in list_artists(input_dir).items():
        if selected is not None and artist_name not in selected:
            continue
        tasks.extend(Task(artist_name=artist_name, url=url) for url in urls)
    return tasks


def _banner(title: str) -> None:
    log.info("\n" + "=" * 50)
    log.info(f" {title}")
    log.info("=" * 50)


def run_pipeline(tasks: List[Task], classifier,
                 on_progress: Optional[ProgressCallback] = None,
                 should_cancel: Optional[CancelCheck] = None) -> None:
    """다운로드 → 변환 → 보컬 분리/지문 추출 → 분석/시각화 를 순서대로 실행합니다."""
    report = on_progress or (lambda stage, current, total: None)
    cancelled = should_cancel or (lambda: False)
    total = len(tasks)

    def each(stage: str, title: str, step: Callable[[Task], None]) -> None:
        _banner(title)
        report(stage, 0, total)
        for i, task in enumerate(tasks):
            if cancelled():
                raise PipelineCancelled()
            log.info(f"\n>> [{i + 1}/{total}] Artist: {task.artist_name}")
            step(task)
            report(stage, i + 1, total)

    def download(task: Task) -> None:
        task.temp_path, task.raw_path = download_original_audio(task.url, task.artist_name)

    def convert(task: Task) -> None:
        # 이전 실행에서 이미 변환된 MP3 가 있으면(다운로드 단계가 temp 없이 raw 만 반환) 그대로 사용
        if not task.temp_path and task.raw_path and os.path.exists(task.raw_path):
            log.info(f"  [Convert Skip] 최종 MP3 파일이 이미 존재합니다: {os.path.basename(task.raw_path)}")
            return
        # 변환 실패 시 raw_path 를 None 으로 설정하여 다음 단계를 건너뛰게 함
        if not convert_to_mp3(task.temp_path, task.raw_path):
            task.raw_path = None

    def process(task: Task) -> None:
        if task.raw_path and os.path.exists(task.raw_path):
            process_audio(task.raw_path, classifier, task.artist_name, task.url)
        else:
            log.warning(f"  [Process Skip] 이전 단계에서 실패했거나 건너뛴 항목입니다: {task.url}")

    each(STAGE_DOWNLOAD, "STAGE 1a: BATCH ORIGINAL AUDIO DOWNLOAD (yt-dlp)", download)
    each(STAGE_CONVERT, "STAGE 1b: BATCH MP3 CONVERSION (ffmpeg)", convert)
    each(STAGE_PROCESS, "STAGE 2: BATCH AUDIO PROCESSING", process)

    if cancelled():
        raise PipelineCancelled()
    _banner("STAGE 3: FINAL ANALYSIS & VISUALIZATION")
    report(STAGE_ANALYZE, 0, 1)
    generate_and_visualize_similarity()
    report(STAGE_ANALYZE, 1, 1)
