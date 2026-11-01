import pytest
import torch

import similarity as sim


def _artists(seed=0, n=5, videos=3, dim=16, spread=0.3):
    g = torch.Generator().manual_seed(seed)
    out = {}
    for i in range(n):
        center = torch.randn(dim, generator=g)
        out[f"a{i}"] = [center + spread * torch.randn(dim, generator=g) for _ in range(videos)]
    return out


@pytest.mark.parametrize("mode", sim.SCORING_MODES)
def test_all_modes_square_symmetric_unit_diagonal(mode):
    names, m = sim.artist_similarity(_artists(), mode=mode, center=False)
    assert m.shape == (5, 5) and len(names) == 5
    assert torch.allclose(m, m.T, atol=1e-6)
    assert torch.allclose(m.diag(), torch.ones(5), atol=1e-5)


def test_video_max_is_at_least_topk_mean():
    arts = _artists()
    _, mx = sim.artist_similarity(arts, "video_max", center=False)
    _, tk = sim.artist_similarity(arts, "video_topk", center=False, topk=3)
    assert torch.all(mx >= tk - 1e-6)


def test_video_modes_catch_one_matching_style():
    # a 는 두 가지 창법. 한 창법이 b 와 같다 → profile 보다 video_max 가 더 높게 평가
    g = torch.Generator().manual_seed(0)
    style1, style2 = torch.randn(16, generator=g), torch.randn(16, generator=g)
    arts = {"a": [style1, style2], "b": [style2 + 0.01], "c": [torch.randn(16, generator=g)]}
    _, prof = sim.artist_similarity(arts, "profile", center=False)
    _, vmax = sim.artist_similarity(arts, "video_max", center=False)
    assert vmax[0, 1] > prof[0, 1]
    assert vmax[0, 1] > 0.99


def test_unknown_mode():
    with pytest.raises(ValueError):
        sim.artist_similarity(_artists(), mode="nope")


def test_score_normalize_symmetric_and_skips_small():
    _, m = sim.artist_similarity(_artists(n=6), "profile", center=False)
    z = sim.score_normalize(m)
    assert torch.allclose(z, z.T, atol=1e-5)
    small = torch.tensor([[1.0, 0.5], [0.5, 1.0]])
    assert torch.equal(sim.score_normalize(small), small)


def test_score_normalize_is_finite_with_hub_artist():
    # 0번은 모두와 비슷한 '허브'
    m = torch.tensor([
        [1.0, 0.8, 0.8, 0.8, 0.8],
        [0.8, 1.0, 0.2, 0.1, 0.3],
        [0.8, 0.2, 1.0, 0.3, 0.1],
        [0.8, 0.1, 0.3, 1.0, 0.2],
        [0.8, 0.3, 0.1, 0.2, 1.0],
    ])
    z = sim.score_normalize(m)
    assert torch.isfinite(z).all()
    assert torch.allclose(z, z.T, atol=1e-5)


def test_ensemble_aligns_common_artists():
    m1 = torch.tensor([[1.0, 0.2, 0.3], [0.2, 1.0, 0.4], [0.3, 0.4, 1.0]])
    m2 = torch.tensor([[1.0, 0.6], [0.6, 1.0]])
    names, m = sim.ensemble_matrices([(["a", "b", "c"], m1), (["c", "a"], m2)])
    assert names == ["a", "c"]
    assert torch.isclose(m[0, 1], torch.tensor((0.3 + 0.6) / 2))


def test_video_similarity_matrix_labels():
    labels, m = sim.video_similarity_matrix([("x", torch.randn(8)), ("y", torch.randn(8))], center=False)
    assert labels == ["x", "y"] and m.shape == (2, 2)
    assert abs(m[0, 0].item() - 1.0) < 1e-5
