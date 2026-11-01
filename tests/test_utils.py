import hashlib
from unittest.mock import MagicMock

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pytest

from vocal_similarity.utils import (
    extract_media_id,
    extract_video_id,
    is_valid_media_url,
    is_youtube_url,
    setup_korean_font,
)


@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch('vocal_similarity.utils.log', new=MagicMock())


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLMC9KNkIncK_bBHBwQ8pgx7i-A7lP1-2B",
])
def test_extract_video_id_valid(url):
    assert extract_video_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize("url", ["https://www.google.com", ""])
def test_extract_video_id_invalid(url):
    assert extract_video_id(url) is None


@pytest.mark.parametrize("url, expected", [
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
    ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", True),
    ("youtu.be/dQw4w9WgXcQ", True),
    ("https://example.com/not-youtube", False),  # 경로가 우연히 11자리
    ("https://www.youtube.com/", False),
    ("", False),
])
def test_is_youtube_url(url, expected):
    assert is_youtube_url(url) is expected


@pytest.mark.parametrize("url", [
    "https://example.com/media/track",
    "https://soundcloud.com/artist/track",
    "http://media.example.org:8080/audio?id=1",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
])
def test_is_valid_media_url_accepts_external_http_urls(url):
    assert is_valid_media_url(url)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://example.com/audio",
    "http://localhost/audio",
    "http://service.local/audio",
    "http://127.0.0.1/audio",
    "http://192.168.1.10/audio",
    "https://user:password@example.com/audio",
    "https://example.com:99999/audio",
])
def test_is_valid_media_url_rejects_unsafe_urls(url):
    assert not is_valid_media_url(url)


def test_extract_media_id_preserves_youtube_id_and_hashes_other_urls():
    youtube = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    external = "https://soundcloud.com/artist/track"
    assert extract_media_id(youtube) == "dQw4w9WgXcQ"
    assert extract_media_id(external) == hashlib.sha256(external.encode("utf-8")).hexdigest()[:16]


def test_setup_korean_font_windows(mocker):
    mocker.patch('platform.system', return_value='Windows')
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'Malgun Gothic'
    assert not plt.rcParams['axes.unicode_minus']


def test_setup_korean_font_darwin(mocker):
    mocker.patch('platform.system', return_value='Darwin')
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'AppleGothic'


def test_setup_korean_font_linux_nanumgothic_found(mocker):
    mocker.patch('platform.system', return_value='Linux')
    font = MagicMock()
    font.name = 'NanumGothic'
    mocker.patch.object(fm.fontManager, 'ttflist', [font])
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'NanumGothic'


def test_setup_korean_font_linux_nanumgothic_not_found(mocker):
    mocker.patch('platform.system', return_value='Linux')
    mocker.patch.object(fm.fontManager, 'ttflist', [])
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'sans-serif'
