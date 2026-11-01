"""임베딩 → 마스터 프로필 → 유사도 행렬 계산 (I/O·시각화와 분리된 순수 로직)."""
import torch


def build_master_profile(embs):
    """임베딩 목록을 평균 낸 뒤 L2 정규화한 마스터 프로필 (D,) 을 반환합니다."""
    stacked = torch.stack(list(embs))
    return torch.nn.functional.normalize(stacked.mean(dim=0), p=2, dim=0)


def compute_similarity_matrix(profiles):
    """{이름: 벡터} → (이름 리스트, (N, N) 코사인 유사도 텐서)."""
    names = list(profiles.keys())
    mat = torch.stack([profiles[n] for n in names])
    mat = torch.nn.functional.normalize(mat, p=2, dim=1)
    return names, mat @ mat.T
