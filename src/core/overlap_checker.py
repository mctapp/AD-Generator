# core/overlap_checker.py
# AD 분량 오버랩 검사

import os
from dataclasses import dataclass
from typing import List, Optional
from ..utils.audio import get_wav_duration_ms
from ..utils.timecode import ms_to_timecode, ms_to_filename_tc


@dataclass
class OverlapResult:
    """오버랩 검사 결과"""
    index: int
    timecode: str
    text: str
    tts_duration_ms: int
    available_duration_ms: int
    diff_ms: int
    status: str  # 'OK', 'OVER', 'MISSING'
    wav_path: Optional[str] = None
    
    @property
    def is_over(self) -> bool:
        return self.status == 'OVER'
    
    @property
    def diff_seconds(self) -> float:
        return self.diff_ms / 1000
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timecode': self.timecode,
            'text': self.text,
            'tts_duration_ms': self.tts_duration_ms,
            'available_duration_ms': self.available_duration_ms,
            'diff_ms': self.diff_ms,
            'status': self.status,
            'wav_path': self.wav_path
        }


class OverlapChecker:
    """AD 분량 오버랩 검사기"""
    
    def __init__(self, fps: float = 24):
        self.fps = fps
        self.results: List[OverlapResult] = []
        self.issues: List[OverlapResult] = []
    
    def check(self, entries: list, wav_folder: str) -> List[OverlapResult]:
        """오버랩 검사 실행
        
        Args:
            entries: SRTEntry 리스트
            wav_folder: WAV 파일이 있는 폴더
        
        Returns:
            OverlapResult 리스트
        """
        self.results = []
        self.issues = []
        
        for entry in entries:
            tc_filename = ms_to_filename_tc(entry.start_ms, self.fps)
            wav_path = os.path.join(wav_folder, f"{tc_filename}.wav")
            
            if os.path.exists(wav_path):
                tts_duration = get_wav_duration_ms(wav_path)
                available_duration = entry.duration_ms
                diff = tts_duration - available_duration
                
                if diff > 0:
                    status = 'OVER'
                else:
                    status = 'OK'
                
                result = OverlapResult(
                    index=entry.index,
                    timecode=ms_to_timecode(entry.start_ms, self.fps),
                    text=entry.text[:50] + '...' if len(entry.text) > 50 else entry.text,
                    tts_duration_ms=tts_duration,
                    available_duration_ms=available_duration,
                    diff_ms=diff,
                    status=status,
                    wav_path=wav_path
                )
            else:
                result = OverlapResult(
                    index=entry.index,
                    timecode=ms_to_timecode(entry.start_ms, self.fps),
                    text=entry.text[:50] + '...' if len(entry.text) > 50 else entry.text,
                    tts_duration_ms=0,
                    available_duration_ms=entry.duration_ms,
                    diff_ms=0,
                    status='MISSING',
                    wav_path=None
                )
            
            self.results.append(result)
            
            if result.is_over:
                self.issues.append(result)
        
        return self.results
    
    def get_summary(self) -> dict:
        """검사 요약 반환"""
        total = len(self.results)
        ok_count = sum(1 for r in self.results if r.status == 'OK')
        over_count = sum(1 for r in self.results if r.status == 'OVER')
        missing_count = sum(1 for r in self.results if r.status == 'MISSING')
        
        total_over_ms = sum(r.diff_ms for r in self.results if r.is_over)
        
        return {
            'total': total,
            'ok': ok_count,
            'over': over_count,
            'missing': missing_count,
            'total_over_ms': total_over_ms,
            'has_issues': over_count > 0 or missing_count > 0
        }
    
    def generate_report(self) -> str:
        """텍스트 리포트 생성"""
        summary = self.get_summary()
        
        lines = [
            "=" * 50,
            "AD TTS 분량 검사 리포트",
            "=" * 50,
            "",
        ]
        
        if self.issues:
            lines.append(f"⚠️ 문제 구간: {len(self.issues)}개")
            lines.append("")
            
            for item in self.issues:
                lines.append(f"[{item.timecode}] #{item.index}")
                lines.append(f"  내용: {item.text}")
                lines.append(f"  TTS: {item.tts_duration_ms/1000:.1f}초")
                lines.append(f"  가용: {item.available_duration_ms/1000:.1f}초")
                lines.append(f"  초과: {item.diff_ms/1000:.1f}초")
                lines.append("")
        else:
            lines.append("모든 구간 정상")
            lines.append("")
        
        lines.append("-" * 50)
        lines.append(f"총 {summary['total']}개 구간")
        lines.append(f"  - 정상: {summary['ok']}개")
        lines.append(f"  - 초과: {summary['over']}개")
        lines.append(f"  - 누락: {summary['missing']}개")
        
        if summary['total_over_ms'] > 0:
            lines.append(f"  - 총 초과 시간: {summary['total_over_ms']/1000:.1f}초")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def save_report(self, filepath: str):
        """리포트를 파일로 저장"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
