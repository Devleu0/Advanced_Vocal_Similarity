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


def split_into_chunks(waveform, sr, chunk_sec, min_tail_sec=1, hop_sec=None):
    """파형을 chunk_sec 길이로 자릅니다.

    hop_sec 가 chunk_sec 보다 작으면 청크가 겹칩니다 (기본: 겹침 없음).
    마지막 남는 구간은 min_tail_sec 이상일 때만 (더 짧은) 꼬리 청크로 유지합니다.
    """
    size = int(sr * chunk_sec)
    hop = int(sr * (hop_sec or chunk_sec))
    total = waveform.shape[1]
    chunks, last_end, start = [], 0, 0
    while start + size <= total:
        chunks.append(waveform[:, start:start + size])
        last_end = start + size
        start += hop
    if total - last_end >= sr * min_tail_sec:
        chunks.append(waveform[:, last_end:])
    return chunks


def filter_silent_chunks(chunks, rms_threshold, relative_ratio=0.0):
    """무음 청크를 제거합니다.

    - rms_threshold: 절대 RMS 임계값
    - relative_ratio > 0: 파일 내 청크 RMS 의 90 백분위수 대비 비율 미만인 청크도 제거
      (보컬 분리 후 남는 반주 잔향/숨소리 구간 제거용)
    """
    if not chunks:
        return []
    rms = torch.stack([torch.sqrt(torch.mean(c ** 2)) for c in chunks])
    threshold = rms_threshold
    if relative_ratio > 0:
        threshold = max(threshold, relative_ratio * torch.quantile(rms, 0.9).item())
    return [c for c, r in zip(chunks, rms) if r >= threshold]


def filter_by_speech_ratio(chunks, ratio_fn, min_ratio):
    """ratio_fn(chunk) (발성 비율, 0~1) 이 min_ratio 이상인 청크만 남깁니다."""
    return [c for c in chunks if ratio_fn(c) >= min_ratio]


def make_silero_ratio_fn(sr):
    """Silero VAD 기반 발성 비율 함수를 만듭니다 (선택 기능, ``pip install silero-vad`` 필요)."""
    try:
        from silero_vad import get_speech_timestamps, load_silero_vad
    except ImportError as e:
        raise ImportError("Silero VAD 를 쓰려면: pip install silero-vad") from e
    model = load_silero_vad()

    def ratio(chunk):
        stamps = get_speech_timestamps(chunk[0], model, sampling_rate=sr)
        return sum(t["end"] - t["start"] for t in stamps) / max(1, chunk.shape[1])

    return ratio


def dominant_cluster(embs, split_cos=0.5, iters=10):
    """청크 임베딩(L2 정규화됨, (N, D))이 두 화자로 뚜렷이 갈리면 더 큰 군집의 인덱스를 반환합니다.

    듀엣/코러스/피처링 구간이 섞인 영상에서 메인 보컬 쪽만 쓰기 위한 휴리스틱입니다.
    두 군집 중심의 코사인 유사도가 split_cos 이상이면(=한 화자로 보임) 전체 인덱스를 반환합니다.
    """
    n = len(embs)
    everything = torch.arange(n)
    if n < 4:
        return everything
    mean = torch.nn.functional.normalize(embs.mean(dim=0), p=2, dim=0)
    first = embs[torch.argmin(embs @ mean)]
    second = embs[torch.argmin(embs @ first)]
    centers = torch.stack([first, second])
    for _ in range(iters):
        assign = torch.argmax(embs @ centers.T, dim=1)
        if len(assign.unique()) < 2:
            return everything
        centers = torch.stack([
            torch.nn.functional.normalize(embs[assign == k].mean(dim=0), p=2, dim=0)
            for k in range(2)
        ])
    if torch.dot(centers[0], centers[1]).item() >= split_cos:
        return everything
    sizes = torch.stack([(assign == k).sum() for k in range(2)])
    return everything[assign == torch.argmax(sizes)]


def encode_chunks(chunks, classifier, device="cpu", batch_size=32):
    """청크들을 배치로 임베딩하여 (N, D) 텐서를 반환합니다.

    길이가 다른 청크(꼬리 조각)는 0 으로 패딩하고 wav_lens 로 실제 길이를 알려 줍니다.
    (이전에는 길이가 다른 청크를 torch.stack 하다가 실패했습니다.)
    """
    outputs = []
    for i in range(0, len(chunks), batch_size):
        group = chunks[i:i + batch_size]
        lengths = torch.tensor([c.shape[1] for c in group])
        max_len = int(lengths.max())
        batch = torch.zeros(len(group), max_len)
        for j, c in enumerate(group):
            batch[j, :c.shape[1]] = c[0]
        wav_lens = (lengths.float() / max_len).to(device)
        with torch.no_grad():
            embs = classifier.encode_batch(batch.to(device), wav_lens)
        outputs.append(embs.reshape(len(group), -1).cpu())
    return torch.cat(outputs)


def aggregate_embeddings(embs, use_outlier_removal=True, top_k_ratio=0.8,
                         multi_speaker=False, split_cos=0.5):
    """(N, D) 임베딩을 하나의 L2 정규화된 (D,) 벡터로 합칩니다.

    각 청크 임베딩을 먼저 L2 정규화하여 노름이 큰 청크가 평균을 지배하지 않게 합니다.
    multi_speaker=True 이면 두 화자로 갈릴 때 더 큰 군집만 사용합니다 (dominant_cluster).
    use_outlier_removal 이면 평균 방향과 코사인 유사도가 높은 상위 top_k_ratio 만 사용합니다.
    Returns: (final_embedding, kept_count)
    """
    embs = torch.nn.functional.normalize(embs, p=2, dim=1)
    if multi_speaker:
        embs = embs[dominant_cluster(embs, split_cos)]
    if use_outlier_removal:
        mean_emb = embs.mean(dim=0, keepdim=True)
        sims = torch.nn.functional.cosine_similarity(embs, mean_emb)
        k = max(1, int(top_k_ratio * len(embs)))
        embs = embs[torch.topk(sims, k).indices]
    return torch.nn.functional.normalize(embs.mean(dim=0), p=2, dim=0), len(embs)
