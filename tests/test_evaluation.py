import pytest
import torch

import evaluation as ev


def _data(noise, centers=4, per=3, dim=16, shared=5.0, seed=0):
    g = torch.Generator().manual_seed(seed)
    common = torch.randn(dim, generator=g) * shared
    ids = torch.randn(centers, dim, generator=g)
    embs, labels = [], []
    for a in range(centers):
        for _ in range(per):
            embs.append(common + ids[a] + noise * torch.randn(dim, generator=g))
            labels.append(a)
    return torch.stack(embs), torch.tensor(labels)


def test_eer_perfect_and_worst():
    assert ev.equal_error_rate(torch.tensor([0.9, 0.8]), torch.tensor([0.1, 0.2])) == 0.0
    assert ev.equal_error_rate(torch.tensor([0.1, 0.2]), torch.tensor([0.9, 0.8])) == 1.0


def test_clean_data_scores_perfectly():
    embs, labels = _data(noise=0.01)
    m = ev.evaluate(embs, labels, center=True)
    assert m["accuracy"] == 1.0
    assert m["eer"] == 0.0
    assert m["gap"] > 0


def test_noisier_data_is_worse():
    clean = ev.evaluate(*_data(0.01), center=True)
    noisy = ev.evaluate(*_data(3.0), center=True)
    assert noisy["gap"] < clean["gap"]


def test_retrieval_ignores_singleton_artists():
    embs = torch.tensor([[1.0, 0.0], [0.99, 0.1], [0.0, 1.0]])
    labels = torch.tensor([0, 0, 1])  # 아티스트 1 은 영상이 1개
    acc = ev.retrieval_accuracy(ev.prepare(embs), labels)
    assert acc == 1.0


def test_evaluate_requires_pairs():
    with pytest.raises(ValueError):
        ev.evaluate(torch.randn(2, 4), torch.tensor([0, 1]))
