# utils/audio.py
# WAV 파일 처리 유틸리티

import wave
import os


def get_wav_duration_ms(wav_path: str) -> int:
    """WAV 파일 길이(밀리초) 반환"""
    try:
        with wave.open(wav_path, 'r') as w:
            frames = w.getnframes()
            rate = w.getframerate()
            return int((frames / rate) * 1000)
    except Exception:
        return 0


def get_wav_info(wav_path: str) -> dict:
    """WAV 파일 정보 반환"""
    try:
        with wave.open(wav_path, 'r') as w:
            return {
                'duration_ms': int((w.getnframes() / w.getframerate()) * 1000),
                'sample_rate': w.getframerate(),
                'channels': w.getnchannels(),
                'sample_width': w.getsampwidth(),
                'frames': w.getnframes()
            }
    except Exception:
        return {
            'duration_ms': 0,
            'sample_rate': 48000,
            'channels': 1,
            'sample_width': 2,
            'frames': 0
        }


def get_wav_sample_rate(wav_path: str) -> int:
    """WAV 파일 샘플레이트 반환"""
    try:
        with wave.open(wav_path, 'r') as w:
            return w.getframerate()
    except Exception:
        return 48000


def is_valid_wav(wav_path: str) -> bool:
    """유효한 WAV 파일인지 확인"""
    if not os.path.exists(wav_path):
        return False
    if os.path.getsize(wav_path) == 0:
        return False
    try:
        with wave.open(wav_path, 'r') as w:
            return w.getnframes() > 0
    except Exception:
        return False
