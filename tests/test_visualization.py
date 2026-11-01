from unittest.mock import MagicMock

import pytest
import torch

from vocal_similarity import visualization


@pytest.fixture
def db(tmp_path, mocker):
    """임시 DB 디렉터리를 config.DB_DIR 로 사용합니다 (실제 파일 사용)."""
    mocker.patch('vocal_similarity.config.DB_DIR', str(tmp_path))
    return tmp_path


@pytest.fixture
def clustermap(mocker):
    return mocker.patch('vocal_similarity.visualization.sns.clustermap', return_value=MagicMock())


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
    assert (db / "top_similar_pairs.txt").exists()
    assert (db / "top_similar_pairs.csv").exists()
    clustermap.return_value.savefig.assert_called_once()


def test_run_outputs_are_archived_without_replacing_the_archive(db, clustermap):
    _add_artist(db, "A")
    _add_artist(db, "B")
    run_dir = db / "runs" / "20261101_142900_123456"
    run_dir.mkdir(parents=True)

    def save_figure(path, **kwargs):
        open(path, "wb").close()

    clustermap.return_value.savefig.side_effect = save_figure
    visualization.generate_and_visualize_similarity(str(run_dir))

    assert (run_dir / "similarity.json").exists()
    assert (run_dir / "vocal_similarities.txt").exists()
    assert (run_dir / "vocal_clustermap.png").exists()
    assert (run_dir / "top_similar_pairs.txt").exists()
    assert (run_dir / "top_similar_pairs.csv").exists()
    assert (db / "vocal_clustermap.png").exists()
    assert clustermap.return_value.savefig.call_count == 1


def test_top_similar_pairs_excludes_diagonal_and_limits_to_ten():
    profiles = {str(i): torch.randn(16) for i in range(6)}
    df = visualization.build_similarity_dataframe(profiles)

    pairs = visualization.top_similar_pairs(df)

    assert len(pairs) == 10
    assert all(pair["artist_a"] != pair["artist_b"] for pair in pairs)
    assert [pair["similarity"] for pair in pairs] == sorted(
        (pair["similarity"] for pair in pairs), reverse=True
    )


def test_corrupt_embedding_skips_that_artist(db, clustermap):
    _add_artist(db, "A")
    bad = db / "B"
    bad.mkdir()
    (bad / "emb_0.pt").write_bytes(b"not a tensor")
    visualization.generate_and_visualize_similarity()
    # 정상 아티스트가 1명뿐이므로 시각화되지 않아야 함
    clustermap.assert_not_called()
