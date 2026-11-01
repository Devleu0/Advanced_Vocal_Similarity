from unittest.mock import MagicMock

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pytest

from vocal_similarity.utils import extract_video_id, is_youtube_url, setup_korean_font


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
