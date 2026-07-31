import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import torch
import torchaudio
import processing
import config
from logger import log # Mocked in fixture

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
    mocker.patch('processing.log', new=MockLogger())
    mocker.patch('utils.log', new=MockLogger()) # ensure utils.log is also mocked

@pytest.fixture(autouse=True)
def mock_config_paths(mocker):
    """config.py의 경로들을 모의(mock)하여 실제 파일 시스템 접근을 방지하고 테스트 환경에 맞춤"""
    mocker.patch('config.DB_DIR', new='mock_db_dir')
    mocker.patch('os.makedirs', return_value=None) # os.makedirs 호출 무시

@pytest.fixture
def mock_separator(mocker):
    """Audio Separator 인스턴스를 모의(mock)합니다."""
    mock_sep = MagicMock()
    mock_sep.separate.return_value = ("mock_vocal.mp3", "mock_instrumental.mp3") # 기본 반환값 설정
    return mock_sep

@pytest.fixture
def mock_classifier(mocker):
    """SpeechBrain Classifier 인스턴스를 모의(mock)합니다."""
    mock_cls = MagicMock()
    # encode_batch는 배치 처리 후 임베딩 텐서를 반환
    mock_cls.encode_batch.return_value = torch.randn(1, 1, 512) # 예시 임베딩 차원
    return mock_cls

@pytest.fixture
def mock_torchaudio_load(mocker):
    """torchaudio.load를 모의(mock)하여 가상의 waveform과 sample_rate를 반환합니다."""
    mock_waveform = torch.randn(1, config.SR * 10) # 10초 분량의 스테레오 오디오
    mocker.patch('torchaudio.load', return_value=(mock_waveform, config.SR))
    return mocker.patch('torchaudio.functional.resample') # resample 함수도 모킹

@pytest.fixture
def mock_yt_dlp(mocker):
    """yt_dlp.YoutubeDL을 모의(mock)하여 다운로드 과정을 스킵합니다."""
    mock_ydl = MagicMock()
    mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
    return mock_ydl

@pytest.fixture
def mock_os_path_exists(mocker):
    """os.path.exists를 모의(mock)하여 파일 존재 여부를 제어합니다."""
    return mocker.patch('os.path.exists', return_value=False)

@pytest.fixture
def mock_glob_glob(mocker):
    """glob.glob를 모의(mock)합니다."""
    return mocker.patch('glob.glob', return_value=[])


# --- Test Cases ---

def test_process_url_invalid_url(mock_separator, mock_classifier):
    """유효하지 않은 URL에 대해 오류를 로깅하고 일찍 종료하는지 테스트"""
    processing.process_url("invalid-url", "ArtistX", mock_separator, mock_classifier)
    assert mock_logger.error.called # 오류 로깅 확인

def test_process_url_skip_if_embedding_exists(mock_os_path_exists, mock_separator, mock_classifier):
    """최종 임베딩 파일이 이미 존재하면 처리를 스킵하는지 테스트"""
    mock_os_path_exists.side_effect = lambda path: path.endswith(".pt") # .pt 파일만 존재한다고 가정
    processing.process_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "ArtistX", mock_separator, mock_classifier)
    assert mock_logger.info.called # 스킵 로깅 확인
    mock_separator.separate.assert_not_called() # 분리 작업이 수행되지 않았는지 확인

def test_process_url_download_and_separate(
    mocker, mock_os_path_exists, mock_separator, mock_classifier, mock_torchaudio_load, mock_yt_dlp
):
    """다운로드 및 보컬 분리, 임베딩 추출 과정이 정상적으로 동작하는지 테스트"""
    video_id = "dQw4w9WgXcQ"
    url = f"https://www.youtube.com/watch?v={video_id}"
    artist_name = "ArtistX"
    artist_dir = os.path.join(config.DB_DIR, artist_name)
    raw_path = os.path.join(artist_dir, f"raw_{video_id}.mp3")
    vocal_path = os.path.join(artist_dir, f"vocal_{video_id}.mp3")
    emb_path = os.path.join(artist_dir, f"emb_{video_id}.pt")

    # 모든 파일이 존재하지 않는다고 가정
    mock_os_path_exists.side_effect = lambda path: False

    # yt_dlp 다운로드 성공 가정 (실제 파일 생성 대신)
    mock_yt_dlp.return_value.__enter__.return_value.download.return_value = None
    # raw_path가 생성되었다고 가정 (실제 파일 생성은 안 함)
    mocker.patch('os.path.exists', side_effect=lambda path: path == raw_path or path == vocal_path)
    mocker.patch('os.rename', return_value=None)
    mocker.patch('os.remove', return_value=None)
    mocker.patch('torch.save', return_value=None)

    processing.process_url(url, artist_name, mock_separator, mock_classifier)

    # yt_dlp 다운로드 호출 확인
    mock_yt_dlp.assert_called_once()
    # 분리 작업 호출 확인
    mock_separator.separate.assert_called_once()
    # torchaudio.load 호출 확인
    mock_torchaudio_load.assert_called_once()
    # classifier.encode_batch 호출 확인
    mock_classifier.encode_batch.assert_called_once()
    # torch.save 호출 확인
    torch.save.assert_called_once()
    assert mock_logger.info.called_with(f"  -> 최종 지문 저장 완료: {emb_path}")

