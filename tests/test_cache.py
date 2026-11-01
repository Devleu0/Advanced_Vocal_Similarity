import cache


def test_signature_is_order_independent_and_sensitive():
    assert cache.signature({"a": 1, "b": 2}) == cache.signature({"b": 2, "a": 1})
    assert cache.signature({"a": 1}) != cache.signature({"a": 2})


def test_is_fresh_lifecycle(tmp_path):
    f = tmp_path / "x.pt"
    settings = {"model": "ecapa", "chunk": 5}
    assert not cache.is_fresh(str(f), settings)           # 파일 없음

    f.write_bytes(b"x")
    assert not cache.is_fresh(str(f), settings)           # 메타 없음 → 오래된 것으로 간주
    assert cache.is_fresh(str(f), settings, allow_legacy=True)

    cache.write_meta(str(f), settings)
    assert cache.is_fresh(str(f), settings)
    assert not cache.is_fresh(str(f), {**settings, "chunk": 3})  # 설정 변경 → 무효


def test_corrupt_meta_is_treated_as_missing(tmp_path):
    f = tmp_path / "x.pt"
    f.write_bytes(b"x")
    (tmp_path / "x.pt.meta.json").write_text("{not json")
    assert not cache.is_fresh(str(f), {"a": 1})
