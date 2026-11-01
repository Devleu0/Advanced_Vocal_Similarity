import types

import pytest

import cli


def _cfg(**kw):
    base = dict(VAD_BACKEND="rms", ARTIST_SCORING="profile", SCORE_NORM=None,
                EMBEDDING_MODEL="ecapa", ENSEMBLE_MODELS=[], CHUNK_SEC=5, INPUT_DIR="in")
    base.update(kw)
    return types.SimpleNamespace(**base)


def test_parse_set_literals_and_strings():
    out = cli.parse_set(["CHUNK_SEC=3", "USE_VAD=False", "X=None", "NAME=abc", "L=['a','b']"])
    assert out == {"CHUNK_SEC": 3, "USE_VAD": False, "X": None, "NAME": "abc", "L": ["a", "b"]}


def test_parse_set_requires_equals():
    with pytest.raises(ValueError):
        cli.parse_set(["oops"])


def test_override_priority_preset_lt_flag_lt_set():
    merged = cli.build_overrides(
        "accurate", {"VAD_BACKEND": "rms", "DEVICE": None}, ["VAD_BACKEND='silero'", "DEMUCS_SHIFTS=3"]
    )
    assert merged["VAD_BACKEND"] == "silero"       # --set 이 최우선
    assert merged["DEMUCS_SHIFTS"] == 3
    assert merged["ENSEMBLE_MODELS"] == ["ecapa", "wavlm-sv"]  # 프리셋 값 유지
    assert "DEVICE" not in merged                   # None 은 무시


def test_unknown_preset_and_key():
    with pytest.raises(ValueError):
        cli.build_overrides("nope")
    with pytest.raises(ValueError):
        cli.apply_overrides(_cfg(), {"NO_SUCH_KEY": 1})


def test_apply_and_validate():
    cfg = _cfg()
    cli.apply_overrides(cfg, {"CHUNK_SEC": 3, "ENSEMBLE_MODELS": ["ecapa", "wavlm-sv"]})
    assert cfg.CHUNK_SEC == 3
    cli.validate(cfg, ["ecapa", "wavlm-sv", "resnet"])


@pytest.mark.parametrize("bad", [
    {"VAD_BACKEND": "x"}, {"ARTIST_SCORING": "x"}, {"SCORE_NORM": "x"},
    {"EMBEDDING_MODEL": "x"}, {"ENSEMBLE_MODELS": ["x"]},
])
def test_validate_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        cli.validate(_cfg(**bad), ["ecapa", "wavlm-sv"])


def test_parser_maps_flags():
    args = cli.build_parser(["ecapa", "wavlm-sv"]).parse_args(
        ["--ensemble", "ecapa,wavlm-sv", "--device", "cpu", "--set", "A=1", "--set", "B=2"]
    )
    explicit = cli.explicit_from_args(args)
    assert explicit["ENSEMBLE_MODELS"] == ["ecapa", "wavlm-sv"]
    assert explicit["DEVICE"] == "cpu" and explicit["EMBEDDING_MODEL"] is None
    assert args.set_pairs == ["A=1", "B=2"]


def test_presets_listed():
    text = cli.format_presets()
    for name in cli.PRESETS:
        assert name in text
