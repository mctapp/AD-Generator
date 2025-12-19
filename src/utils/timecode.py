# utils/timecode.py
# 타임코드 변환 유틸리티

def ms_to_timecode(ms: int, fps: float = 24) -> str:
    """밀리초를 타임코드(HH:MM:SS:FF)로 변환"""
    total_seconds = ms / 1000
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    f = int((total_seconds % 1) * fps)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def ms_to_filename_tc(ms: int, fps: float = 24) -> str:
    """밀리초를 파일명용 타임코드로 변환 (콜론→언더스코어)"""
    tc = ms_to_timecode(ms, fps)
    return tc.replace(':', '_')


def ms_to_frames(ms: int, fps: float = 24) -> int:
    """밀리초를 프레임 수로 변환"""
    return int((ms / 1000) * fps)


def frames_to_ms(frames: int, fps: float = 24) -> int:
    """프레임 수를 밀리초로 변환"""
    return int((frames / fps) * 1000)


def timecode_to_ms(tc: str, fps: float = 24) -> int:
    """타임코드(HH:MM:SS:FF)를 밀리초로 변환"""
    parts = tc.replace(';', ':').split(':')
    if len(parts) == 4:
        h, m, s, f = map(int, parts)
        return int((h * 3600 + m * 60 + s + f / fps) * 1000)
    return 0


def frames_to_timecode(frames: int, fps: float = 24) -> str:
    """프레임 수를 타임코드로 변환"""
    h = frames // (3600 * int(fps))
    m = (frames % (3600 * int(fps))) // (60 * int(fps))
    s = (frames % (60 * int(fps))) // int(fps)
    f = frames % int(fps)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


def format_duration(ms: int) -> str:
    """밀리초를 읽기 쉬운 형식으로 변환 (예: 2.5초)"""
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}분 {secs:.1f}초"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}시간 {minutes}분"
