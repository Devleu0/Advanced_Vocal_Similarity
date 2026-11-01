import torch
from unittest.mock import MagicMock

import fingerprint as fp


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
    wav = torch.ones(1, 16000 * 5 + 8000)  # 꼬리 0.5s 제거
    assert len(fp.split_into_chunks(wav, 16000, 5)) == 1


def test_split_keeps_long_tail_as_shorter_chunk():
    wav = torch.ones(1, 16000 * 5 + 32000)  # 꼬리 2s 유지
    chunks = fp.split_into_chunks(wav, 16000, 5)
    assert [c.shape[1] for c in chunks] == [80000, 32000]


def test_split_with_overlap():
    wav = torch.ones(1, 16000 * 10)
    chunks = fp.split_into_chunks(wav, 16000, 5, hop_sec=2.5)
    assert len(chunks) == 3  # 시작: 0, 2.5, 5
    assert all(c.shape[1] == 80000 for c in chunks)


def test_filter_silent_chunks_absolute():
    chunks = [torch.zeros(1, 100), torch.ones(1, 100)]
    assert len(fp.filter_silent_chunks(chunks, 0.01)) == 1


def test_filter_silent_chunks_relative():
    chunks = [torch.full((1, 100), v) for v in (1.0, 1.0, 1.0, 1.0, 0.05)]
    assert len(fp.filter_silent_chunks(chunks, 0.01)) == 5
    assert len(fp.filter_silent_chunks(chunks, 0.01, relative_ratio=0.1)) == 4


def test_filter_silent_chunks_empty():
    assert fp.filter_silent_chunks([], 0.01) == []


def test_encode_chunks_handles_unequal_lengths_and_batches():
    seen = []

    def fake_encode(batch, wav_lens):
        seen.append((tuple(batch.shape), wav_lens.tolist()))
        return torch.ones(batch.shape[0], 1, 4)

    clf = MagicMock()
    clf.encode_batch.side_effect = fake_encode
    chunks = [torch.randn(1, 100), torch.randn(1, 100), torch.randn(1, 50)]
    out = fp.encode_chunks(chunks, clf, batch_size=2)

    assert out.shape == (3, 4)
    assert seen[0] == ((2, 100), [1.0, 1.0])
    assert seen[1] == ((1, 50), [1.0])

    out = fp.encode_chunks(chunks, clf, batch_size=8)  # 한 배치: 패딩 + wav_lens
    assert seen[2] == ((3, 100), [1.0, 1.0, 0.5])
    assert out.shape == (3, 4)


def test_aggregate_without_outlier_removal_is_normalized_mean_direction():
    embs = torch.tensor([[1.0, 0.0], [3.0, 0.0]])
    out, kept = fp.aggregate_embeddings(embs, use_outlier_removal=False)
    assert torch.allclose(out, torch.tensor([1.0, 0.0]))
    assert kept == 2


def test_aggregate_normalizes_chunks_before_averaging():
    # 노름이 큰 청크가 평균을 지배하면 안 된다
    embs = torch.tensor([[100.0, 0.0], [0.0, 1.0]])
    out, _ = fp.aggregate_embeddings(embs, use_outlier_removal=False)
    assert torch.allclose(out, torch.tensor([2 ** -0.5, 2 ** -0.5]), atol=1e-5)


def test_aggregate_removes_outlier():
    embs = torch.tensor([[1.0, 0.0]] * 4 + [[-1.0, 0.0]])
    out, kept = fp.aggregate_embeddings(embs, True, 0.8)
    assert kept == 4
    assert torch.allclose(out, torch.tensor([1.0, 0.0]))


def test_aggregate_keeps_at_least_one():
    out, kept = fp.aggregate_embeddings(torch.randn(1, 4), True, 0.1)
    assert kept == 1
    assert abs(out.norm().item() - 1.0) < 1e-5
