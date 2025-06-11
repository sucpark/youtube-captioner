# tests/test_downloader.py

import pytest
import os
from unittest.mock import patch, MagicMock

# 테스트 대상 함수 임포트
from src.modules.downloader import download_youtube_audio

# 성공적인 다운로드를 시뮬레이션하는 가짜 info_dict
FAKE_INFO_DICT = {
    'id': 'test_video_id',
    'title': 'Test Video Title',
}

@pytest.fixture
def tmp_output_path(tmp_path):
    """테스트를 위한 임시 출력 디렉터리를 생성하는 Fixture"""
    return tmp_path

# yt_dlp.YoutubeDL 클래스를 모킹(가짜로 대체)
@patch('yt_dlp.YoutubeDL')
def test_download_success(mock_youtube_dl, tmp_output_path):
    """유튜브 오디오 다운로드 성공 케이스를 테스트합니다."""
    # 가짜 YoutubeDL 객체가 반환할 내용 설정
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = FAKE_INFO_DICT
    # with 구문이 mock_instance를 반환하도록 설정
    mock_youtube_dl.return_value.__enter__.return_value = mock_instance

    # 다운로드될 가짜 파일 생성 (실제 다운로드는 일어나지 않음)
    fake_id = FAKE_INFO_DICT['id']
    expected_filepath = os.path.join(tmp_output_path, f"{fake_id}.mp3")
    # 빈 파일을 생성하여 os.path.exists()가 True를 반환하도록 함
    open(expected_filepath, 'a').close()

    # 테스트 함수 실행
    filepath, title = download_youtube_audio("https://www.youtube.com/watch?v=test_video_id", tmp_output_path)

    # 결과 검증
    assert filepath == expected_filepath
    assert title == FAKE_INFO_DICT['title']
    # ydl.extract_info가 올바른 인자와 함께 호출되었는지 확인
    mock_instance.extract_info.assert_called_with("https://www.youtube.com/watch?v=test_video_id", download=True)

def test_invalid_url(tmp_output_path):
    """유효하지 않은 URL에 대해 ValueError를 발생시키는지 테스트합니다."""
    # pytest.raises 문맥 안에서 특정 에러가 발생하는지 확인
    with pytest.raises(ValueError, match="유효하지 않은 YouTube URL입니다"):
        download_youtube_audio("this is not a valid url", tmp_output_path)