import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import torch

import processing

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
VID = "dQw4w9WgXcQ"


@pytest.fixture(autouse=True)
def env(tmp_path, mocker):
    mocker.patch('config.DB_DIR', str(tmp_path))
    mocker.patch('config.DEVICE', 'cpu')
    mocker.patch('processing.log', new=MagicMock())
    return tmp_path


# ---------- download_original_audio ----------
def test_download_invalid_url():
    assert processing.download_original_audio("https://example.com", "A") == (None, None)


def test_download_skipped_when_raw_exists(env):
    artist = env / "A"
    artist.mkdir()
    raw = artist / f"raw_{VID}.mp3"
    raw.write_bytes(b"x")
    temp, raw_path = processing.download_original_audio(URL, "A")
    assert temp is None
    assert Path(raw_path) == raw


def test_download_success(mocker):
    def fake_run(cmd, **kwargs):
        out = cmd[cmd.index('-o') + 1].replace('%(ext)s', 'webm')
        Path(out).write_bytes(b"audio")
        return MagicMock(stdout="")

    run = mocker.patch('processing.subprocess.run', side_effect=fake_run)
    temp, raw = processing.download_original_audio(URL, "A")
    run.assert_called_once()
    assert temp.endswith(".webm")
    assert raw.endswith(f"raw_{VID}.mp3")


def test_download_failure_returns_none_temp(mocker):
    err = subprocess.CalledProcessError(1, "yt-dlp", stderr="boom")
    mocker.patch('processing.subprocess.run', side_effect=err)
    temp, raw = processing.download_original_audio(URL, "A")
    assert temp is None
    assert raw.endswith(f"raw_{VID}.mp3")


# ---------- convert_to_mp3 ----------
def test_convert_no_temp_file():
    assert processing.convert_to_mp3(None, "x.mp3") is None


def test_convert_skips_and_cleans_temp_when_raw_exists(env):
    temp = env / "t.webm"
    raw = env / "r.mp3"
    temp.write_bytes(b"x")
    raw.write_bytes(b"x")
    assert processing.convert_to_mp3(str(temp), str(raw)) == str(raw)
    assert not temp.exists()


def test_convert_runs_ffmpeg(env, mocker):
    temp = env / "t.webm"
    temp.write_bytes(b"x")
    run = mocker.patch('processing.subprocess.run')
    raw = str(env / "r.mp3")
    assert processing.convert_to_mp3(str(temp), raw) == raw
    cmd = run.call_args.args[0]
    assert cmd[0] == 'ffmpeg' and raw in cmd


def test_convert_ffmpeg_failure(env, mocker):
    temp = env / "t.webm"
    temp.write_bytes(b"x")
    mocker.patch('processing.subprocess.run',
                 side_effect=subprocess.CalledProcessError(1, "ffmpeg", stderr="e"))
    assert processing.convert_to_mp3(str(temp), str(env / "r.mp3")) is None


# ---------- process_audio ----------
def _prepare_vocal(env):
    artist = env / "A"
    artist.mkdir()
    raw = artist / f"raw_{VID}.mp3"
    raw.write_bytes(b"x")
    (artist / f"vocal_{VID}.mp3").write_bytes(b"x")
    return artist, raw


def test_process_missing_raw_does_nothing(env):
    classifier = MagicMock()
    processing.process_audio(str(env / "nope.mp3"), classifier, "A", URL)
    classifier.encode_batch.assert_not_called()


def test_process_skips_when_embedding_exists(env):
    artist, raw = _prepare_vocal(env)
    (artist / f"emb_{VID}.pt").write_bytes(b"x")
    classifier = MagicMock()
    processing.process_audio(str(raw), classifier, "A", URL)
    classifier.encode_batch.assert_not_called()


def test_process_extracts_and_saves_embedding(env, mocker):
    artist, raw = _prepare_vocal(env)
    mocker.patch('processing.torchaudio.load',
                 return_value=(torch.randn(1, 16000 * 10), 16000))
    classifier = MagicMock()
    classifier.encode_batch.return_value = torch.randn(2, 1, 8)

    processing.process_audio(str(raw), classifier, "A", URL)

    emb = torch.load(artist / f"emb_{VID}.pt", weights_only=True)
    assert emb.shape == (8,)


def test_process_silent_audio_saves_nothing(env, mocker):
    artist, raw = _prepare_vocal(env)
    mocker.patch('processing.torchaudio.load',
                 return_value=(torch.zeros(1, 16000 * 10), 16000))
    classifier = MagicMock()
    processing.process_audio(str(raw), classifier, "A", URL)
    classifier.encode_batch.assert_not_called()
    assert not (artist / f"emb_{VID}.pt").exists()
