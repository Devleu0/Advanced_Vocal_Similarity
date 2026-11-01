import pytest
import torch

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from webapp.app import create_app  # noqa: E402

URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
URL_B = "https://youtu.be/bbbbbbbbbbb"


@pytest.fixture
def dirs(tmp_path, mocker):
    inputs, db = tmp_path / "inputs", tmp_path / "database"
    inputs.mkdir()
    db.mkdir()
    mocker.patch("config.INPUT_DIR", str(inputs))
    mocker.patch("config.DB_DIR", str(db))
    return inputs, db


@pytest.fixture
def runner_calls():
    return []


@pytest.fixture
def client(dirs, runner_calls):
    def fake_runner(artists, on_progress, should_cancel):
        runner_calls.append(artists)
        on_progress("analyze", 1, 1)

    return TestClient(create_app(runner=fake_runner))


def test_index_and_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    res = client.get("/")
    assert res.status_code == 200
    assert "Advanced Vocal Similarity" in res.text


def test_artist_crud_and_status(client, dirs):
    _, db = dirs
    res = client.put("/api/artists/아이유", json={"urls": [URL_A, URL_B, URL_A, " "]})
    assert res.status_code == 200
    body = res.json()
    assert [u["video_id"] for u in body["urls"]] == ["aaaaaaaaaaa", "bbbbbbbbbbb"]  # 중복/공백 제거
    assert {u["status"] for u in body["urls"]} == {"pending"}

    (db / "아이유").mkdir()
    torch.save(torch.randn(8), db / "아이유" / "emb_aaaaaaaaaaa.pt")
    (db / "아이유" / "raw_bbbbbbbbbbb.mp3").write_bytes(b"")

    [artist] = client.get("/api/artists").json()
    assert artist["embeddings"] == 1
    assert [u["status"] for u in artist["urls"]] == ["done", "downloaded"]

    assert client.delete("/api/artists/아이유?purge=true").status_code == 204
    assert client.get("/api/artists").json() == []
    assert not (db / "아이유").exists()
    assert client.delete("/api/artists/아이유").status_code == 404


def test_artist_validation(client):
    bad = ["https://example.com/nope", "https://example.com/not-youtube"]
    res = client.put("/api/artists/A", json={"urls": [URL_A, *bad]})
    assert res.status_code == 422
    assert res.json()["detail"]["invalid_urls"] == bad
    assert client.put("/api/artists/.hidden", json={"urls": []}).status_code == 422


def test_job_lifecycle(client, runner_calls):
    res = client.post("/api/jobs", json={"artists": ["A"]})
    assert res.status_code == 202
    job_id = res.json()["id"]
    client.app.state.job_manager.wait(job_id)

    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "succeeded"
    assert job["stage"] == "analyze"
    assert runner_calls == [["A"]]
    assert [j["id"] for j in client.get("/api/jobs").json()] == [job_id]
    assert client.get("/api/jobs/unknown").status_code == 404


def test_similarity_results(client, dirs):
    _, db = dirs
    assert client.get("/api/results/similarity").json() == {
        "artists": [], "matrix": [], "clustermap_available": False}
    assert client.get("/api/results/clustermap.png").status_code == 404

    base = torch.randn(16)
    for name, vec in [("A", base), ("B", base * 2), ("C", -base)]:
        (db / name).mkdir()
        torch.save(vec, db / name / "emb_x.pt")

    data = client.get("/api/results/similarity").json()
    assert data["artists"] == ["A", "B", "C"]
    m = data["matrix"]
    assert m[0][1] == pytest.approx(1.0, abs=1e-3)
    assert m[0][2] == pytest.approx(-1.0, abs=1e-3)

    csv = client.get("/api/results/similarity.csv")
    assert csv.status_code == 200
    assert csv.content.decode("utf-8-sig").splitlines()[0] == "artist,A,B,C"

    (db / "vocal_clustermap.png").write_bytes(b"\x89PNG")
    assert client.get("/api/results/clustermap.png").status_code == 200
    assert client.get("/api/results/similarity").json()["clustermap_available"] is True
