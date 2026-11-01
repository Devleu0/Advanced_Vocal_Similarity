import pytest

import input_store


def test_write_and_list_roundtrip(tmp_path):
    input_store.write_urls(str(tmp_path), "아이유", [" https://youtu.be/aaaaaaaaaaa ", "", "https://youtu.be/bbbbbbbbbbb"])
    input_store.write_urls(str(tmp_path), "B", [])
    (tmp_path / "notes.md").write_text("ignored")

    artists = input_store.list_artists(str(tmp_path))
    assert list(artists) == ["B", "아이유"]
    assert artists["아이유"] == ["https://youtu.be/aaaaaaaaaaa", "https://youtu.be/bbbbbbbbbbb"]
    assert artists["B"] == []


def test_list_missing_dir_returns_empty(tmp_path):
    assert input_store.list_artists(str(tmp_path / "nope")) == {}


@pytest.mark.parametrize("name", ["", "   ", "../evil", "a/b", "a\\b", ".hidden", "..", "x" * 65])
def test_invalid_names_rejected(name):
    with pytest.raises(input_store.InvalidArtistName):
        input_store.validate_artist_name(name)


@pytest.mark.parametrize("name", ["아이유", "artist_A", "New Jeans", "BTS-v.2"])
def test_valid_names_accepted(name):
    assert input_store.validate_artist_name(f" {name} ") == name


def test_delete_artist(tmp_path):
    input_store.write_urls(str(tmp_path), "A", ["u"])
    assert input_store.delete_artist(str(tmp_path), "A") is True
    assert input_store.delete_artist(str(tmp_path), "A") is False
