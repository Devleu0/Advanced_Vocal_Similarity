import pytest
import torch
from unittest.mock import MagicMock
import visualization


@pytest.fixture
def db(tmp_path, mocker):
    """임시 DB 디렉터리를 config.DB_DIR 로 사용합니다 (실제 파일 사용)."""
    mocker.patch('config.DB_DIR', str(tmp_path))
    return tmp_path


@pytest.fixture
def clustermap(mocker):
    return mocker.patch('visualization.sns.clustermap', return_value=MagicMock())


def _add_artist(db, name, n_embs=1):
    d = db / name
    d.mkdir()
    for i in range(n_embs):
        torch.save(torch.randn(16), d / f"emb_{i}.pt")
    return d


def test_no_artists_skips_visualization(db, clustermap):
    visualization.generate_and_visualize_similarity()
    clustermap.assert_not_called()


def test_single_artist_skips_visualization(db, clustermap):
    _add_artist(db, "A")
    visualization.generate_and_visualize_similarity()
    clustermap.assert_not_called()


def test_two_artists_writes_outputs(db, clustermap):
    _add_artist(db, "A", 2)
    _add_artist(db, "B")
    visualization.generate_and_visualize_similarity()

    clustermap.assert_called_once()
    df = clustermap.call_args.args[0]
    assert list(df.index) == list(df.columns)
    assert set(df.index) == {"A", "B"}
    assert (db / "vocal_similarities.txt").exists()
    clustermap.return_value.savefig.assert_called_once()


def test_corrupt_embedding_skips_that_artist(db, clustermap):
    _add_artist(db, "A")
    bad = db / "B"
    bad.mkdir()
    (bad / "emb_0.pt").write_bytes(b"not a tensor")
    visualization.generate_and_visualize_similarity()
    # 정상 아티스트가 1명뿐이므로 시각화되지 않아야 함
    clustermap.assert_not_called()
