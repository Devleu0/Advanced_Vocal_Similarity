import hashlib
import platform
import re
from urllib.parse import urlparse
import matplotlib.pyplot as plt
from logger import log

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

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def is_youtube_url(url):
    """URL 의 호스트가 유튜브 계열인지 확인합니다."""
    return (urlparse(url).hostname or "").lower() in YOUTUBE_HOSTS


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


def get_media_id(url):
    """
    yt-dlp 가 지원하는 임의의 영상 URL 에서 파일명에 쓸 11자 ID 를 만듭니다.

    - 유튜브 URL: 기존과 같은 11자리 비디오 ID (기존 산출물과 호환)
    - 그 외 http(s) URL: ``u`` + URL 해시 10자리 (같은 URL → 항상 같은 ID)
    - 영상 페이지로 보기 어려운 입력(스킴 없음, 경로 없는 도메인 등): None
    """
    if is_youtube_url(url):
        return extract_video_id(url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.path in ("", "/"):
        return None
    return "u" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def normalize_download_url(url, media_id):
    """유튜브는 안정적인 다운로드를 위해 표준 watch URL 로 정규화하고, 그 외는 원본 URL 을 씁니다."""
    if is_youtube_url(url):
        return f"https://www.youtube.com/watch?v={media_id}"
    return url
