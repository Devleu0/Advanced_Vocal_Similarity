import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import torch
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import visualization
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
    mocker.patch('visualization.log', new=MockLogger())

@pytest.fixture(autouse=True)
def mock_config_paths(mocker):
    """config.py의 경로들을 모의(mock)하여 실제 파일 시스템 접근을 방지하고 테스트 환경에 맞춤"""
    mocker.patch('config.DB_DIR', new='mock_db_dir')

@pytest.fixture
def mock_glob_glob(mocker):
    """glob.glob를 모의(mock)합니다."""
    return mocker.patch('glob.glob')

@pytest.fixture
def mock_torch_load(mocker):
    """torch.load를 모의(mock)합니다."""
    # 더미 임베딩 반환 (크기 512)
    return mocker.patch('torch.load', return_value=torch.randn(512))

@pytest.fixture
def mock_sns_clustermap(mocker):
    """seaborn.clustermap을 모의(mock)합니다."""
    mock_fig = MagicMock()
    mock_fig.fig.suptitle = MagicMock()
    mock_fig.savefig = MagicMock()
    return mocker.patch('seaborn.clustermap', return_value=mock_fig)

@pytest.fixture
def mock_plt_close(mocker):
    """matplotlib.pyplot.close를 모의(mock)합니다."""
    return mocker.patch('matplotlib.pyplot.close')

def test_generate_and_visualize_similarity_no_artists(
    mock_glob_glob, mock_sns_clustermap
):
    """아티스트 폴더가 없을 때 시각화가 실행되지 않고 경고를 로깅하는지 테스트"""
    mock_glob_glob.return_value = [] # 아티스트 폴더 없음
    visualization.generate_and_visualize_similarity()
    assert mock_logger.warning.called
    mock_sns_clustermap.assert_not_called()

def test_generate_and_visualize_similarity_less_than_two_artists(
    mock_glob_glob, mock_torch_load, mock_sns_clustermap, mocker
):
    """아티스트가 한 명일 때 시각화가 실행되지 않고 경고를 로깅하는지 테스트"""
    # 하나의 아티스트 폴더와 임베딩 파일이 있다고 가정
    mock_glob_glob.side_effect = [['mock_db_dir/ArtistA'], ['mock_db_dir/ArtistA/emb_video1.pt']]
    
    visualization.generate_and_visualize_similarity()
    assert mock_logger.warning.called
    mock_sns_clustermap.assert_not_called()

def test_generate_and_visualize_similarity_success(
    mock_glob_glob, mock_torch_load, mock_sns_clustermap, mock_plt_close, mocker
):
    """두 명 이상의 아티스트가 있을 때 시각화가 성공적으로 실행되는지 테스트"""
    # 두 개의 아티스트 폴더와 각각 임베딩 파일이 있다고 가정
    mock_glob_glob.side_effect = [
        ['mock_db_dir/ArtistA', 'mock_db_dir/ArtistB'], # artist_dirs
        ['mock_db_dir/ArtistA/emb_video1.pt'],         # ArtistA emb_files
        ['mock_db_dir/ArtistB/emb_video2.pt']          # ArtistB emb_files
    ]
    
    # torch.save는 사용되지 않지만, mock_open으로 파일 쓰기 모킹
    mocker.patch('builtins.open', mock_open())
    mocker.patch('pandas.DataFrame.to_string', return_value="mock_matrix_string")

    visualization.generate_and_visualize_similarity()

    # 로그 확인
    assert mock_logger.info.called_with("[*] [Step 5] 전체 마스터 프로필 생성 및 시각화 시작")
    assert mock_logger.info.called_with("  -> 텍스트 결과물 저장: mock_db_dir\vocal_similarities.txt")
    assert mock_logger.info.called_with("  -> 시각화 결과물 저장: mock_db_dir\vocal_clustermap.png")

    # Seaborn clustermap이 올바른 인자와 함께 호출되었는지 확인
    mock_sns_clustermap.assert_called_once()
    args, kwargs = mock_sns_clustermap.call_args
    assert isinstance(args[0], pd.DataFrame) # 첫 번째 인자는 DataFrame이어야 함
    assert kwargs['annot'] == True
    assert kwargs['cmap'] == 'mako'
    assert kwargs['vmin'] == 0.0
    assert kwargs['vmax'] == 1.0

    # 이미지 파일이 저장되었는지 확인
    mock_sns_clustermap.return_value.savefig.assert_called_once_with(
        os.path.join('mock_db_dir', "vocal_clustermap.png"), dpi=300, bbox_inches='tight'
    )
    # matplotlib.pyplot.close가 호출되었는지 확인
    mock_plt_close.assert_called_once_with('all')

def test_generate_and_visualize_similarity_profile_creation_failure(
    mock_glob_glob, mock_torch_load, mock_sns_clustermap, mocker
):
    """프로필 생성 중 에러 발생 시 오류를 로깅하고 해당 아티스트를 건너뛰는지 테스트"""
    # 두 개의 아티스트 폴더가 있지만, 한 아티스트의 임베딩 로딩에 실패한다고 가정
    mock_glob_glob.side_effect = [
        ['mock_db_dir/ArtistA', 'mock_db_dir/ArtistB'],
        ['mock_db_dir/ArtistA/emb_video1.pt'],
        ['mock_db_dir/ArtistB/emb_video2.pt']
    ]
    # ArtistA의 torch.load가 예외를 발생시키도록 설정
    mock_torch_load.side_effect = [Exception("Failed to load emb for ArtistA"), torch.randn(512)]
    
    visualization.generate_and_visualize_similarity()

    assert mock_logger.error.called # 오류 로깅 확인
    # ArtistB에 대한 처리는 계속 진행되어야 함 (경고 대신 에러이므로 시각화는 1명으로 불가)
    assert mock_logger.warning.called
    mock_sns_clustermap.assert_not_called()
