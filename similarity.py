"""임베딩 → 마스터 프로필 → 유사도 행렬 계산 (I/O·시각화와 분리된 순수 로직)."""
import torch

_normalize = torch.nn.functional.normalize


def build_master_profile(embs):
    """임베딩 목록을 L2 정규화 후 평균 내고 다시 정규화한 프로필 (D,) 을 반환합니다."""
    stacked = _normalize(torch.stack(list(embs)), p=2, dim=1)
    return _normalize(stacked.mean(dim=0), p=2, dim=0)


def build_master_profiles(artist_embs, center=True, min_artists=5):
    """{아티스트: [임베딩...]} → {아티스트: 프로필}.

    center=True 이고 아티스트가 min_artists 명 이상이면, 모든 아티스트에 공통인 성분
    (가수 공통 창법/장르/녹음 특성)을 빼서 아티스트 고유 특성의 대비를 키웁니다.
    아티스트가 적으면 평균이 불안정해(2명이면 항상 -1) 센터링을 건너뜁니다.
    아티스트당 가중치가 같도록 아티스트 평균들의 평균을 사용합니다.
    """
    normed = {a: _normalize(torch.stack(list(e)), p=2, dim=1) for a, e in artist_embs.items()}
    if center and len(normed) >= min_artists:
        mu = torch.stack([v.mean(dim=0) for v in normed.values()]).mean(dim=0)
        normed = {a: v - mu for a, v in normed.items()}
    return {a: _normalize(v.mean(dim=0), p=2, dim=0) for a, v in normed.items()}


def compute_similarity_matrix(profiles):
    """{이름: 벡터} → (이름 리스트, (N, N) 코사인 유사도 텐서)."""
    names = list(profiles.keys())
    mat = _normalize(torch.stack([profiles[n] for n in names]), p=2, dim=1)
    return names, mat @ mat.T
