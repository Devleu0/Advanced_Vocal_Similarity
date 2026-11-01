import torch

import similarity as sim


def test_master_profile_is_unit_norm():
    p = sim.build_master_profile([torch.randn(16), torch.randn(16)])
    assert abs(p.norm().item() - 1.0) < 1e-5


def test_similarity_matrix_properties():
    profiles = {
        "a": torch.tensor([1.0, 0.0]),
        "b": torch.tensor([0.0, 2.0]),
        "c": torch.tensor([3.0, 0.0]),
    }
    names, m = sim.compute_similarity_matrix(profiles)
    assert names == ["a", "b", "c"]
    assert torch.allclose(m.diag(), torch.ones(3), atol=1e-5)
    assert torch.allclose(m, m.T)
    assert abs(m[0, 1].item()) < 1e-5
    assert abs(m[0, 2].item() - 1.0) < 1e-5


def _artists(n, common=5.0, dim=32, seed=0):
    g = torch.Generator().manual_seed(seed)
    base = torch.randn(dim, generator=g) * common
    return {
        f"a{i}": [base + torch.randn(dim, generator=g) + 0.1 * torch.randn(dim, generator=g)]
        for i in range(n)
    }


def test_centering_increases_contrast_when_enough_artists():
    artists = _artists(6)
    _, raw = sim.compute_similarity_matrix(sim.build_master_profiles(artists, center=False))
    _, cen = sim.compute_similarity_matrix(sim.build_master_profiles(artists, center=True))
    off = ~torch.eye(6, dtype=torch.bool)
    assert cen[off].mean() < raw[off].mean()


def test_centering_skipped_with_few_artists():
    artists = _artists(2)
    raw = sim.build_master_profiles(artists, center=False)
    cen = sim.build_master_profiles(artists, center=True, min_artists=5)
    for k in raw:
        assert torch.allclose(raw[k], cen[k])


def test_profiles_are_unit_norm():
    for p in sim.build_master_profiles(_artists(6), center=True).values():
        assert abs(p.norm().item() - 1.0) < 1e-5
