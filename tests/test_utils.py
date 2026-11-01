import pytest
from unittest.mock import MagicMock
from utils import extract_video_id, setup_korean_font
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch('utils.log', new=MagicMock())


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
