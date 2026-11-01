import config
from embedding_store import embedding_path, list_embedding_files

MODELS = ["ecapa", "wavlm-sv", "resnet"]


def test_paths_default_is_legacy_name(tmp_path):
    assert embedding_path(str(tmp_path), "abc", "ecapa").endswith("emb_abc.pt")
    assert embedding_path(str(tmp_path), "abc", "wavlm-sv").endswith("emb_wavlm-sv_abc.pt")


def test_listing_separates_models(tmp_path):
    for name in ["emb_a.pt", "emb_b.pt", "emb_wavlm-sv_a.pt", "emb_resnet_a.pt"]:
        (tmp_path / name).write_bytes(b"x")

    def names(m):
        return [f.rsplit("/", 1)[-1] for f in list_embedding_files(str(tmp_path), m, MODELS)]

    assert names("ecapa") == ["emb_a.pt", "emb_b.pt"]
    assert names("wavlm-sv") == ["emb_wavlm-sv_a.pt"]
    assert names("resnet") == ["emb_resnet_a.pt"]


def test_default_model_is_ecapa():
    assert config.EMBEDDING_MODEL == "ecapa"
