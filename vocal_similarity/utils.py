import platform
import re
from urllib.parse import urlparse

import matplotlib.pyplot as plt

from .logger import log


def setup_korean_font():
    """
    OS에 맞는 한글 폰트를 설정하여 Matplotlib 시각화 시 한글 깨짐을 방지합니다.
    """
    system_name = platform.system()
    
    if system_name == 'Windows':
        font_family = 'Malgun Gothic'
    elif system_name == 'Darwin': # Mac
        font_family = 'AppleGothic'
    else: # Linux
        # 나눔고딕이 설치되어 있는지 확인 후 설정
        try:
            import matplotlib.font_manager as fm
            if any('NanumGothic' in font.name for font in fm.fontManager.ttflist):
                font_family = 'NanumGothic'
            else:
                # 대체 폰트나 경고 메시지
                log.warning("NanumGothic not found. Please install it for proper Korean display.")
                font_family = 'sans-serif' # 기본 폰트로 대체
        except ImportError:
            log.warning("Could not check for NanumGothic. Using a default font.")
            font_family = 'sans-serif'
            
    plt.rc('font', family=font_family)
    plt.rcParams['axes.unicode_minus'] = False
    log.info(f"[*] 한글 폰트 설정 완료: {font_family} ({system_name} OS)")

def extract_video_id(url):
    """
    유튜브 URL에서 11자리 비디오 ID를 추출합니다. (youtu.be 단축 링크 포함)
    
    Args:
        url (str): 유튜브 비디오 URL.
        
    Returns:
        str or None: 추출된 비디오 ID 또는 실패 시 None.
    """
    match = re.search(r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})', url)
    return match.group(1) if match else None


_YOUTUBE_HOSTS = ("youtube.com", "youtu.be", "youtube-nocookie.com")


def is_youtube_url(url):
    """유튜브 도메인이면서 비디오 ID 를 추출할 수 있는 URL 인지 검사합니다.

    extract_video_id 는 경로의 11자리 문자열도 ID 로 인식하므로(예: example.com/not-youtube),
    사용자 입력 검증에는 이 함수를 사용합니다.
    """
    if not url:
        return False
    host = urlparse(url if "://" in url else f"https://{url}").hostname or ""
    on_youtube = any(host == h or host.endswith("." + h) for h in _YOUTUBE_HOSTS)
    return on_youtube and extract_video_id(url) is not None
