import pytest
import torch
from unittest.mock import MagicMock

import config
import models


@pytest.fixture(autouse=True)
def quiet(mocker):
    mocker.patch('models.log', new=MagicMock())


def test_registry_has_one_default_and_a_recommended():
    specs = models.EMBEDDING_MODELS.values()
    assert sum(s.default for s in specs) == 1
    assert any(s.recommended for s in specs)


def test_model_list_marks_recommended_and_default():
    text = models.format_model_list()
    assert "[추천]" in text and "[기본]" in text
    for key in models.EMBEDDING_MODELS:
        assert key in text


def test_get_spec_rejects_unknown():
    with pytest.raises(ValueError):
        models.get_spec("nope")


def test_load_ecapa_uses_config_source(mocker):
    fh = mocker.patch(
        'speechbrain.inference.speaker.EncoderClassifier.from_hparams',
        return_value=MagicMock(),
    )
    clf = models.load_embedding_model("ecapa")
    fh.assert_called_once_with(
        source=config.SPEECHBRAIN_MODEL_SOURCE,
        run_opts={"device": config.DEVICE},
        savedir=config.PRETRAINED_MODELS_DIR,
    )
    assert clf is fh.return_value


def test_load_resnet_uses_own_savedir(mocker):
    fh = mocker.patch(
        'speechbrain.inference.speaker.EncoderClassifier.from_hparams',
        return_value=MagicMock(),
    )
    models.load_embedding_model("resnet")
    kwargs = fh.call_args.kwargs
    assert kwargs["source"] == "speechbrain/spkrec-resnet-voxceleb"
    assert kwargs["savedir"].endswith("resnet")


def test_hf_encoder_masks_padding_and_normalizes():
    seen = {}

    def fake_model(input_values, attention_mask):
        seen["x"], seen["mask"] = input_values, attention_mask
        return MagicMock(embeddings=torch.ones(input_values.shape[0], 4))

    fake = MagicMock(side_effect=fake_model)
    fake.to.return_value = fake
    fake.eval.return_value = fake
    enc = models.HFXVectorEncoder(model=fake)

    wavs = torch.zeros(2, 100)
    wavs[0] = torch.randn(100)
    wavs[1, :50] = torch.randn(50)
    out = enc.encode_batch(wavs, torch.tensor([1.0, 0.5]))

    assert out.shape == (2, 4)
    assert seen["mask"].sum(dim=1).tolist() == [100, 50]
    assert torch.all(seen["x"][1, 50:] == 0)
    assert abs(seen["x"][0].mean().item()) < 1e-4
