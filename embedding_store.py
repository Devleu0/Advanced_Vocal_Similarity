"""임베딩 파일 경로 규칙. 모델마다 차원/공간이 달라 섞이면 안 되므로 파일명으로 구분합니다.

- 기본 모델(ecapa): 기존 호환을 위해 ``emb_{vid}.pt``
- 그 외 모델:       ``emb_{model}_{vid}.pt``
"""
import glob
import os

LEGACY_MODEL = "ecapa"


def embedding_path(artist_dir, vid, model=LEGACY_MODEL):
    name = f"emb_{vid}.pt" if model == LEGACY_MODEL else f"emb_{model}_{vid}.pt"
    return os.path.join(artist_dir, name)


def chunk_cache_path(artist_dir, vid, model=LEGACY_MODEL):
    """집계 이전의 청크 임베딩 캐시 (emb_*.pt 패턴과 겹치지 않음)."""
    return os.path.join(artist_dir, f"chunks_{model}_{vid}.pt")


def list_embedding_files(artist_dir, model, all_models):
    """artist_dir 안에서 ``model`` 로 만든 임베딩 파일만 정렬해서 반환합니다."""
    others = [m for m in all_models if m != LEGACY_MODEL]

    def owner(path):
        base = os.path.basename(path)
        for m in others:
            if base.startswith(f"emb_{m}_"):
                return m
        return LEGACY_MODEL

    files = sorted(glob.glob(os.path.join(artist_dir, "emb_*.pt")))
    return [f for f in files if owner(f) == model]
