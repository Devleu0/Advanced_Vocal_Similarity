from speechbrain.inference.speaker import EncoderClassifier
import config
from logger import log

def load_speech_brain_model():
    """SpeechBrain ECAPA-TDNN 모델을 로드합니다."""
    log.info("[*] SpeechBrain 모델 로딩 중...")
    classifier = EncoderClassifier.from_hparams(
        source=config.SPEECHBRAIN_MODEL_SOURCE,
        run_opts={"device": config.DEVICE},
        savedir=config.PRETRAINED_MODELS_DIR
    )
    return classifier
