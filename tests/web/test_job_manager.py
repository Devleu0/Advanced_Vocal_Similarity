import threading

import pytest

from vocal_similarity.logger import log
from vocal_similarity.webapp.services.jobs import (
    JobBusyError,
    JobCancelled,
    JobManager,
    JobStatus,
)


def test_successful_job_collects_progress_and_logs():
    def runner(artists, on_progress, should_cancel):
        log.info(f"hello {artists}")
        on_progress("download", 1, 2)

    jm = JobManager(runner)
    job = jm.wait(jm.submit(["A"]).id)

    assert job.status is JobStatus.SUCCEEDED
    assert (job.stage, job.current, job.total) == ("download", 1, 2)
    lines, next_offset = job.logs_since(0)
    assert "hello ['A']" in lines
    assert next_offset == len(lines)
    assert job.logs_since(next_offset)[0] == []


def test_failed_job_records_error():
    def runner(*_):
        log.error("download failed")
        raise ValueError("boom")

    jm = JobManager(runner)
    job = jm.wait(jm.submit().id)
    assert job.status is JobStatus.FAILED
    assert "boom" in job.error
    assert list(job.failure_logs)[:2] == [
        "download failed",
        "[!] 작업 실패: ValueError: boom",
    ]


def test_only_one_active_job_and_cancel():
    started, release = threading.Event(), threading.Event()

    def runner(artists, on_progress, should_cancel):
        started.set()
        release.wait(5)
        if should_cancel():
            raise JobCancelled()

    jm = JobManager(runner)
    job = jm.submit()
    started.wait(5)
    with pytest.raises(JobBusyError):
        jm.submit()

    jm.cancel(job.id)
    release.set()
    assert jm.wait(job.id).status is JobStatus.CANCELLED
    # 끝난 뒤에는 새 작업을 받을 수 있음
    assert jm.wait(jm.submit().id).status is JobStatus.SUCCEEDED


def test_log_buffer_is_bounded_and_offsets_stay_consistent():
    def runner(*_):
        for i in range(10):
            log.info(f"line {i}")

    jm = JobManager(runner, max_log_lines=3)
    job = jm.wait(jm.submit().id)
    lines, next_offset = job.logs_since(0)
    assert lines == ["line 7", "line 8", "line 9"]
    assert next_offset == 10
    assert job.logs_since(9)[0] == ["line 9"]


def test_logs_from_other_threads_are_ignored():
    def runner(*_):
        t = threading.Thread(target=lambda: log.info("other thread"))
        t.start()
        t.join()
        log.info("job thread")

    jm = JobManager(runner)
    job = jm.wait(jm.submit().id)
    assert job.logs_since(0)[0] == ["job thread"]
