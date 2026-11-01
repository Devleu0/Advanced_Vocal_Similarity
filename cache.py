"""산출물(보컬/청크 임베딩/지문)의 생성 설정을 기록하고 일치 여부를 검사합니다.

설정이 바뀐 뒤 예전 산출물이 조용히 섞이는 것을 막고, 설정이 같으면 무거운 단계를 건너뛰게 합니다.
메타데이터는 ``<파일>.meta.json`` 에 저장됩니다.
"""
import hashlib
import json
import os


def signature(settings):
    payload = json.dumps(settings, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def meta_path(path):
    return f"{path}.meta.json"


def write_meta(path, settings):
    with open(meta_path(path), "w", encoding="utf-8") as f:
        json.dump({"signature": signature(settings), "settings": settings}, f,
                  ensure_ascii=False, indent=2, default=str)


def read_signature(path):
    try:
        with open(meta_path(path), encoding="utf-8") as f:
            return json.load(f).get("signature")
    except (OSError, ValueError):
        return None


def is_fresh(path, settings, allow_legacy=False):
    """파일이 있고 생성 설정이 같으면 True.

    allow_legacy=True 이면 메타데이터가 없는 (이전 버전이 만든) 파일도 유효로 봅니다.
    """
    if not os.path.exists(path):
        return False
    stored = read_signature(path)
    if stored is None:
        return allow_legacy
    return stored == signature(settings)
