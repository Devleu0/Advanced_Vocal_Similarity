"""명령행 인자 → config 덮어쓰기. 프리셋, --set KEY=VALUE, 검증을 담당합니다."""
import argparse
import ast

# 프리셋: 속도 ↔ 정확도 번들. (정확도 향상은 기대치이며 evaluate.py 로 검증 권장)
PRESETS = {
    "fast": {
        "description": "빠름: 가벼운 보컬 분리 모델 + 영상당 최대 240초만 사용",
        "values": {"DEMUCS_MODEL": "htdemucs", "MAX_AUDIO_SEC": 240},
    },
    "balanced": {
        "description": "기본값 (config.py 그대로)",
        "values": {},
    },
    "accurate": {
        "description": "느림: 모델 앙상블 + Silero VAD + Demucs shifts + 다중화자 필터 + s-norm + 영상 단위 점수",
        "values": {
            "ENSEMBLE_MODELS": ["ecapa", "wavlm-sv"],
            "VAD_BACKEND": "silero",
            "DEMUCS_SHIFTS": 2,
            "MULTI_SPEAKER_FILTER": True,
            "SCORE_NORM": "snorm",
            "ARTIST_SCORING": "video_topk",
        },
    },
}

CHOICES = {
    "VAD_BACKEND": ("rms", "silero"),
    "ARTIST_SCORING": ("profile", "video_max", "video_topk"),
    "SCORE_NORM": (None, "snorm"),
}


def format_presets():
    return "\n".join(f"  {k:<9s} {p['description']}" for k, p in PRESETS.items())


def parse_set(pairs):
    """['KEY=VALUE', ...] → {KEY: python 값}. 값은 literal(숫자/True/None/리스트)로 해석, 아니면 문자열."""
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"--set 형식은 KEY=VALUE 입니다: {pair}")
        key, raw = pair.split("=", 1)
        try:
            out[key.strip()] = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            out[key.strip()] = raw
    return out


def build_overrides(preset=None, explicit=None, set_pairs=None):
    """우선순위: 프리셋 < 명시 플래그 < --set."""
    merged = {}
    if preset:
        if preset not in PRESETS:
            raise ValueError(f"알 수 없는 프리셋 '{preset}'. 선택 가능: {', '.join(PRESETS)}")
        merged.update(PRESETS[preset]["values"])
    merged.update({k: v for k, v in (explicit or {}).items() if v is not None})
    merged.update(parse_set(set_pairs))
    return merged


def apply_overrides(cfg, overrides):
    for key, value in overrides.items():
        if not hasattr(cfg, key):
            raise ValueError(f"알 수 없는 설정 키: {key}")
        setattr(cfg, key, value)


def validate(cfg, model_keys):
    for key, allowed in CHOICES.items():
        if getattr(cfg, key) not in allowed:
            raise ValueError(f"{key} 는 {allowed} 중 하나여야 합니다 (현재: {getattr(cfg, key)!r})")
    for m in [cfg.EMBEDDING_MODEL, *cfg.ENSEMBLE_MODELS]:
        if m not in model_keys:
            raise ValueError(f"알 수 없는 임베딩 모델 '{m}'. 선택 가능: {', '.join(model_keys)}")


def build_parser(model_keys):
    p = argparse.ArgumentParser(description="Advanced Vocal Similarity 파이프라인")
    p.add_argument("--preset", choices=list(PRESETS), help="속도/정확도 프리셋 (--list-presets)")
    p.add_argument("--model", choices=list(model_keys), help="임베딩 모델 (--list-models)")
    p.add_argument("--ensemble", help="앙상블할 모델을 쉼표로 (예: ecapa,wavlm-sv)")
    p.add_argument("--input-dir", help="URL 목록(txt) 폴더")
    p.add_argument("--db-dir", help="산출물 저장 폴더")
    p.add_argument("--device", help="cpu 또는 cuda:0")
    p.add_argument("--set", action="append", metavar="KEY=VALUE", dest="set_pairs",
                   help="config.py 의 임의 설정 덮어쓰기 (여러 번 가능). 예: --set CHUNK_SEC=3")
    p.add_argument("--list-models", action="store_true", help="임베딩 모델 목록")
    p.add_argument("--list-presets", action="store_true", help="프리셋 목록")
    return p


def explicit_from_args(args):
    return {
        "EMBEDDING_MODEL": args.model,
        "ENSEMBLE_MODELS": args.ensemble.split(",") if args.ensemble else None,
        "INPUT_DIR": args.input_dir,
        "DB_DIR": args.db_dir,
        "DEVICE": args.device,
    }
