import json

import pytest
import torch

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from vocal_similarity.webapp.app import create_app

URL_A = "https://www.youtube.com/watch?v=aaaaaaaaaaa"
URL_B = "https://youtu.be/bbbbbbbbbbb"


@pytest.fixture
def dirs(tmp_path, mocker):
    inputs, db = tmp_path / "inputs", tmp_path / "database"
    inputs.mkdir()
    db.mkdir()
    mocker.patch("vocal_similarity.config.INPUT_DIR", str(inputs))
    mocker.patch("vocal_similarity.config.DB_DIR", str(db))
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
    assert [u["media_id"] for u in body["urls"]] == ["aaaaaaaaaaa", "bbbbbbbbbbb"]  # 중복/공백 제거
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
    bad = ["file:///etc/passwd", "http://127.0.0.1/audio"]
    res = client.put("/api/artists/A", json={"urls": ["https://soundcloud.com/artist/track", *bad]})
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
    assert job["failure_logs"] == []
    assert job["stage"] == "analyze"
    assert runner_calls == [["A"]]
    assert [j["id"] for j in client.get("/api/jobs").json()] == [job_id]
    assert client.get("/api/jobs/unknown").status_code == 404


def test_similarity_results(client, dirs):
    _, db = dirs
    assert client.get("/api/results/similarity").json() == {
        "artists": [], "matrix": [], "top_pairs": [], "run_id": None,
        "clustermap_available": False}
    assert client.get("/api/results/clustermap.png").status_code == 404

    base = torch.randn(16)
    for name, vec in [("A", base), ("B", base * 2), ("C", -base)]:
        (db / name).mkdir()
        torch.save(vec, db / name / "emb_x.pt")

    data = client.get("/api/results/similarity").json()
    assert data["artists"] == ["A", "B", "C"]
    assert data["top_pairs"][0]["artist_a"] != data["top_pairs"][0]["artist_b"]
    m = data["matrix"]
    assert m[0][1] == pytest.approx(1.0, abs=1e-3)
    assert m[0][2] == pytest.approx(-1.0, abs=1e-3)
    assert client.get("/api/results/top-pairs.txt").status_code == 200

    csv = client.get("/api/results/similarity.csv")
    assert csv.status_code == 200
    assert csv.content.decode("utf-8-sig").splitlines()[0] == "artist,A,B,C"

    (db / "vocal_clustermap.png").write_bytes(b"\x89PNG")
    assert client.get("/api/results/clustermap.png").status_code == 200
    assert client.get("/api/results/similarity").json()["clustermap_available"] is True


def test_archived_run_results_and_reports(client, dirs):
    _, db = dirs
    run_id = "20261101_142900_123456"
    run_dir = db / "runs" / run_id
    run_dir.mkdir(parents=True)
    payload = {
        "run_id": run_id,
        "created_at": run_id,
        "artists": ["A", "B"],
        "matrix": [[1.0, 0.8], [0.8, 1.0]],
        "top_pairs": [{"artist_a": "A", "artist_b": "B", "similarity": 0.8}],
    }
    (run_dir / "similarity.json").write_text(json.dumps(payload), encoding="utf-8")
    (run_dir / "vocal_clustermap.png").write_bytes(b"\x89PNG")
    (run_dir / "top_similar_pairs.txt").write_text("Top pair", encoding="utf-8")

    assert client.get("/api/results/runs").json() == [{"id": run_id, "created_at": run_id}]
    assert client.get("/api/results/similarity").json()["run_id"] == run_id
    assert client.get(f"/api/results/similarity?run_id={run_id}").json()["top_pairs"] == payload["top_pairs"]
    assert client.get(f"/api/results/clustermap.png?run_id={run_id}").status_code == 200
    report = client.get(f"/api/results/top-pairs.txt?run_id={run_id}").text
    assert "A | B | 0.8000" in report
    csv = client.get(f"/api/results/top-pairs.csv?run_id={run_id}").content.decode("utf-8-sig")
    assert csv.splitlines() == ["rank,artist_a,artist_b,similarity", "1,A,B,0.8000"]
    assert client.get("/api/results/similarity?run_id=../../escape").status_code == 404
