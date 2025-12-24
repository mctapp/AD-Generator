# core/pdf_parser.py
# PDF 음성해설 대본 파서 v3.7 (y좌표 기반)

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class ScriptEntry:
    """파싱된 대본 항목"""
    index: int
    timecode_raw: str           # 원본 타임코드 (예: "0036")
    timecode_formatted: str     # 포맷된 타임코드 (예: "00:00:36:00")
    timecode_ms: int            # 밀리초
    bracket_content: str        # 괄호 안 내용 - 지시사항 (예: "바로")
    script_text: str            # 음성해설 대본 텍스트


class PDFParser:
    """
    PDF 음성해설 대본 파서 v3.7 (y좌표 기반)
    
    개선된 파싱 로직:
    1. 타임코드 앵커 우선 탐색 - 모든 4자리 숫자의 위치 파악
    2. y좌표 기반 라인 분리 - block/line 무시, 순수 y좌표로 판단
    3. 타임코드 영역별 할당 - 각 타임코드 y좌표 범위 내 텍스트 수집
    """
    
    # 효과음 키워드 (지시사항에서 제외)
    SOUND_KEYWORDS = ['소리', '울음', '웃음', '효과음', '천둥', '한숨', '비명', '신음']
    
    # y좌표 라인 분리 임계값 (픽셀)
    Y_LINE_THRESHOLD = 8.0
    
    def __init__(self):
        if not HAS_PYMUPDF:
            raise ImportError("PyMuPDF 패키지가 필요합니다: pip install PyMuPDF")
    
    def parse(self, pdf_path: str, 
              remove_slashes: bool = True,
              remove_periods: bool = False,
              include_brackets: bool = False) -> List[ScriptEntry]:
        """
        PDF에서 음성해설 대본 파싱
        
        Args:
            pdf_path: PDF 파일 경로
            remove_slashes: '/' 기호 제거 여부
            remove_periods: '.' 기호 제거 여부
            include_brackets: 괄호 내용(지시사항) 텍스트에 포함 여부
        
        Returns:
            파싱된 ScriptEntry 리스트
        """
        doc = fitz.open(pdf_path)
        
        # 1. 모든 페이지에서 words와 밑줄 수집
        all_words = []
        all_underlines = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # words 수집
            for w in page.get_text("words"):
                all_words.append({
                    "page": page_num,
                    "x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3],
                    "text": w[4]
                })
            
            # 밑줄(수평선) 수집
            for d in page.get_drawings():
                items = d.get("items", [])
                if items and items[0][0] == "l":
                    start, end = items[0][1], items[0][2]
                    if abs(start.y - end.y) < 1:  # 수평선
                        all_underlines.append({
                            "page": page_num,
                            "y": start.y,
                            "x0": min(start.x, end.x),
                            "x1": max(start.x, end.x)
                        })
        
        doc.close()
        
        # 2. 타임코드 앵커 우선 탐색
        timecode_anchors = self._find_timecode_anchors(all_words)
        
        if not timecode_anchors:
            return []
        
        # 3. y좌표 기반 라인 분리
        lines = self._group_words_by_y(all_words, all_underlines)
        
        # 4. 타임코드 영역별 텍스트 할당
        entries = self._assign_lines_to_timecodes(
            timecode_anchors, lines, 
            remove_slashes, remove_periods, include_brackets
        )
        
        return entries
    
    def _find_timecode_anchors(self, words: List[Dict]) -> List[Dict]:
        """타임코드 위치를 먼저 찾아 앵커로 저장

        타임코드 형식:
        - 4자리: MMSS (예: 3400 = 34분 00초)
        - 5자리: HMMSS (예: 11111 = 1시간 11분 11초)
        - 6자리: HHMMSS (예: 015628 = 01시간 56분 28초)
        """
        anchors = []
        # 4-6자리 숫자 패턴 (60분 이상 타임코드 지원)
        tc_pattern = re.compile(r'^\d{4,6}$')

        for w in words:
            text = w["text"].strip()
            if tc_pattern.match(text):
                # 타임코드 유효성 검증
                if self._is_valid_timecode(text):
                    anchors.append({
                        "timecode": text,
                        "page": w["page"],
                        "y": w["y0"],
                        "x": w["x0"]
                    })
        
        # 페이지, y좌표 순 정렬
        anchors.sort(key=lambda x: (x["page"], x["y"], x["x"]))
        
        # 중복 제거 (같은 y좌표에 있는 타임코드)
        unique_anchors = []
        prev_key = None
        for a in anchors:
            key = (a["page"], round(a["y"] / 10))  # 10px 단위로 그룹화
            if key != prev_key:
                unique_anchors.append(a)
                prev_key = key
        
        return unique_anchors
    
    def _is_underlined(self, word: Dict, underlines: List[Dict]) -> bool:
        """단어에 밑줄이 있는지 확인"""
        for ul in underlines:
            if ul["page"] != word["page"]:
                continue
            # 밑줄이 텍스트 하단 바로 아래 (0~5px)
            y_diff = ul["y"] - word["y1"]
            if 0 < y_diff < 5:
                # x 범위 겹침 확인
                if word["x0"] < ul["x1"] and word["x1"] > ul["x0"]:
                    return True
        return False
    
    def _group_words_by_y(self, words: List[Dict], 
                          underlines: List[Dict]) -> List[Dict]:
        """y좌표 기준으로 라인 그룹화 (block/line 무시)"""
        if not words:
            return []
        
        # 페이지, y좌표 순 정렬
        sorted_words = sorted(words, key=lambda x: (x["page"], x["y0"], x["x0"]))
        
        lines = []
        current_line_words = [sorted_words[0]]
        current_y = sorted_words[0]["y0"]
        current_page = sorted_words[0]["page"]
        
        for w in sorted_words[1:]:
            # 페이지 변경 또는 y좌표 차이가 임계값 초과
            if w["page"] != current_page or abs(w["y0"] - current_y) > self.Y_LINE_THRESHOLD:
                # 현재 라인 저장
                line = self._merge_line_words(current_line_words, underlines)
                lines.append(line)
                
                current_line_words = [w]
                current_y = w["y0"]
                current_page = w["page"]
            else:
                current_line_words.append(w)
        
        # 마지막 라인
        if current_line_words:
            line = self._merge_line_words(current_line_words, underlines)
            lines.append(line)
        
        return lines
    
    def _merge_line_words(self, words: List[Dict], underlines: List[Dict]) -> Dict:
        """같은 라인의 단어들을 병합"""
        # x좌표 순 정렬
        words.sort(key=lambda x: x["x0"])
        
        text = " ".join(w["text"] for w in words)
        has_underline = any(self._is_underlined(w, underlines) for w in words)
        
        return {
            "page": words[0]["page"],
            "y": words[0]["y0"],
            "text": text,
            "underlined": has_underline
        }
    
    def _assign_lines_to_timecodes(self, anchors: List[Dict], 
                                    lines: List[Dict],
                                    remove_slashes: bool,
                                    remove_periods: bool,
                                    include_brackets: bool) -> List[ScriptEntry]:
        """각 라인을 해당 타임코드 영역에 할당"""
        entries = []
        
        for i, anchor in enumerate(anchors):
            tc = anchor["timecode"]
            tc_page = anchor["page"]
            tc_y = anchor["y"]
            
            # 다음 타임코드의 y좌표 (영역 끝)
            if i + 1 < len(anchors) and anchors[i + 1]["page"] == tc_page:
                next_y = anchors[i + 1]["y"]
            else:
                next_y = float('inf')  # 페이지 끝까지
            
            # 이 타임코드 영역의 라인들 수집
            region_lines = []
            for line in lines:
                if line["page"] != tc_page:
                    continue
                
                # y좌표가 현재 타임코드 ~ 다음 타임코드 범위
                if tc_y - 5 <= line["y"] < next_y - 5:
                    region_lines.append(line)
            
            # 타임코드와 같은 라인에서 지시어 추출
            instructions = []
            script_texts = []
            
            for line in region_lines:
                text = line["text"]
                
                # 타임코드 자체 제거 (4-6자리)
                text = re.sub(r'^\d{4,6}\s*', '', text)
                
                # 괄호 지시어 추출
                bracket_match = re.match(r'\(([^)]+)\)\s*(.*)', text)
                if bracket_match:
                    instr = bracket_match.group(1)
                    if not any(kw in instr for kw in self.SOUND_KEYWORDS):
                        instructions.append(instr)
                    text = bracket_match.group(2).strip()
                
                # 밑줄 텍스트만 스크립트로
                if text and line["underlined"]:
                    script_texts.append(text)
            
            # 엔트리 생성
            if script_texts:
                entry = self._build_entry(
                    index=len(entries) + 1,
                    timecode_raw=tc,
                    instructions=instructions,
                    scripts=script_texts,
                    remove_slashes=remove_slashes,
                    remove_periods=remove_periods,
                    include_brackets=include_brackets
                )
                if entry:
                    entries.append(entry)
        
        return entries
    
    def _build_entry(self, index: int, timecode_raw: str,
                     instructions: List[str], scripts: List[str],
                     remove_slashes: bool, remove_periods: bool,
                     include_brackets: bool) -> Optional[ScriptEntry]:
        """ScriptEntry 생성"""
        # 타임코드 변환
        tc_formatted, tc_ms = self._parse_timecode(timecode_raw)
        
        # 지시사항
        bracket_content = ", ".join(instructions)
        
        # 대본 텍스트
        script_text = " ".join(scripts)
        
        # 슬래시 제거
        if remove_slashes:
            script_text = script_text.replace("/", " ")
        
        # 마침표 제거
        if remove_periods:
            script_text = script_text.replace(".", " ")
        
        # 지시사항 포함
        if include_brackets and bracket_content:
            script_text = f"({bracket_content}) {script_text}"
        
        # 연속 공백 제거
        script_text = re.sub(r'\s+', ' ', script_text).strip()
        
        if not script_text:
            return None
        
        return ScriptEntry(
            index=index,
            timecode_raw=timecode_raw,
            timecode_formatted=tc_formatted,
            timecode_ms=tc_ms,
            bracket_content=bracket_content,
            script_text=script_text
        )
    
    def _is_valid_timecode(self, raw: str) -> bool:
        """타임코드 유효성 검증

        Args:
            raw: 4-6자리 숫자 문자열

        Returns:
            유효한 타임코드이면 True
        """
        try:
            length = len(raw)

            if length == 4:
                # MMSS: 분(00-99), 초(00-59)
                minutes = int(raw[:2])
                seconds = int(raw[2:])
                return 0 <= minutes <= 99 and 0 <= seconds <= 59
            elif length == 5:
                # HMMSS: 시(0-9), 분(00-59), 초(00-59)
                hours = int(raw[0])
                minutes = int(raw[1:3])
                seconds = int(raw[3:])
                return 0 <= hours <= 9 and 0 <= minutes <= 59 and 0 <= seconds <= 59
            elif length == 6:
                # HHMMSS: 시(00-99), 분(00-59), 초(00-59)
                hours = int(raw[:2])
                minutes = int(raw[2:4])
                seconds = int(raw[4:])
                return 0 <= hours <= 99 and 0 <= minutes <= 59 and 0 <= seconds <= 59
            return False
        except ValueError:
            return False

    def _parse_timecode(self, raw: str) -> Tuple[str, int]:
        """
        4-6자리 타임코드를 HH:MM:SS:FF 형식과 밀리초로 변환

        형식:
        - 4자리 MMSS: "3400" → ("00:34:00:00", 2040000) - 34분 0초
        - 5자리 HMMSS: "11111" → ("01:11:11:00", 4271000) - 1시간 11분 11초
        - 6자리 HHMMSS: "015628" → ("01:56:28:00", 7028000) - 1시간 56분 28초
        """
        length = len(raw)

        if length == 4:
            # MMSS 형식
            minutes = int(raw[:2])
            seconds = int(raw[2:])
            hours = minutes // 60
            minutes = minutes % 60
        elif length == 5:
            # HMMSS 형식 (시간 1자리)
            hours = int(raw[0])
            minutes = int(raw[1:3])
            seconds = int(raw[3:])
        elif length == 6:
            # HHMMSS 형식 (시간 2자리)
            hours = int(raw[:2])
            minutes = int(raw[2:4])
            seconds = int(raw[4:])
        else:
            # 기본값 (4자리로 처리)
            raw = raw.zfill(4)
            minutes = int(raw[:2])
            seconds = int(raw[2:])
            hours = minutes // 60
            minutes = minutes % 60

        tc_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}:00"
        tc_ms = (hours * 3600 + minutes * 60 + seconds) * 1000

        return tc_formatted, tc_ms
    
    def get_page_count(self, pdf_path: str) -> int:
        """PDF 페이지 수 반환"""
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count

    def get_all_underlined_text(self, pdf_path: str) -> str:
        """
        PDF에서 모든 밑줄 텍스트를 추출 (검증용)

        parse()와 동일한 라인 단위 로직 사용:
        - 라인에 밑줄 단어가 하나라도 있으면 전체 라인 텍스트 포함
        - 페이지 경계와 타임코드에 관계없이 모든 밑줄 라인 수집

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            밑줄이 그어진 모든 텍스트 (공백으로 연결)
        """
        doc = fitz.open(pdf_path)

        # 모든 페이지에서 words와 밑줄 수집
        all_words = []
        all_underlines = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # words 수집
            for w in page.get_text("words"):
                all_words.append({
                    "page": page_num,
                    "x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3],
                    "text": w[4]
                })

            # 밑줄(수평선) 수집
            for d in page.get_drawings():
                items = d.get("items", [])
                if items and items[0][0] == "l":
                    start, end = items[0][1], items[0][2]
                    if abs(start.y - end.y) < 1:  # 수평선
                        all_underlines.append({
                            "page": page_num,
                            "y": start.y,
                            "x0": min(start.x, end.x),
                            "x1": max(start.x, end.x)
                        })

        doc.close()

        # 라인 단위로 그룹화 (parse()와 동일한 로직)
        lines = self._group_words_by_y(all_words, all_underlines)

        # 밑줄이 있는 라인의 텍스트만 수집
        underlined_texts = []
        for line in lines:
            if line["underlined"]:
                # 타임코드 제거 (4-6자리 숫자)
                text = re.sub(r'^\d{4,6}\s*', '', line["text"])
                # 괄호 지시어 제거
                text = re.sub(r'\([^)]*\)\s*', '', text)
                text = text.strip()
                if text:
                    underlined_texts.append(text)

        # 텍스트 합치기
        all_text = " ".join(underlined_texts)

        # 연속 공백 제거
        all_text = re.sub(r'\s+', ' ', all_text).strip()

        return all_text


__all__ = ['PDFParser', 'ScriptEntry']
