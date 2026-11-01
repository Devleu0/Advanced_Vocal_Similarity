"""FastAPI 의존성: 서비스 인스턴스는 `app.state` 에 보관되어 테스트에서 쉽게 교체됩니다."""
from fastapi import Request

from .services.artists import ArtistService
from .services.jobs import JobManager
from .services.results import ResultService


def get_artist_service(request: Request) -> ArtistService:
    return request.app.state.artist_service


def get_job_manager(request: Request) -> JobManager:
    return request.app.state.job_manager


def get_result_service(request: Request) -> ResultService:
    return request.app.state.result_service
