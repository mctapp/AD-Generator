# core/srt_parser.py
# SRT 파일 파싱

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SRTEntry:
    """SRT 항목 데이터 클래스"""
    index: int
    start_ms: int
    end_ms: int
    text: str
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'start_ms': self.start_ms,
            'end_ms': self.end_ms,
            'text': self.text,
            'duration_ms': self.duration_ms
        }


class SRTParser:
    """SRT 파일 파서"""
    
    SRT_PATTERN = re.compile(
        r'(\d+)\s*\n'
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*'
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*\n'
        r'(.*?)(?=\n\n|\n\d+\n|\Z)',
        re.DOTALL
    )
    
    def __init__(self):
        self.entries: List[SRTEntry] = []
        self.filepath: Optional[str] = None
    
    def parse(self, filepath: str) -> List[SRTEntry]:
        """SRT 파일 파싱"""
        self.filepath = filepath
        self.entries = []
        
        # 여러 인코딩 시도
        encodings = ['utf-8', 'utf-8-sig', 'cp949', 'euc-kr', 'latin-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise ValueError(f"파일을 읽을 수 없습니다: {filepath}")
        
        for match in self.SRT_PATTERN.finditer(content):
            idx = int(match.group(1))
            
            start_ms = (
                int(match.group(2)) * 3600000 +
                int(match.group(3)) * 60000 +
                int(match.group(4)) * 1000 +
                int(match.group(5))
            )
            
            end_ms = (
                int(match.group(6)) * 3600000 +
                int(match.group(7)) * 60000 +
                int(match.group(8)) * 1000 +
                int(match.group(9))
            )
            
            text = match.group(10).strip().replace('\n', ' ')
            
            entry = SRTEntry(
                index=idx,
                start_ms=start_ms,
                end_ms=end_ms,
                text=text
            )
            self.entries.append(entry)
        
        return self.entries
    
    def parse_text(self, content: str) -> List[SRTEntry]:
        """SRT 텍스트 내용 파싱"""
        self.entries = []
        
        for match in self.SRT_PATTERN.finditer(content):
            idx = int(match.group(1))
            
            start_ms = (
                int(match.group(2)) * 3600000 +
                int(match.group(3)) * 60000 +
                int(match.group(4)) * 1000 +
                int(match.group(5))
            )
            
            end_ms = (
                int(match.group(6)) * 3600000 +
                int(match.group(7)) * 60000 +
                int(match.group(8)) * 1000 +
                int(match.group(9))
            )
            
            text = match.group(10).strip().replace('\n', ' ')
            
            entry = SRTEntry(
                index=idx,
                start_ms=start_ms,
                end_ms=end_ms,
                text=text
            )
            self.entries.append(entry)
        
        return self.entries
    
    def get_total_duration_ms(self) -> int:
        """전체 길이 (마지막 항목 끝 시간)"""
        if not self.entries:
            return 0
        return max(entry.end_ms for entry in self.entries)
    
    def get_entry_count(self) -> int:
        """항목 수"""
        return len(self.entries)
    
    def get_total_text_length(self) -> int:
        """전체 텍스트 글자 수"""
        return sum(len(entry.text) for entry in self.entries)
