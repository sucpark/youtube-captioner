"""YouTube video/audio downloader using yt-dlp."""

import os
import re
import logging
import yt_dlp

logger = logging.getLogger(__name__)


def get_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    match = re.search(r"(?<=v=)[a-zA-Z0-9_-]{11}", url)
    if match:
        return match.group(0)
    match = re.search(r"(?<=youtu.be/)[a-zA-Z0-9_-]{11}", url)
    if match:
        return match.group(0)
    raise ValueError(f"Invalid YouTube URL: {url}")


def fetch_video_info(youtube_url: str) -> dict:
    """Fetch video metadata without downloading."""
    logger.info(f"Fetching video metadata: {youtube_url}")
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            return {
                'title': info_dict.get('title', 'Unknown'),
                'channel': info_dict.get('channel', 'Unknown'),
                'duration': info_dict.get('duration', 0),
                'thumbnail': info_dict.get('thumbnail', ''),
            }
    except Exception as e:
        raise ValueError(f"Failed to fetch video info: {e}")


def download_youtube_audio(youtube_url: str, output_path: str, video_id: str) -> str:
    """Download audio from YouTube and convert to mp3."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, f'{video_id}.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting audio download...")
            ydl.download([youtube_url])
            filepath = os.path.join(output_path, f"{video_id}.mp3")
            if os.path.exists(filepath):
                logger.info(f"Audio download complete: {filepath}")
                return filepath
            raise ValueError("Audio file not found after download")
    except Exception as e:
        raise ValueError(f"Audio download failed: {e}")


def download_youtube_video(youtube_url: str, output_path: str, video_id: str, quality: str = 'high') -> str:
    """Download video from YouTube."""
    quality_formats = {
        'high': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'medium': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'low': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    if quality not in quality_formats:
        raise ValueError(f"Invalid quality: {quality}. Use 'high', 'medium', or 'low'")

    ydl_opts = {
        'format': quality_formats[quality],
        'outtmpl': os.path.join(output_path, f'{video_id}.mp4'),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Starting {quality} quality video download...")
            ydl.download([youtube_url])
            filepath = os.path.join(output_path, f"{video_id}.mp4")
            if os.path.exists(filepath):
                logger.info(f"Video download complete: {filepath}")
                return filepath
            raise ValueError("Video file not found after download")
    except Exception as e:
        raise ValueError(f"Video download failed: {e}")
