import pytest
from unittest.mock import MagicMock, patch
import models
import config

# Mock the logger to prevent actual logging during tests
class MockLogger:
    def info(self, message):
        pass
    def warning(self, message):
        pass
    def error(self, message, exc_info=False):
        pass

@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch('models.log', new=MockLogger())

@pytest.fixture
def mock_speechbrain_encoder_classifier(mocker):
    """SpeechBrain EncoderClassifier를 모의(mock)합니다."""
    mock_classifier = MagicMock()
    mocker.patch('speechbrain.inference.speaker.EncoderClassifier.from_hparams', return_value=mock_classifier)
    return mock_classifier

@pytest.fixture
def mock_audio_separator(mocker):
    """Audio-Separator를 모의(mock)합니다."""
    mock_separator = MagicMock()
    mocker.patch('audio_separator.separator.Separator', return_value=mock_separator)
    return mock_separator

def test_load_speech_brain_model(mock_speechbrain_encoder_classifier):
    """SpeechBrain 모델 로딩 함수가 올바르게 호출되고 인스턴스를 반환하는지 테스트"""
    classifier = models.load_speech_brain_model()
    
    # from_hparams가 올바른 인자와 함께 호출되었는지 확인
    mock_speechbrain_encoder_classifier.from_hparams.assert_called_once_with(
        source=config.SPEECHBRAIN_MODEL_SOURCE,
        run_opts={"device": config.DEVICE},
        savedir=config.PRETRAINED_MODELS_DIR
    )
    # 반환된 객체가 모의 객체인지 확인
    assert classifier == mock_speechbrain_encoder_classifier.return_value

def test_load_audio_separator_model(mock_audio_separator):
    """Audio-Separator 모델 로딩 함수가 올바르게 호출되고 인스턴스를 반환하는지 테스트"""
    separator = models.load_audio_separator_model()
    
    # Separator 클래스가 호출되었는지 확인
    mock_audio_separator.assert_called_once()
    # load_model 메소드가 올바른 인자와 함께 호출되었는지 확인
    mock_audio_separator.return_value.load_model.assert_called_once_with(
        model_filename=config.AUDIO_SEPARATOR_MODEL
    )
    # 반환된 객체가 모의 객체인지 확인
    assert separator == mock_audio_separator.return_value

# config.py의 BASE_DIR을 위한 임시 mocking (실제 파일 시스템 접근 방지)
@pytest.fixture(autouse=True)
def mock_config_base_dir(mocker):
    mocker.patch('config.BASE_DIR', new='mock_base_dir')
    mocker.patch('config.INPUT_DIR', new='mock_base_dir/inputs')
    mocker.patch('config.DB_DIR', new='mock_base_dir/database')
    mocker.patch('config.PRETRAINED_MODELS_DIR', new='mock_base_dir/pretrained_models')
    mocker.patch('os.makedirs', return_value=None) # os.makedirs 호출 무시
