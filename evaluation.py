"""유사도 파이프라인의 품질을 정량 평가하는 순수 함수 (정답 = 영상이 속한 아티스트).

같은 아티스트의 영상끼리는 유사하고 다른 아티스트와는 덜 유사해야 한다는 가정으로,
설정(모델/VAD/센터링 등)을 바꿨을 때 좋아졌는지 숫자로 비교할 수 있게 합니다.
"""
import torch

_normalize = torch.nn.functional.normalize


def prepare(embs, center=False):
    """(N, D) 영상 임베딩을 정규화하고 선택적으로 전체 평균을 빼 다시 정규화합니다."""
    x = _normalize(embs, p=2, dim=1)
    if center:
        x = _normalize(x - x.mean(dim=0, keepdim=True), p=2, dim=1)
    return x


def _pair_scores(x, labels):
    sims = x @ x.T
    same = labels[:, None] == labels[None, :]
    upper = torch.ones(same.shape).triu(diagonal=1).bool()
    return sims[same & upper], sims[~same & upper]


def equal_error_rate(genuine, impostor):
    """동일인(genuine)/타인(impostor) 점수 분포의 EER (낮을수록 좋음)."""
    thr = torch.unique(torch.cat([genuine, impostor]))
    far = (impostor[None, :] >= thr[:, None]).float().mean(dim=1)
    frr = (genuine[None, :] < thr[:, None]).float().mean(dim=1)
    k = torch.argmin((far - frr).abs())
    return ((far[k] + frr[k]) / 2).item()


def retrieval_accuracy(x, labels):
    """각 영상의 최근접 이웃(자기 자신 제외)이 같은 아티스트인 비율 (높을수록 좋음).

    영상이 1개뿐인 아티스트는 정답이 없으므로 제외합니다.
    """
    sims = x @ x.T
    sims.fill_diagonal_(float("-inf"))
    counts = (labels[:, None] == labels[None, :]).sum(dim=1)
    valid = counts > 1
    if not valid.any():
        return float("nan")
    nearest = sims.argmax(dim=1)
    return (labels[nearest] == labels)[valid].float().mean().item()


def evaluate(embs, labels, center=False):
    """{'eer','accuracy','intra','inter','gap'} 를 반환합니다. labels: (N,) 정수 텐서."""
    x = prepare(embs, center)
    genuine, impostor = _pair_scores(x, labels)
    if len(genuine) == 0 or len(impostor) == 0:
        raise ValueError("평가에는 영상이 2개 이상인 아티스트와 아티스트 2명 이상이 필요합니다.")
    return {
        "eer": equal_error_rate(genuine, impostor),
        "accuracy": retrieval_accuracy(x, labels),
        "intra": genuine.mean().item(),
        "inter": impostor.mean().item(),
        "gap": (genuine.mean() - impostor.mean()).item(),
    }
