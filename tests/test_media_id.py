import pytest

from utils import get_media_id, is_youtube_url, normalize_download_url


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
])
def test_youtube_ids_unchanged(url):
    assert is_youtube_url(url)
    assert get_media_id(url) == "dQw4w9WgXcQ"
    assert normalize_download_url(url, "dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_other_site_gets_stable_hash_id_and_original_url():
    url = "https://vimeo.com/76979871"
    mid = get_media_id(url)
    assert not is_youtube_url(url)
    assert mid.startswith("u") and len(mid) == 11
    assert get_media_id(url) == mid                       # 같은 URL → 같은 ID
    assert get_media_id("https://vimeo.com/76979872") != mid
    assert normalize_download_url(url, mid) == url


@pytest.mark.parametrize("url", ["", "https://example.com", "https://example.com/", "not a url", "ftp://x.com/a"])
def test_non_video_inputs_rejected(url):
    assert get_media_id(url) is None


def test_looks_like_youtube_id_on_other_host_is_not_treated_as_youtube():
    # 기존 정규식은 아무 사이트의 11자 경로도 ID 로 오인했다
    assert not is_youtube_url("https://example.com/abcdefghijk")
    assert get_media_id("https://example.com/abcdefghijk").startswith("u")
