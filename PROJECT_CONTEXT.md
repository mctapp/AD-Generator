# TOMATO AD Voice Generator - 프로젝트 컨텍스트

## 프로젝트 개요

**TOMATO AD**는 영화/영상의 **음성해설(Audio Description)** 제작을 자동화하는 macOS 데스크톱 애플리케이션입니다.

- **개발자**: Brian (미디어센터내일 / POLLLOCK)
- **기술 스택**: Python 3.11+, PyQt6, NAVER CLOVA Voice API
- **현재 버전**: v3.7.6
- **플랫폼**: macOS (Apple Silicon 지원)

---

## 핵심 워크플로우

```
PDF 대본 → SRT 추출 → TTS 음성 생성 → WAV 동기화 → DaVinci Resolve 내보내기
```

### 상세 흐름

1. **대본 → SRT** (Script Converter)
   - PDF 음성해설 대본 파싱 (y-coordinate 기반 v3.7 알고리즘)
   - 타임코드, 지시사항, 대본 텍스트 추출
   - SRT/XLSX 자동 저장

2. **SRT → TTS** (Batch Generator)
   - NAVER CLOVA Voice API로 음성 합성
   - WAV 파일 생성 (타임코드 포함 파일명)
   - FCPXML/EDL 타임라인 파일 생성

3. **SRT 동기화** (Sync Tab)
   - WAV 실제 길이와 SRT 타임코드 비교
   - 겹침(overlap) 감지 및 리포트
   - _synced.srt 자동 저장

4. **DaVinci Resolve 내보내기**
   - Media Pool 자동 임포트
   - 타임라인 생성 (개발 중)

---

## 파일 구조

```
TomatoAD/
├── run.sh                    # 실행 스크립트
├── requirements.txt          # 의존성
├── src/
│   ├── main.py              # 진입점
│   ├── core/
│   │   ├── pdf_parser.py    # PDF 파싱 (v3.7 y-coordinate 로직) ⚠️ 수정 금지
│   │   ├── srt_generator.py # SRT 생성
│   │   ├── srt_parser.py    # SRT 파싱
│   │   ├── srt_sync.py      # WAV-SRT 동기화
│   │   ├── tts_engine.py    # NAVER CLOVA TTS
│   │   ├── overlap_checker.py
│   │   ├── fcpxml_exporter.py
│   │   └── edl_exporter.py
│   ├── ui/
│   │   ├── main_window.py   # 메인 윈도우 + DaVinci 연동
│   │   ├── styles.py        # 색상/스타일 정의
│   │   ├── tabs/
│   │   │   ├── script_converter_tab.py  # 대본→SRT
│   │   │   ├── srt_batch_tab.py         # SRT→TTS
│   │   │   ├── single_clip_tab.py       # 단일 클립
│   │   │   └── srt_sync_tab.py          # 동기화
│   │   └── widgets/
│   │       ├── collapsible.py   # 접힘/펼침 섹션
│   │       ├── drop_zone.py     # 드래그앤드롭
│   │       ├── srt_table.py     # SRT 테이블
│   │       └── ...
│   └── utils/
│       ├── config.py        # 설정 관리
│       └── timecode.py      # 타임코드 변환
```

---

## 색상 스키마

```python
COLORS = {
    'bg_primary': '#1A1A1A',      # 배경 (어두운 회색)
    'brand_primary': '#6D3B1F',   # 브랜드 (갈색)
    'accent_yellow': '#F5C518',   # 강조 (노란색) - 탭 선택
    'accent_green': '#1DB954',    # 액션 (녹색) - 버튼
    'accent_success': '#10B981',  # 성공
    'accent_warning': '#F59E0B',  # 경고
    'accent_error': '#E74C3C',    # 오류
}
```

---

## PDF 파싱 알고리즘 (v3.7) ⚠️ 중요

**절대 수정하지 말 것** - 현재 정상 작동 중

### 핵심 로직
1. **타임코드 앵커 우선 탐색**: 4자리 숫자 패턴 (^\d{4}$) 스캔
2. **Y-좌표 기반 라인 분리**: Y_LINE_THRESHOLD = 8px
3. **영역 기반 할당**: 각 타임코드의 y_start ~ y_end 범위 내 밑줄 텍스트 수집
4. **지시어/대본 분리**: 괄호는 지시어, 밑줄은 대본

---

## 현재 이슈 (v3.7.6 기준)

### 해결된 이슈
- ✅ PDF 파싱 0200/0210 병합 문제 (y-coordinate 로직으로 해결)
- ✅ 추출결과 접힘 시 레이아웃 깨짐
- ✅ FPS 23.976 표시 잘림
- ✅ 겹침 보고서 단위 (ms + 초 + 프레임)
- ✅ 행 추가/삭제 기능
- ✅ 통합실행 워크플로우

### 미해결 이슈
- ⚠️ **DaVinci Resolve 타임라인 배치 실패**
  - Media Pool 임포트는 성공
  - AppendToTimeline이 작동하지 않음
  - 디버그 로그로 원인 분석 중

---

## NAVER CLOVA Voice API

### 인증
```python
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
```

### 엔드포인트
```
https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts
```

### 주요 파라미터
- `speaker`: 음성 (nara, clara, shinji 등)
- `speed`: 속도 (-5 ~ 5)
- `pitch`: 피치 (-5 ~ 5)
- `volume`: 볼륨 (-5 ~ 5)

---

## 개발 가이드

### 실행
```bash
cd TomatoAD
./run.sh
```

### 의존성 설치
```bash
pip install -r requirements.txt
```

### 주요 의존성
- PyQt6
- PyMuPDF (fitz)
- requests
- openpyxl

---

## 다음 개발 과제

1. **DaVinci Resolve 연동 완성**
   - 타임라인 자동 배치 문제 해결
   - 영상 + AD오디오 + 자막 통합

2. **UI 개선**
   - 테이블 마지막 행 가려짐 문제
   - 스핀박스 버튼 스타일

3. **기능 확장**
   - 다중 음성 지원
   - 배치 재시도 기능
   - 프로젝트 저장/불러오기
