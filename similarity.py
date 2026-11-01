"""임베딩 → 프로필/영상 단위 점수 → 유사도 행렬 계산 (I/O·시각화와 분리된 순수 로직)."""
import torch

_normalize = torch.nn.functional.normalize

SCORING_MODES = ("profile", "video_max", "video_topk")


def build_master_profile(embs):
    """임베딩 목록을 L2 정규화 후 평균 내고 다시 정규화한 프로필 (D,) 을 반환합니다."""
    stacked = _normalize(torch.stack(list(embs)), p=2, dim=1)
    return _normalize(stacked.mean(dim=0), p=2, dim=0)


def _prepare(artist_embs, center, min_artists):
    """아티스트별 임베딩을 정규화하고, 조건이 맞으면 아티스트 공통 성분을 뺍니다.

    아티스트가 min_artists 명 미만이면 평균이 불안정해(2명이면 항상 -1) 센터링을 건너뜁니다.
    아티스트당 가중치가 같도록 아티스트 평균들의 평균을 사용합니다.
    """
    normed = {a: _normalize(torch.stack(list(e)), p=2, dim=1) for a, e in artist_embs.items()}
    if center and len(normed) >= min_artists:
        mu = torch.stack([v.mean(dim=0) for v in normed.values()]).mean(dim=0)
        normed = {a: v - mu for a, v in normed.items()}
    return normed


def build_master_profiles(artist_embs, center=True, min_artists=5):
    """{아티스트: [임베딩...]} → {아티스트: 프로필}."""
    normed = _prepare(artist_embs, center, min_artists)
    return {a: _normalize(v.mean(dim=0), p=2, dim=0) for a, v in normed.items()}


def compute_similarity_matrix(profiles):
    """{이름: 벡터} → (이름 리스트, (N, N) 코사인 유사도 텐서)."""
    names = list(profiles.keys())
    mat = _normalize(torch.stack([profiles[n] for n in names]), p=2, dim=1)
    return names, mat @ mat.T


def artist_similarity(artist_embs, mode="profile", center=True, min_artists=5, topk=3):
    """아티스트 간 유사도 행렬을 계산합니다.

    - profile:    아티스트 평균 프로필끼리 비교 (기본, 빠름)
    - video_max:  두 아티스트의 영상 쌍 중 가장 비슷한 쌍의 점수 (창법이 다양한 가수에 유리)
    - video_topk: 영상 쌍 점수 상위 topk 개의 평균 (max 보다 이상치에 덜 민감)
    """
    if mode not in SCORING_MODES:
        raise ValueError(f"알 수 없는 scoring 모드 '{mode}'. 선택 가능: {', '.join(SCORING_MODES)}")
    if mode == "profile":
        return compute_similarity_matrix(build_master_profiles(artist_embs, center, min_artists))

    normed = {a: _normalize(v, p=2, dim=1)
              for a, v in _prepare(artist_embs, center, min_artists).items()}
    names = list(normed)
    n = len(names)
    matrix = torch.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            pair = (normed[names[i]] @ normed[names[j]].T).flatten()
            score = pair.max() if mode == "video_max" else pair.topk(min(topk, pair.numel())).values.mean()
            matrix[i, j] = matrix[j, i] = score
    return names, matrix


def video_similarity_matrix(labeled_embs, center=True, min_videos=5):
    """[(라벨, 임베딩)] → (라벨 리스트, (V, V) 영상 단위 코사인 유사도)."""
    labels = [label for label, _ in labeled_embs]
    x = _normalize(torch.stack([e for _, e in labeled_embs]), p=2, dim=1)
    if center and len(x) >= min_videos:
        x = _normalize(x - x.mean(dim=0, keepdim=True), p=2, dim=1)
    return labels, x @ x.T


def score_normalize(matrix, min_n=4):
    """대칭 점수 정규화(s-norm 계열): 각 아티스트의 '다른 아티스트와의 점수 분포'로 z-score 화.

    '누구와도 잘 맞는' 아티스트가 과대평가되는 것을 줄입니다. 대각선은 최댓값으로 채웁니다.
    아티스트가 min_n 명 미만이면 분포를 추정할 수 없어 원본을 반환합니다.
    """
    n = matrix.shape[0]
    if n < min_n:
        return matrix
    off = ~torch.eye(n, dtype=torch.bool)
    rows = matrix.masked_fill(~off, float("nan"))
    mu = torch.nanmean(rows, dim=1)
    sd = torch.sqrt(torch.nanmean((rows - mu[:, None]) ** 2, dim=1)) + 1e-6
    z = (matrix - mu[:, None]) / sd[:, None]
    out = 0.5 * (z + z.T)
    out[~off] = out[off].max()
    return out


def ensemble_matrices(results):
    """[(이름 리스트, 행렬), ...] 을 공통 아티스트 기준으로 정렬해 평균합니다."""
    common = [n for n in results[0][0] if all(n in names for names, _ in results)]
    mats = []
    for names, m in results:
        idx = [names.index(n) for n in common]
        mats.append(m[idx][:, idx])
    return common, torch.stack(mats).mean(dim=0)
