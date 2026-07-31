from speechbrain.inference.speaker import EncoderClassifier
from audio_separator.separator import Separator
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

def load_audio_separator_model():
    """Audio-Separator(MDX-Net) 모델을 로드합니다."""
    log.info("[*] 음원 분리(MDX-Net) 모델 설정 중...")
    separator = Separator()
    separator.load_model(model_filename=config.AUDIO_SEPARATOR_MODEL)
    return separator