def test_process_url_vocal_exists_skip_download(
    mocker, mock_os_path_exists, mock_separator, mock_classifier, mock_torchaudio_load, mock_yt_dlp
):
    """보컬 파일이 존재하면 다운로드/분리를 스킵하고 임베딩부터 시작하는지 테스트"""
    video_id = "dQw4w9WgXcQ"
    url = f"https://www.youtube.com/watch?v={video_id}"
    artist_name = "ArtistX"
    artist_dir = os.path.join(config.DB_DIR, artist_name)
    raw_path = os.path.join(artist_dir, f"raw_{video_id}.mp3")
    vocal_path = os.path.join(artist_dir, f"vocal_{video_id}.mp3")
    emb_path = os.path.join(artist_dir, f"emb_{video_id}.pt")

    # 보컬 파일만 존재한다고 가정
    mock_os_path_exists.side_effect = lambda path: path == vocal_path

    mocker.patch('torch.save', return_value=None)

    processing.process_url(url, artist_name, mock_separator, mock_classifier)

    mock_yt_dlp.assert_not_called() # 다운로드 스킵 확인
    mock_separator.separate.assert_not_called() # 분리 스킵 확인
    mock_torchaudio_load.assert_called_once() # 임베딩부터 시작 확인
    mock_classifier.encode_batch.assert_called_once()
    torch.save.assert_called_once()

def test_process_url_download_fail(
    mocker, mock_os_path_exists, mock_separator, mock_classifier, mock_yt_dlp
):
    """다운로드 실패 시 오류 로깅 후 종료하는지 테스트"""
    mock_os_path_exists.return_value = False
    mock_yt_dlp.return_value.__enter__.return_value.download.side_effect = Exception("Download Failed")
    
    processing.process_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "ArtistX", mock_separator, mock_classifier)
    assert mock_logger.error.called # 오류 로깅 확인
    mock_separator.separate.assert_not_called() # 분리 작업이 수행되지 않았는지 확인

def test_process_url_separation_fail(
    mocker, mock_os_path_exists, mock_separator, mock_classifier, mock_torchaudio_load, mock_yt_dlp
):
    """음원 분리 실패 시 오류 로깅 후 종료하는지 테스트"""
    video_id = "dQw4w9WgXcQ"
    url = f"https://www.youtube.com/watch?v={video_id}"
    artist_name = "ArtistX"
    artist_dir = os.path.join(config.DB_DIR, artist_name)
    raw_path = os.path.join(artist_dir, f"raw_{video_id}.mp3")

    mock_os_path_exists.side_effect = lambda path: path == raw_path # raw 파일만 존재
    mock_yt_dlp.return_value.__enter__.return_value.download.return_value = None
    mock_separator.separate.side_effect = Exception("Separation Failed")
    
    processing.process_url(url, artist_name, mock_separator, mock_classifier)
    assert mock_logger.error.called # 오류 로깅 확인
    mock_torchaudio_load.assert_not_called() # 임베딩 작업이 수행되지 않았는지 확인

def test_process_url_no_valid_chunks(
    mocker, mock_os_path_exists, mock_separator, mock_classifier, mock_torchaudio_load, mock_yt_dlp
):
    """유효한 오디오 청크가 없을 때 오류 로깅 후 종료하는지 테스트"""
    video_id = "dQw4w9WgXcQ"
    url = f"https://www.youtube.com/watch?v={video_id}"
    artist_name = "ArtistX"
    artist_dir = os.path.join(config.DB_DIR, artist_name)
    raw_path = os.path.join(artist_dir, f"raw_{video_id}.mp3")
    vocal_path = os.path.join(artist_dir, f"vocal_{video_id}.mp3")

    mock_os_path_exists.side_effect = lambda path: path == vocal_path # 보컬 파일만 존재
    mock_yt_dlp.return_value.__enter__.return_value.download.return_value = None
    mocker.patch('torch.save', return_value=None)

    # torchaudio.load가 반환하는 waveform을 VAD 임계값을 통과하지 못하게 설정
    mock_waveform = torch.zeros(1, config.SR * 10) # 모든 값이 0인 waveform
    mocker.patch('torchaudio.load', return_value=(mock_waveform, config.SR))

    processing.process_url(url, artist_name, mock_separator, mock_classifier)
    assert mock_logger.warning.called # 경고 로깅 확인
    mock_classifier.encode_batch.assert_not_called() # 임베딩 작업이 수행되지 않았는지 확인

