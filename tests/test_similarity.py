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
