from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from webapp.dependencies import get_job_manager
from webapp.schemas import JobCreate, JobOut
from webapp.services.jobs import JobBusyError, JobManager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobOut])
def list_jobs(jobs: JobManager = Depends(get_job_manager)):
    return [JobOut.from_domain(j) for j in jobs.list()]


@router.post("", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_job(body: Optional[JobCreate] = None, jobs: JobManager = Depends(get_job_manager)):
    """분석 작업을 시작합니다. 동시에 하나의 작업만 실행되며, 실행 중이면 409 를 반환합니다."""
    try:
        job = jobs.submit(body.artists if body else None)
    except JobBusyError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, {"message": str(e), "active_job_id": e.active_job_id})
    return JobOut.from_domain(job, log_offset=0)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, log_offset: int = 0, jobs: JobManager = Depends(get_job_manager)):
    """작업 상태와 log_offset 이후의 로그를 반환합니다 (응답의 next_log_offset 으로 이어서 조회)."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "작업을 찾을 수 없습니다.")
    return JobOut.from_domain(job, log_offset=log_offset)


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, jobs: JobManager = Depends(get_job_manager)):
    """취소를 요청합니다. 현재 처리 중인 URL 이 끝난 뒤 중단됩니다."""
    job = jobs.cancel(job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "작업을 찾을 수 없습니다.")
    return JobOut.from_domain(job)
