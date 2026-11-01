from unittest.mock import MagicMock

import pytest

from vocal_similarity import config, models


@pytest.fixture
def mock_from_hparams(mocker):
    """SpeechBrain EncoderClassifier.from_hparams 를 모의(mock)합니다."""
    mocker.patch('vocal_similarity.models.log', new=MagicMock())
    return mocker.patch.object(
        models.EncoderClassifier, 'from_hparams', return_value=MagicMock()
    )


def test_load_speech_brain_model(mock_from_hparams):
    """from_hparams 가 config 값과 함께 호출되고 그 결과를 반환하는지 테스트"""
    classifier = models.load_speech_brain_model()

    mock_from_hparams.assert_called_once_with(
        source=config.SPEECHBRAIN_MODEL_SOURCE,
        run_opts={"device": config.DEVICE},
        savedir=config.PRETRAINED_MODELS_DIR,
    )
    assert classifier is mock_from_hparams.return_value
