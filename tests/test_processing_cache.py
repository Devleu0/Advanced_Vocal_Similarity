from unittest.mock import MagicMock

import pytest
import torch

import cache
import config
import processing

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
VID = "dQw4w9WgXcQ"


@pytest.fixture(autouse=True)
def env(tmp_path, mocker):
    mocker.patch('config.DB_DIR', str(tmp_path))
    mocker.patch('config.DEVICE', 'cpu')
    mocker.patch('processing.log', new=MagicMock())
    artist = tmp_path / "A"
    artist.mkdir()
    (artist / f"raw_{VID}.mp3").write_bytes(b"x")
    (artist / f"vocal_{VID}.mp3").write_bytes(b"x")
    return artist


def _run(artist, mocker, classifier=None, **kw):
    mocker.patch('processing.torchaudio.load', return_value=(torch.randn(1, 16000 * 10), 16000))
    classifier = classifier or MagicMock()
    classifier.encode_batch.return_value = torch.randn(2, 1, 8)
    processing.process_audio(str(artist / f"raw_{VID}.mp3"), classifier, "A", URL, **kw)
    return classifier


def test_second_run_with_same_settings_is_skipped(env, mocker):
    first = _run(env, mocker)
    assert first.encode_batch.call_count == 1
    assert cache.is_fresh(str(env / f"emb_{VID}.pt"), processing.aggregation_settings("ecapa"))
    second = _run(env, mocker)
    second.encode_batch.assert_not_called()


def test_changing_aggregation_reuses_chunk_cache(env, mocker):
    _run(env, mocker)
    mocker.patch('config.EMB_TOP_K_RATIO', 0.5)
    again = _run(env, mocker)
    again.encode_batch.assert_not_called()          # 모델 추론 없이
    assert cache.is_fresh(str(env / f"emb_{VID}.pt"), processing.aggregation_settings("ecapa"))


def test_changing_extraction_settings_recomputes(env, mocker):
    _run(env, mocker)
    mocker.patch('config.CHUNK_SEC', 3)
    again = _run(env, mocker)
    assert again.encode_batch.call_count == 1


def test_models_are_stored_separately(env, mocker):
    _run(env, mocker, model="ecapa")
    _run(env, mocker, model="wavlm-sv")
    assert (env / f"emb_{VID}.pt").exists()
    assert (env / f"emb_wavlm-sv_{VID}.pt").exists()
    assert config.EMBEDDING_MODEL == "ecapa"


def test_vocal_is_reseparated_when_demucs_settings_change(env, mocker):
    cache.write_meta(str(env / f"vocal_{VID}.mp3"), {"demucs_model": "old", "demucs_shifts": None})
    sep = mocker.patch('processing._separate_vocals', return_value=False)
    _run(env, mocker)
    sep.assert_called_once()


def test_legacy_vocal_without_meta_is_reused(env, mocker):
    sep = mocker.patch('processing._separate_vocals', return_value=False)
    _run(env, mocker)
    sep.assert_not_called()
