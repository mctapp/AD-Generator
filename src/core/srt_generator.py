# core/srt_generator.py
# SRT 파일 생성기

import re
from typing import List, Optional
from .pdf_parser import ScriptEntry


class SRTGenerator:
    """SRT 파일 생성기"""
    
    def __init__(self, fps: float = 24):
        self.fps = fps
        self.default_duration_ms = 5000  # 기본 자막 지속 시간 5초
    
    def generate(self, entries: List[ScriptEntry], 
                 max_chars_per_line: int = 40,
                 break_on_period: bool = True,
                 remove_brackets: bool = True) -> str:
        """
        SRT 파일 내용 생성
        
        Args:
            entries: ScriptEntry 리스트
            max_chars_per_line: 줄당 최대 글자 수
            break_on_period: 마침표에서 줄바꿈
            remove_brackets: 괄호 내용 제거
        
        Returns:
            SRT 파일 내용 문자열
        """
        srt_content = []
        
        for i, entry in enumerate(entries):
            # 시작/종료 시간
            start_ms = entry.timecode_ms
            
            # 다음 항목이 있으면 그 시작 시간을 종료 시간으로
            if i + 1 < len(entries):
                end_ms = entries[i + 1].timecode_ms
            else:
                end_ms = start_ms + self.default_duration_ms
            
            # 텍스트 포맷팅
            text = entry.script_text
            
            if remove_brackets:
                text = re.sub(r'\([^)]*\)', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
            
            text = self._format_text(text, max_chars_per_line, break_on_period)
            
            # SRT 블록 생성
            srt_block = f"{entry.index}\n"
            srt_block += f"{self._ms_to_srt_time(start_ms)} --> {self._ms_to_srt_time(end_ms)}\n"
            srt_block += f"{text}\n"
            
            srt_content.append(srt_block)
        
        return '\n'.join(srt_content)
    
    def generate_from_entries_with_duration(self, entries: List[dict]) -> str:
        """
        종료 시간이 포함된 항목으로 SRT 생성
        
        Args:
            entries: [{'index': 1, 'start_ms': 0, 'end_ms': 5000, 'text': '...'}]
        """
        srt_content = []
        
        for entry in entries:
            srt_block = f"{entry['index']}\n"
            srt_block += f"{self._ms_to_srt_time(entry['start_ms'])} --> {self._ms_to_srt_time(entry['end_ms'])}\n"
            srt_block += f"{entry['text']}\n"
            srt_content.append(srt_block)
        
        return '\n'.join(srt_content)
    
    def _format_text(self, text: str, 
                     max_chars: int, 
                     break_on_period: bool) -> str:
        """텍스트 포맷팅"""
        
        if break_on_period:
            # 마침표 뒤에 줄바꿈
            text = re.sub(r'\.\s+', '.\n', text)
        
        # 줄당 글자 수 제한
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if len(line) <= max_chars:
                lines.append(line)
            else:
                # 긴 줄 분할
                current = ""
                for char in line:
                    current += char
                    if len(current) >= max_chars and char in ' ,':
                        lines.append(current.strip())
                        current = ""
                if current.strip():
                    lines.append(current.strip())
        
        return '\n'.join(lines)
    
    def _ms_to_srt_time(self, ms: int) -> str:
        """밀리초를 SRT 시간 형식으로 변환"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        milliseconds = ms % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def save(self, content: str, filepath: str, encoding: str = 'utf-8'):
        """SRT 파일 저장"""
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
    
    def set_fps(self, fps: float):
        """FPS 설정"""
        self.fps = fps
