"""화자 임베딩 모델 레지스트리와 로더.

모든 인코더는 ``encode_batch(wavs, wav_lens) -> (B, D) 또는 (B, 1, D)`` 를 제공합니다.
새 모델을 추가하려면 EMBEDDING_MODELS 에 ModelSpec 을 등록하세요.
"""
import os
from dataclasses import dataclass

import torch

import config
from logger import log


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    backend: str          # "speechbrain" | "hf-xvector"
    source: str
    description: str = ""
    recommended: bool = False
    default: bool = False


EMBEDDING_MODELS = {
    "ecapa": ModelSpec(
        "ecapa", "ECAPA-TDNN (VoxCeleb)", "speechbrain",
        "speechbrain/spkrec-ecapa-voxceleb",
        "기존 기본 모델. 가볍고 빠름. 말소리 위주로 학습됨.", default=True,
    ),
    "wavlm-sv": ModelSpec(
        "wavlm-sv", "WavLM-base-plus-SV", "hf-xvector",
        "microsoft/wavlm-base-plus-sv",
        "자기지도 사전학습(SSL) 기반 화자 모델. 노래처럼 말소리와 다른 음성에 더 강건할 것으로 "
        "기대되어 추천. (transformers 필요, 실제 데이터에서는 evaluate.py 로 검증 권장)",
        recommended=True,
    ),
    "resnet": ModelSpec(
        "resnet", "ResNet-TDNN (VoxCeleb)", "speechbrain",
        "speechbrain/spkrec-resnet-voxceleb",
        "SpeechBrain 의 ResNet 기반 화자 모델. ECAPA 대안.",
    ),
}


def get_spec(name=None):
    name = name or config.EMBEDDING_MODEL
    if name not in EMBEDDING_MODELS:
        raise ValueError(
            f"알 수 없는 임베딩 모델 '{name}'. 선택 가능: {', '.join(EMBEDDING_MODELS)}"
        )
    return EMBEDDING_MODELS[name]


def format_model_list():
    """사용자에게 보여줄 모델 목록 (추천/기본 표시 포함)."""
    lines = []
    for spec in EMBEDDING_MODELS.values():
        tags = [t for t, on in (("추천", spec.recommended), ("기본", spec.default)) if on]
        tag = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"  {spec.key:<9s} {spec.label}{tag}\n            {spec.description}")
    return "\n".join(lines)


class HFXVectorEncoder:
    """HuggingFace ``*ForXVector`` 모델(WavLM-SV 등)을 speechbrain 스타일 인터페이스로 감쌉니다."""

    def __init__(self, source=None, device="cpu", model=None):
        if model is None:
            try:
                from transformers import WavLMForXVector
            except ImportError as e:
                raise ImportError(
                    "이 모델은 transformers 가 필요합니다: pip install transformers"
                ) from e
            model = WavLMForXVector.from_pretrained(source)
        self.device = device
        self.model = model.to(device).eval()

    def encode_batch(self, wavs, wav_lens=None):
        batch, total = wavs.shape
        if wav_lens is None:
            wav_lens = torch.ones(batch)
        lengths = (wav_lens.cpu() * total).round().long().clamp(min=1)
        x = torch.zeros(batch, total)
        for i, n in enumerate(lengths.tolist()):
            seg = wavs[i, :n].cpu()
            x[i, :n] = (seg - seg.mean()) / (seg.std() + 1e-7)  # 모델 학습 시 전처리와 동일
        mask = (torch.arange(total)[None, :] < lengths[:, None]).long()
        with torch.no_grad():
            out = self.model(input_values=x.to(self.device), attention_mask=mask.to(self.device))
        return out.embeddings


def _load_speechbrain(source, savedir):
    from speechbrain.inference.speaker import EncoderClassifier
    return EncoderClassifier.from_hparams(
        source=source, run_opts={"device": config.DEVICE}, savedir=savedir
    )


def load_speech_brain_model():
    """(하위 호환) 기본 ECAPA-TDNN 을 로드합니다."""
    log.info("[*] SpeechBrain 모델 로딩 중...")
    return _load_speechbrain(config.SPEECHBRAIN_MODEL_SOURCE, config.PRETRAINED_MODELS_DIR)


def load_embedding_model(name=None):
    """config.EMBEDDING_MODEL (또는 name) 에 해당하는 인코더를 로드합니다."""
    spec = get_spec(name)
    log.info(f"[*] 임베딩 모델 로딩 중: {spec.label} ({spec.source})")
    if spec.backend == "speechbrain":
        if spec.key == "ecapa":
            return load_speech_brain_model()
        return _load_speechbrain(spec.source, os.path.join(config.PRETRAINED_MODELS_DIR, spec.key))
    if spec.backend == "hf-xvector":
        return HFXVectorEncoder(spec.source, device=config.DEVICE)
    raise ValueError(f"지원하지 않는 backend: {spec.backend}")
