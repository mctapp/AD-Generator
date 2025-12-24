# core/validation.py
# PDF → SRT 변환 검증 모듈 v2.0

import re
import os
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class ValidationResult:
    """검증 결과"""
    # 타임코드 검증
    timecode_original: int
    timecode_converted: int
    timecode_match: bool

    # 음절수 검증 (전체 밑줄 텍스트 vs 전체 SRT 텍스트)
    syllable_original: int
    syllable_converted: int
    syllable_match: bool
    syllable_diff: int  # 누락된 음절수 (원본 - 변환)

    # 전체 결과
    is_valid: bool

    def get_summary_text(self) -> str:
        """UI 표시용 요약 텍스트"""
        tc_icon = "✓" if self.timecode_match else "⚠️"
        syl_icon = "✓" if self.syllable_match else "⚠️"

        tc_diff = ""
        if not self.timecode_match:
            diff = self.timecode_converted - self.timecode_original
            tc_diff = f" ({diff:+d}개)"

        syl_diff = ""
        if not self.syllable_match:
            syl_diff = f" ({self.syllable_diff}자 누락)"

        return (
            f"[검증] 타임코드: {self.timecode_original}개 → "
            f"{self.timecode_converted}개{tc_diff} {tc_icon} | "
            f"음절수: {self.syllable_original:,} → "
            f"{self.syllable_converted:,}{syl_diff} {syl_icon}"
        )


class Validator:
    """PDF → SRT 변환 검증기 v2.0

    검증 방식:
    - 타임코드 수: 파싱된 entries 수 비교
    - 음절수: PDF의 모든 밑줄 텍스트 vs SRT의 모든 텍스트 비교
      (페이지 걸침으로 인한 누락 검출)
    """

    def __init__(self):
        self.result: Optional[ValidationResult] = None
        self.pdf_path: Optional[str] = None
        self.srt_path: Optional[str] = None
        self.all_underlined_text: Optional[str] = None

    @staticmethod
    def count_syllables(text: str) -> int:
        """
        텍스트의 음절수 계산
        - 공백, 특수문자 제외
        - 한글/영문/숫자 글자 수
        """
        # 공백 및 특수문자 제거 (한글, 영문, 숫자만 남김)
        cleaned = re.sub(r'[^\w가-힣]', '', text)
        return len(cleaned)

    def validate(self,
                 all_underlined_text: str,
                 converted_entries: List,
                 timecode_count_original: int,
                 pdf_path: str = None,
                 srt_path: str = None) -> ValidationResult:
        """
        변환 결과 검증

        Args:
            all_underlined_text: PDF에서 추출한 모든 밑줄 텍스트
            converted_entries: SRT로 변환된 항목 리스트
            timecode_count_original: 원본 PDF의 타임코드 수
            pdf_path: PDF 파일 경로 (보고서용)
            srt_path: SRT 파일 경로 (보고서용)

        Returns:
            ValidationResult
        """
        self.pdf_path = pdf_path
        self.srt_path = srt_path
        self.all_underlined_text = all_underlined_text

        # 타임코드 수 비교
        tc_original = timecode_count_original
        tc_converted = len(converted_entries)
        tc_match = tc_original == tc_converted

        # 음절수 비교 (전체 밑줄 텍스트 vs 전체 SRT 텍스트)
        syl_original = self.count_syllables(all_underlined_text)

        # SRT entries에서 전체 텍스트 추출
        srt_all_text = " ".join(e.script_text for e in converted_entries)
        syl_converted = self.count_syllables(srt_all_text)

        syl_match = syl_original == syl_converted
        syl_diff = syl_original - syl_converted  # 양수면 누락

        self.result = ValidationResult(
            timecode_original=tc_original,
            timecode_converted=tc_converted,
            timecode_match=tc_match,
            syllable_original=syl_original,
            syllable_converted=syl_converted,
            syllable_match=syl_match,
            syllable_diff=syl_diff,
            is_valid=tc_match and syl_match
        )

        return self.result

    def generate_report(self) -> str:
        """검증 보고서 생성"""
        if not self.result:
            return "검증 결과가 없습니다."

        r = self.result

        lines = [
            "=" * 50,
            "ADFlow 검증 리포트",
            "=" * 50,
            "",
            f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if self.pdf_path:
            lines.append(f"PDF 파일: {os.path.basename(self.pdf_path)}")
        if self.srt_path:
            lines.append(f"SRT 파일: {os.path.basename(self.srt_path)}")

        lines.extend([
            "",
            "-" * 50,
            "",
            "[타임코드 검증]",
            f"  원본: {r.timecode_original}개",
            f"  변환: {r.timecode_converted}개",
        ])

        if r.timecode_match:
            lines.append("  결과: ✓ 일치")
        else:
            diff = r.timecode_converted - r.timecode_original
            lines.append(f"  차이: {diff:+d}개")
            lines.append("  결과: ⚠️ 불일치")

        lines.extend([
            "",
            "[음절수 검증]",
            f"  PDF 밑줄 텍스트: {r.syllable_original:,} 음절",
            f"  SRT 변환 텍스트: {r.syllable_converted:,} 음절",
        ])

        if r.syllable_match:
            lines.append("  결과: ✓ 일치")
        else:
            lines.append(f"  누락: {r.syllable_diff} 음절")
            lines.append("  결과: ⚠️ 불일치 (페이지 걸침 의심)")

        lines.extend([
            "",
            "-" * 50,
            "",
            f"전체 결과: {'✓ 검증 통과' if r.is_valid else '⚠️ 검증 실패'}",
        ])

        if not r.is_valid:
            lines.extend([
                "",
                "※ 검증 실패 시 PDF 원본에서 페이지가 넘어가는 부분의",
                "  밑줄 텍스트가 누락되었을 수 있습니다.",
            ])

        lines.extend([
            "",
            "=" * 50,
        ])

        return "\n".join(lines)

    def save_report(self, filepath: str):
        """검증 보고서 저장"""
        report = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)


__all__ = ['Validator', 'ValidationResult']
