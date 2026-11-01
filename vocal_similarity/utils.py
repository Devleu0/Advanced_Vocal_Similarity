import hashlib
import ipaddress
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
    """유튜브 동영상 ID를 추출할 수 있는 URL인지 검사합니다."""
    if not url:
        return False
    try:
        host = urlparse(url if "://" in url else f"//{url}").hostname or ""
    except ValueError:
        return False
    on_youtube = any(host == h or host.endswith("." + h) for h in _YOUTUBE_HOSTS)
    return on_youtube and extract_video_id(url) is not None


def is_valid_media_url(url):
    """yt-dlp 입력으로 사용할 외부 HTTP(S) URL을 검사합니다.

    URL 자체로 localhost 또는 사설·예약 IP에 접근하지 못하도록 제한합니다.
    실제 사이트/미디어 지원 여부는 yt-dlp 실행 시 확인됩니다.
    """
    if not url or url != url.strip():
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return False
        if parsed.username or parsed.password or not parsed.hostname:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local")):
            return False
        port = parsed.port
    except ValueError:
        return False

    if port is not None and not 1 <= port <= 65535:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


def extract_media_id(url):
    """미디어 URL의 파일 저장용 ID를 반환합니다(YouTube는 기존 11자리 ID 유지)."""
    if is_youtube_url(url):
        return extract_video_id(url)
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
