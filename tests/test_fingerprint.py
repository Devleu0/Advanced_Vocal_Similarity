from unittest.mock import MagicMock

import torch

from vocal_similarity import fingerprint as fp


def test_prepare_waveform_mono_and_peak_normalized():
    wav = torch.stack([torch.full((100,), 0.5), torch.full((100,), 0.25)])
    out = fp.prepare_waveform(wav, 16000, 16000)
    assert out.shape == (1, 100)
    assert abs(out.abs().max().item() - 1.0) < 1e-4


def test_prepare_waveform_resamples_when_sr_differs():
    resample = MagicMock(side_effect=lambda w, orig_freq, new_freq: w)
    fp.prepare_waveform(torch.ones(1, 10), 44100, 16000, resample_fn=resample)
    resample.assert_called_once()


def test_split_drops_short_tail():
    wav = torch.ones(1, 16000 * 5 + 8000)  # 5.5s, chunk 5s -> 꼬리 0.5s 제거
    assert len(fp.split_into_chunks(wav, 16000, 5)) == 1


def test_split_keeps_long_tail():
    wav = torch.ones(1, 16000 * 5 + 32000)  # 꼬리 2s 유지
    assert len(fp.split_into_chunks(wav, 16000, 5)) == 2


def test_filter_silent_chunks():
    chunks = [torch.zeros(1, 100), torch.ones(1, 100)]
    assert len(fp.filter_silent_chunks(chunks, 0.01)) == 1


def test_encode_chunks_single_chunk_is_2d():
    clf = MagicMock()
    clf.encode_batch.return_value = torch.randn(1, 1, 8)
    assert fp.encode_chunks([torch.randn(1, 100)], clf).shape == (1, 8)


def test_aggregate_without_outlier_removal_is_mean():
    embs = torch.tensor([[1.0, 0.0], [3.0, 0.0]])
    out, kept = fp.aggregate_embeddings(embs, use_outlier_removal=False)
    assert torch.allclose(out, torch.tensor([2.0, 0.0]))
    assert kept == 2


def test_aggregate_removes_outlier():
    embs = torch.tensor([[1.0, 0.0]] * 4 + [[-1.0, 0.0]])
    out, kept = fp.aggregate_embeddings(embs, True, 0.8)
    assert kept == 4
    assert torch.allclose(out, torch.tensor([1.0, 0.0]))


def test_aggregate_keeps_at_least_one():
    _, kept = fp.aggregate_embeddings(torch.randn(1, 4), True, 0.1)
    assert kept == 1
