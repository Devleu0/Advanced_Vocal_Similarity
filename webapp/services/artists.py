"""아티스트(입력 URL 목록) 관리 서비스.

파일 포맷은 `input_store`, 처리 산출물 경로 규칙은 `processing.py` 와 동일한
`database/<아티스트>/{raw,vocal,emb}_<vid>.*` 를 따릅니다.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from typing import List, Optional

import config
import input_store
from utils import extract_video_id, is_youtube_url

# URL 별 처리 상태 (진행 순서대로)
STATUS_INVALID = "invalid"      # 유튜브 URL 형식 아님
STATUS_PENDING = "pending"      # 아직 처리 전
STATUS_DOWNLOADED = "downloaded"  # raw mp3 존재
STATUS_SEPARATED = "separated"  # 보컬 분리 완료
STATUS_DONE = "done"            # 지문(임베딩) 추출 완료


class InvalidUrls(ValueError):
    def __init__(self, urls: List[str]):
        super().__init__("유튜브 URL 형식이 아닙니다: " + ", ".join(urls))
        self.urls = urls


@dataclass
class UrlStatus:
    url: str
    video_id: Optional[str]
    status: str


@dataclass
class Artist:
    name: str
    urls: List[UrlStatus] = field(default_factory=list)

    @property
    def embeddings(self) -> int:
        return sum(1 for u in self.urls if u.status == STATUS_DONE)


def url_status(artist_name: str, url: str, db_dir: Optional[str] = None) -> UrlStatus:
    if not is_youtube_url(url):
        return UrlStatus(url, None, STATUS_INVALID)
    vid = extract_video_id(url)
    artist_dir = os.path.join(db_dir or config.DB_DIR, artist_name)

    def exists(name: str) -> bool:
        return os.path.exists(os.path.join(artist_dir, name))

    if exists(f"emb_{vid}.pt"):
        status = STATUS_DONE
    elif exists(f"vocal_{vid}.mp3"):
        status = STATUS_SEPARATED
    elif exists(f"raw_{vid}.mp3"):
        status = STATUS_DOWNLOADED
    else:
        status = STATUS_PENDING
    return UrlStatus(url, vid, status)


class ArtistService:
    """입력 폴더/DB 폴더 경로는 호출 시점의 config 값을 사용합니다 (테스트에서 교체 가능)."""

    def list(self) -> List[Artist]:
        return [
            Artist(name, [url_status(name, u) for u in urls])
            for name, urls in input_store.list_artists(config.INPUT_DIR).items()
        ]

    def get(self, name: str) -> Optional[Artist]:
        name = input_store.validate_artist_name(name)
        return next((a for a in self.list() if a.name == name), None)

    def save(self, name: str, urls: List[str]) -> Artist:
        name = input_store.validate_artist_name(name)
        cleaned = list(dict.fromkeys(u.strip() for u in urls if u and u.strip()))  # 순서 유지 중복 제거
        invalid = [u for u in cleaned if not is_youtube_url(u)]
        if invalid:
            raise InvalidUrls(invalid)
        input_store.write_urls(config.INPUT_DIR, name, cleaned)
        return Artist(name, [url_status(name, u) for u in cleaned])

    def delete(self, name: str, purge_data: bool = False) -> bool:
        name = input_store.validate_artist_name(name)
        removed = input_store.delete_artist(config.INPUT_DIR, name)
        if purge_data:
            artist_dir = os.path.join(config.DB_DIR, name)
            if os.path.isdir(artist_dir):
                shutil.rmtree(artist_dir)
                removed = True
        return removed
