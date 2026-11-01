"""FastAPI 애플리케이션 팩토리."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from webapp.routers import artists, jobs, results
from webapp.services.artists import ArtistService
from webapp.services.jobs import JobManager, Runner
from webapp.services.results import ResultService

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def create_app(runner: Optional[Runner] = None) -> FastAPI:
    """앱을 생성합니다. runner 를 주입하면 실제 파이프라인 대신 사용합니다 (테스트/데모용)."""
    if runner is None:
        from webapp.services.runner import PipelineRunner
        runner = PipelineRunner()

    app = FastAPI(title="Advanced Vocal Similarity", version="1.0.0")
    app.state.artist_service = ArtistService()
    app.state.job_manager = JobManager(runner)
    app.state.result_service = ResultService()

    app.include_router(artists.router)
    app.include_router(jobs.router)
    app.include_router(results.router)

    @app.get("/api/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    # API 라우트를 먼저 등록한 뒤 나머지 경로를 정적 프런트엔드로 제공합니다.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app
