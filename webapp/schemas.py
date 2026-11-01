"""HTTP API 요청/응답 스키마 (서비스 계층의 dataclass ↔ JSON 변환)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from webapp.services.artists import Artist
from webapp.services.jobs import Job


class UrlStatusOut(BaseModel):
    url: str
    video_id: Optional[str]
    status: str


class ArtistOut(BaseModel):
    name: str
    urls: List[UrlStatusOut]
    embeddings: int

    @classmethod
    def from_domain(cls, artist: Artist) -> "ArtistOut":
        return cls(
            name=artist.name,
            urls=[UrlStatusOut(url=u.url, video_id=u.video_id, status=u.status) for u in artist.urls],
            embeddings=artist.embeddings,
        )


class ArtistIn(BaseModel):
    urls: List[str] = Field(default_factory=list, description="유튜브 URL 목록")


class JobCreate(BaseModel):
    artists: Optional[List[str]] = Field(default=None, description="대상 아티스트 (생략 시 전체)")


class JobOut(BaseModel):
    id: str
    artists: Optional[List[str]]
    status: str
    stage: Optional[str]
    current: int
    total: int
    error: Optional[str]
    created_at: float
    started_at: Optional[float]
    finished_at: Optional[float]
    logs: List[str] = Field(default_factory=list)
    next_log_offset: int = 0

    @classmethod
    def from_domain(cls, job: Job, log_offset: Optional[int] = None) -> "JobOut":
        logs, next_offset = job.logs_since(log_offset) if log_offset is not None else ([], 0)
        return cls(
            id=job.id, artists=job.artists, status=job.status.value, stage=job.stage,
            current=job.current, total=job.total, error=job.error,
            created_at=job.created_at, started_at=job.started_at, finished_at=job.finished_at,
            logs=logs, next_log_offset=next_offset,
        )


class SimilarityOut(BaseModel):
    artists: List[str]
    matrix: List[List[float]]
    clustermap_available: bool = False
