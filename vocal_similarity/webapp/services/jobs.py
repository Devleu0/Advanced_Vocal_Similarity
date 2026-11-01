"""백그라운드 분석 작업 관리.

파이프라인은 GPU/디스크를 독점하고 같은 산출물 파일을 다루므로 **동시에 하나의 작업만**
실행합니다. 실제 실행 로직은 생성자에 주입되는 `runner` 가 담당하므로 테스트에서는
가짜 runner 를 넣어 HTTP·상태 전이를 검증할 수 있습니다.
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Deque, Dict, List, Optional

LOGGER_NAME = "VocalSimilarityPipeline"

ProgressCallback = Callable[[str, int, int], None]
CancelCheck = Callable[[], bool]
# runner(artists, on_progress, should_cancel) - 취소되면 JobCancelled 를 던집니다
Runner = Callable[[Optional[List[str]], ProgressCallback, CancelCheck], None]


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_active(self) -> bool:
        return self in (JobStatus.QUEUED, JobStatus.RUNNING)


class JobBusyError(RuntimeError):
    """이미 실행 중인 작업이 있음."""

    def __init__(self, active_job_id: str):
        super().__init__(f"이미 실행 중인 작업이 있습니다: {active_job_id}")
        self.active_job_id = active_job_id


class JobCancelled(Exception):
    """runner 가 취소를 알릴 때 사용할 수 있는 예외."""


@dataclass
class Job:
    id: str
    artists: Optional[List[str]]
    status: JobStatus = JobStatus.QUEUED
    stage: Optional[str] = None
    current: int = 0
    total: int = 0
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    log_lines: Deque[str] = field(default_factory=deque)
    log_offset: int = 0  # log_lines[0] 의 전역 줄 번호 (오래된 줄이 잘려도 증분 조회 가능)
    failure_logs: Deque[str] = field(default_factory=deque)
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _log_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def append_log(self, line: str, max_lines: int, is_failure: bool = False) -> None:
        with self._log_lock:
            self.log_lines.append(line)
            if len(self.log_lines) > max_lines:
                self.log_lines.popleft()
                self.log_offset += 1
            if is_failure:
                self.failure_logs.append(line)
                if len(self.failure_logs) > max_lines:
                    self.failure_logs.popleft()

    def logs_since(self, offset: int):
        """(offset 이후의 로그 줄들, 다음 조회에 쓸 offset) 을 반환합니다."""
        with self._log_lock:
            start = max(offset - self.log_offset, 0)
            lines = list(self.log_lines)[start:]
            return lines, self.log_offset + len(self.log_lines)


class _JobLogHandler(logging.Handler):
    """작업 스레드에서 발생한 파이프라인 로그만 해당 Job 에 수집합니다."""

    def __init__(self, job: Job, thread_id: int, max_lines: int):
        super().__init__(level=logging.INFO)
        self.job = job
        self.thread_id = thread_id
        self.max_lines = max_lines
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        if record.thread != self.thread_id:
            return
        for line in self.format(record).splitlines() or [""]:
            self.job.append_log(
                line,
                self.max_lines,
                is_failure=record.levelno >= logging.ERROR,
            )


class JobManager:
    def __init__(self, runner: Runner, max_log_lines: int = 5000, history_limit: int = 20):
        self._runner = runner
        self._max_log_lines = max_log_lines
        self._history_limit = history_limit
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    # ---- 조회 ----
    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def list(self) -> List[Job]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def active(self) -> Optional[Job]:
        return next((j for j in self._jobs.values() if j.status.is_active), None)

    # ---- 제어 ----
    def submit(self, artists: Optional[List[str]] = None) -> Job:
        with self._lock:
            running = self.active()
            if running:
                raise JobBusyError(running.id)
            job = Job(id=uuid.uuid4().hex[:12], artists=artists or None)
            self._jobs[job.id] = job
            self._trim_history()
        thread = threading.Thread(target=self._run, args=(job,), name=f"job-{job.id}", daemon=True)
        thread.start()
        return job

    def cancel(self, job_id: str) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if job and job.status.is_active:
            job.cancel_event.set()
        return job

    def wait(self, job_id: str, timeout: float = 10.0) -> Optional[Job]:
        """작업이 끝날 때까지 대기 (테스트·스크립트용)."""
        deadline = time.time() + timeout
        job = self._jobs.get(job_id)
        while job and job.status.is_active and time.time() < deadline:
            time.sleep(0.02)
        return job

    # ---- 내부 ----
    def _trim_history(self) -> None:
        finished = [j for j in self.list() if not j.status.is_active]
        for old in finished[self._history_limit:]:
            self._jobs.pop(old.id, None)

    def _run(self, job: Job) -> None:
        logger = logging.getLogger(LOGGER_NAME)
        handler = _JobLogHandler(job, threading.get_ident(), self._max_log_lines)
        logger.addHandler(handler)

        def on_progress(stage: str, current: int, total: int) -> None:
            job.stage, job.current, job.total = stage, current, total

        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        try:
            self._runner(job.artists, on_progress, job.cancel_event.is_set)
            job.status = JobStatus.SUCCEEDED
        except JobCancelled:
            job.status = JobStatus.CANCELLED
            logger.info("[!] 사용자 요청으로 작업이 취소되었습니다.")
        except Exception as e:  # noqa: BLE001 - 작업 실패는 상태로 보고
            if job.cancel_event.is_set():
                job.status = JobStatus.CANCELLED
            else:
                job.status = JobStatus.FAILED
                job.error = f"{type(e).__name__}: {e}"
                logger.error(f"[!] 작업 실패: {job.error}", exc_info=True)
        finally:
            job.finished_at = time.time()
            logger.removeHandler(handler)
