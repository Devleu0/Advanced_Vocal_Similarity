import pytest

from vocal_similarity import input_store, pipeline


@pytest.fixture
def steps(mocker):
    """processing / visualization 단계를 mock 하여 오케스트레이션만 검증합니다."""
    return {
        "download": mocker.patch("vocal_similarity.pipeline.download_original_audio", return_value=("tmp.webm", "raw.mp3")),
        "convert": mocker.patch("vocal_similarity.pipeline.convert_to_mp3", return_value="raw.mp3"),
        "process": mocker.patch("vocal_similarity.pipeline.process_audio"),
        "analyze": mocker.patch("vocal_similarity.pipeline.generate_and_visualize_similarity"),
        "exists": mocker.patch("vocal_similarity.pipeline.os.path.exists", return_value=True),
    }


def test_collect_tasks_filters_artists(tmp_path):
    input_store.write_urls(str(tmp_path), "A", ["u1", "u2"])
    input_store.write_urls(str(tmp_path), "B", ["u3"])

    assert [(t.artist_name, t.url) for t in pipeline.collect_tasks(str(tmp_path))] == [
        ("A", "u1"), ("A", "u2"), ("B", "u3")]
    assert [t.url for t in pipeline.collect_tasks(str(tmp_path), ["B"])] == ["u3"]


def test_run_pipeline_runs_all_stages_and_reports_progress(steps):
    tasks = [pipeline.Task("A", "u1"), pipeline.Task("B", "u2")]
    events = []
    pipeline.run_pipeline(tasks, classifier="clf", on_progress=lambda *e: events.append(e))

    assert steps["download"].call_count == 2
    assert steps["convert"].call_count == 2
    assert steps["process"].call_count == 2
    steps["process"].assert_any_call("raw.mp3", "clf", "A", "u1")
    steps["analyze"].assert_called_once()
    assert events[0] == ("download", 0, 2)
    assert ("process", 2, 2) in events
    assert events[-1] == ("analyze", 1, 1)


def test_failed_conversion_skips_processing(steps):
    steps["convert"].return_value = None
    pipeline.run_pipeline([pipeline.Task("A", "u1")], classifier=None)
    steps["process"].assert_not_called()


def test_already_converted_audio_is_processed(steps):
    """다운로드 단계가 (None, raw) 를 돌려주면(이전 실행의 MP3 재사용) 변환 없이 처리되어야 합니다."""
    steps["download"].return_value = (None, "raw.mp3")
    pipeline.run_pipeline([pipeline.Task("A", "u1")], classifier=None)
    steps["convert"].assert_not_called()
    steps["process"].assert_called_once()


def test_cancel_stops_before_next_task(steps):
    calls = {"n": 0}

    def should_cancel():
        calls["n"] += 1
        return calls["n"] > 1  # 첫 작업 이후 취소

    with pytest.raises(pipeline.PipelineCancelled):
        pipeline.run_pipeline([pipeline.Task("A", "u1"), pipeline.Task("A", "u2")],
                              classifier=None, should_cancel=should_cancel)
    assert steps["download"].call_count == 1
    steps["analyze"].assert_not_called()
