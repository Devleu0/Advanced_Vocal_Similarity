import pytest
from utils import extract_video_id, setup_korean_font
import matplotlib.pyplot as plt
import platform
import matplotlib.font_manager as fm

# Mock log for setup_korean_font to prevent actual printing during tests
class MockLogger:
    def info(self, message):
        pass
    def warning(self, message):
        pass

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch('utils.log', new=MockLogger())

def test_extract_video_id_standard_url():
    """표준 YouTube URL에서 비디오 ID를 올바르게 추출하는지 테스트"""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    expected_id = "dQw4w9WgXcQ"
    assert extract_video_id(url) == expected_id

def test_extract_video_id_short_url():
    """단축 YouTube URL에서 비디오 ID를 올바르게 추출하는지 테스트"""
    url = "https://youtu.be/dQw4w9WgXcQ"
    expected_id = "dQw4w9WgXcQ"
    assert extract_video_id(url) == expected_id

def test_extract_video_id_with_playlist_params():
    """재생 목록 파라미터가 포함된 URL에서 비디오 ID를 올바르게 추출하는지 테스트"""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLMC9KNkIncK_bBHBwQ8pgx7i-A7lP1-2B"
    expected_id = "dQw4w9WgXcQ"
    assert extract_video_id(url) == expected_id

def test_extract_video_id_invalid_url():
    """유효하지 않은 URL에서 None을 반환하는지 테스트"""
    url = "https://www.google.com"
    assert extract_video_id(url) is None

def test_extract_video_id_empty_string():
    """빈 문자열에 대해 None을 반환하는지 테스트"""
    url = ""
    assert extract_video_id(url) is None

def test_setup_korean_font_windows(mocker):
    """Windows 환경에서 올바른 폰트가 설정되는지 테스트"""
    mocker.patch('platform.system', return_value='Windows')
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'Malgun Gothic'
    assert not plt.rcParams['axes.unicode_minus']

def test_setup_korean_font_darwin(mocker):
    """macOS 환경에서 올바른 폰트가 설정되는지 테스트"""
    mocker.patch('platform.system', return_value='Darwin')
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'AppleGothic'
    assert not plt.rcParams['axes.unicode_minus']

def test_setup_korean_font_linux_nanumgothic_found(mocker):
    """Linux 환경에서 NanumGothic이 발견될 때 올바른 폰트가 설정되는지 테스트"""
    mocker.patch('platform.system', return_value='Linux')
    # Simulate NanumGothic being available
    mock_font = mocker.Mock(name='NanumGothic')
    mocker.patch.object(fm.fontManager, 'ttflist', [mock_font])
    
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'NanumGothic'
    assert not plt.rcParams['axes.unicode_minus']

def test_setup_korean_font_linux_nanumgothic_not_found(mocker):
    """Linux 환경에서 NanumGothic을 찾을 수 없을 때 대체 폰트가 설정되는지 테스트"""
    mocker.patch('platform.system', return_value='Linux')
    # Simulate NanumGothic not being available
    mocker.patch.object(fm.fontManager, 'ttflist', []) 
    
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'sans-serif'
    assert not plt.rcParams['axes.unicode_minus']

def test_setup_korean_font_linux_import_error(mocker):
    """Linux 환경에서 font_manager import 에러 발생 시 대체 폰트가 설정되는지 테스트"""
    mocker.patch('platform.system', return_value='Linux')
    mocker.patch('matplotlib.font_manager', side_effect=ImportError)
    
    setup_korean_font()
    assert plt.rcParams['font.family'][0] == 'sans-serif'
    assert not plt.rcParams['axes.unicode_minus']
