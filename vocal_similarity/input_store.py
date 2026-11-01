"""입력(`inputs/<아티스트>.txt`) 파일 포맷을 다루는 모듈.

CLI(`main.py`)와 웹 UI(`webapp`)가 같은 규칙으로 입력을 읽고 쓰도록
파일 포맷·이름 검증 로직을 이 모듈 한 곳에 모읍니다.
무거운 의존성(torch 등)이 없으므로 어디서든 가볍게 import 할 수 있습니다.
"""
from __future__ import annotations

import os
import re
from typing import Dict, List

INPUT_EXT = ".txt"

# 한글/영문/숫자/밑줄/하이픈/공백/마침표 허용, 경로 구분자 및 선행 마침표 금지 (경로 조작 방지)
_ARTIST_NAME_RE = re.compile(r"^(?!\.)[\w\-. ]{1,64}$")


class InvalidArtistName(ValueError):
    """허용되지 않는 아티스트 이름."""


def validate_artist_name(name: str) -> str:
    """아티스트 이름을 검증하고 앞뒤 공백을 제거한 값을 반환합니다."""
    cleaned = (name or "").strip()
    if not _ARTIST_NAME_RE.match(cleaned) or cleaned in (".", ".."):
        raise InvalidArtistName(
            f"아티스트 이름이 올바르지 않습니다: {name!r} "
            "(한글/영문/숫자/공백/-/_/. 만 사용, 최대 64자)"
        )
    return cleaned


def artist_file_path(input_dir: str, artist_name: str) -> str:
    return os.path.join(input_dir, validate_artist_name(artist_name) + INPUT_EXT)


def read_urls(path: str) -> List[str]:
    """URL 파일에서 비어 있지 않은 줄을 순서대로 읽습니다."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def list_artists(input_dir: str) -> Dict[str, List[str]]:
    """{아티스트 이름: URL 목록} 을 이름순으로 반환합니다."""
    if not os.path.isdir(input_dir):
        return {}
    result: Dict[str, List[str]] = {}
    for filename in sorted(os.listdir(input_dir)):
        if not filename.endswith(INPUT_EXT):
            continue
        name = filename[: -len(INPUT_EXT)]
        result[name] = read_urls(os.path.join(input_dir, filename))
    return result


def write_urls(input_dir: str, artist_name: str, urls: List[str]) -> str:
    """아티스트의 URL 목록을 저장(생성 또는 덮어쓰기)하고 파일 경로를 반환합니다."""
    os.makedirs(input_dir, exist_ok=True)
    path = artist_file_path(input_dir, artist_name)
    cleaned = [u.strip() for u in urls if u and u.strip()]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(cleaned) + ("\n" if cleaned else ""))
    return path


def delete_artist(input_dir: str, artist_name: str) -> bool:
    """아티스트 입력 파일을 삭제합니다. 파일이 없었다면 False."""
    path = artist_file_path(input_dir, artist_name)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True
