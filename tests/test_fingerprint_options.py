import torch

import fingerprint as fp


def _two_speakers(n_a=6, n_b=3, dim=8, noise=0.02, seed=0):
    g = torch.Generator().manual_seed(seed)
    a = torch.zeros(dim)
    a[0] = 1.0
    b = torch.zeros(dim)
    b[1] = 1.0
    embs = [a + noise * torch.randn(dim, generator=g) for _ in range(n_a)]
    embs += [b + noise * torch.randn(dim, generator=g) for _ in range(n_b)]
    return torch.nn.functional.normalize(torch.stack(embs), p=2, dim=1)


def test_dominant_cluster_picks_larger_speaker():
    idx = fp.dominant_cluster(_two_speakers())
    assert sorted(idx.tolist()) == [0, 1, 2, 3, 4, 5]


def test_dominant_cluster_single_speaker_keeps_all():
    g = torch.Generator().manual_seed(1)
    base = torch.zeros(8)
    base[0] = 1.0
    embs = torch.nn.functional.normalize(base + 0.02 * torch.randn(8, 8, generator=g), p=2, dim=1)
    assert len(fp.dominant_cluster(embs)) == 8


def test_dominant_cluster_too_few_chunks():
    assert len(fp.dominant_cluster(torch.randn(3, 4))) == 3


def test_aggregate_multi_speaker_uses_main_voice():
    out, kept = fp.aggregate_embeddings(
        _two_speakers(), use_outlier_removal=False, multi_speaker=True
    )
    assert kept == 6
    assert out[0] > 0.99


def test_aggregate_multi_speaker_off_mixes_voices():
    out, kept = fp.aggregate_embeddings(_two_speakers(), use_outlier_removal=False)
    assert kept == 9
    assert out[1] > 0.3


def test_filter_by_speech_ratio():
    chunks = [torch.zeros(1, 10) + i for i in range(4)]
    kept = fp.filter_by_speech_ratio(chunks, lambda c: c.mean().item() / 3, 0.5)
    assert len(kept) == 2  # i=2,3
