"""음성 지문(fingerprint) 추출용 순수 함수 모음.

config 나 파일 시스템에 의존하지 않고 인자로만 동작하므로 단위 테스트가 쉽습니다.
"""
import torch


def prepare_waveform(waveform, sr, target_sr, resample_fn=None):
    """리샘플링 → 모노 변환 → 피크 정규화를 수행합니다. 입력 shape: (channels, samples)."""
    if sr != target_sr:
        if resample_fn is None:
            import torchaudio
            resample_fn = torchaudio.functional.resample
        waveform = resample_fn(waveform, orig_freq=sr, new_freq=target_sr)
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)
    return waveform / (waveform.abs().max() + 1e-8)


def split_into_chunks(waveform, sr, chunk_sec, min_tail_sec=1):
    """파형을 chunk_sec 단위로 자르고, min_tail_sec 보다 짧은 마지막 조각은 버립니다."""
    chunks = list(torch.split(waveform, sr * chunk_sec, dim=1))
    if chunks and chunks[-1].shape[1] < sr * min_tail_sec:
        chunks = chunks[:-1]
    return chunks


def filter_silent_chunks(chunks, rms_threshold):
    """RMS 가 임계값 미만인 (무음) 청크를 제거합니다."""
    return [c for c in chunks if torch.sqrt(torch.mean(c ** 2)) >= rms_threshold]


def encode_chunks(chunks, classifier, device="cpu"):
    """청크들을 배치로 임베딩하여 (N, D) 텐서를 반환합니다."""
    batch = torch.stack(chunks).squeeze(1).to(device)
    with torch.no_grad():
        embs = classifier.encode_batch(batch).squeeze().cpu()
    if embs.dim() == 1:
        embs = embs.unsqueeze(0)
    return embs


def aggregate_embeddings(embs, use_outlier_removal=True, top_k_ratio=0.8):
    """(N, D) 임베딩을 하나의 (D,) 벡터로 합칩니다.

    use_outlier_removal 이면 평균 임베딩과 코사인 유사도가 높은 상위 top_k_ratio 만 평균합니다.
    Returns: (final_embedding, kept_count)
    """
    if use_outlier_removal:
        mean_emb = embs.mean(dim=0, keepdim=True)
        sims = torch.nn.functional.cosine_similarity(embs, mean_emb)
        k = max(1, int(top_k_ratio * len(embs)))
        idx = torch.topk(sims, k).indices
        return embs[idx].mean(dim=0), k
    return embs.mean(dim=0), len(embs)
