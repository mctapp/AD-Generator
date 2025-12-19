# ui/tabs/single_clip_tab.py
# 단일 클립 생성 탭

import os
import subprocess
import tempfile
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QMessageBox, QFrame,
    QApplication, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal

from ..styles import COLORS, FONTS, RADIUS, get_button_style, get_input_style
from ..widgets import TimecodeInput, ClipHistoryTable, CollapsibleSection
from ...core import TTSEngine, TTSOptions
from ...utils import config


class SingleClipTab(QWidget):
    """단일 클립 생성 탭"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_engine = TTSEngine()
        self.output_folder = None
        self.fps = 24
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)
        
        # === 클립 정보 입력 ===
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['lg']};
            }}
        """)
        input_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(12)
        
        # 타임코드 입력
        tc_layout = QHBoxLayout()
        tc_layout.setSpacing(12)
        
        tc_label = QLabel("타임코드")
        tc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        tc_label.setFixedWidth(80)
        tc_layout.addWidget(tc_label)
        
        self.timecode_input = TimecodeInput(self.fps)
        tc_layout.addWidget(self.timecode_input)
        
        tc_hint = QLabel("HH:MM:SS:FF")
        tc_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        tc_layout.addWidget(tc_hint)
        
        tc_layout.addStretch()
        
        input_layout.addLayout(tc_layout)
        
        # 텍스트 입력
        text_label = QLabel("텍스트")
        text_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        input_layout.addWidget(text_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("음성으로 변환할 텍스트를 입력하세요...")
        self.text_edit.setMinimumHeight(80)
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
                padding: 10px;
                font-size: {FONTS['size_base']};
                color: {COLORS['text_primary']};
            }}
            QTextEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        input_layout.addWidget(self.text_edit)
        
        # 글자 수 표시
        char_layout = QHBoxLayout()
        char_layout.addStretch()
        self.label_char_count = QLabel("0자")
        self.label_char_count.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        char_layout.addWidget(self.label_char_count)
        input_layout.addLayout(char_layout)
        
        self.text_edit.textChanged.connect(self._update_char_count)
        
        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        self.btn_preview = QPushButton("미리듣기")
        self.btn_preview.setStyleSheet(get_button_style('secondary'))
        self.btn_preview.setFixedWidth(100)
        self.btn_preview.clicked.connect(self.preview_tts)
        btn_layout.addWidget(self.btn_preview)
        
        self.btn_generate = QPushButton("WAV 생성")
        self.btn_generate.setStyleSheet(get_button_style('primary'))
        self.btn_generate.setFixedWidth(100)
        self.btn_generate.clicked.connect(self.generate_wav)
        btn_layout.addWidget(self.btn_generate)
        
        input_layout.addLayout(btn_layout)
        
        layout.addWidget(input_frame)
        
        # === 생성 기록 (접힘/펼침) ===
        self.history_section = CollapsibleSection("생성 기록 (0개)", expanded=True)
        self.clip_history = ClipHistoryTable()
        self.clip_history.setMinimumHeight(200)
        self.clip_history.clip_selected.connect(self._on_clip_selected)
        self.history_section.set_content(self.clip_history)
        layout.addWidget(self.history_section, 1)
        
        # 하단 버튼
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        bottom_layout.addStretch()
        
        self.btn_export_fcpxml = QPushButton("FCPXML 내보내기")
        self.btn_export_fcpxml.setStyleSheet(get_button_style('secondary'))
        self.btn_export_fcpxml.setFixedWidth(130)
        self.btn_export_fcpxml.clicked.connect(self.export_fcpxml)
        self.btn_export_fcpxml.setEnabled(False)
        bottom_layout.addWidget(self.btn_export_fcpxml)
        
        layout.addLayout(bottom_layout)
        
        self._update_buttons()
    
    def _update_char_count(self):
        """글자 수 업데이트"""
        text = self.text_edit.toPlainText()
        self.label_char_count.setText(f"{len(text)}자")
        self._update_buttons()
    
    def _update_buttons(self):
        """버튼 상태 업데이트"""
        has_text = len(self.text_edit.toPlainText().strip()) > 0
        has_api = config.has_api_keys()
        has_output = self.output_folder is not None
        
        self.btn_preview.setEnabled(has_text and has_api)
        self.btn_generate.setEnabled(has_text and has_api and has_output)
        
        has_records = len(self.clip_history.get_success_records()) > 0
        self.btn_export_fcpxml.setEnabled(has_records and has_output)
        
        # 기록 수 업데이트
        record_count = len(self.clip_history.records)
        self.history_section.set_title(f"생성 기록 ({record_count}개)")
        
        if not has_api:
            self.btn_generate.setToolTip("설정에서 API 키를 입력하세요")
        elif not has_output:
            self.btn_generate.setToolTip("출력 폴더를 선택하세요")
        else:
            self.btn_generate.setToolTip("")
    
    def set_output_folder(self, folder: str):
        """출력 폴더 설정"""
        self.output_folder = folder
        self._update_buttons()
    
    def set_fps(self, fps: float):
        """FPS 설정"""
        self.fps = fps
        self.timecode_input.set_fps(fps)
    
    def set_voice_settings(self, settings: dict):
        """음성 설정 적용"""
        options = TTSOptions(**settings)
        self.tts_engine.set_options(options)
    
    def preview_tts(self):
        """미리듣기"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        
        if not config.has_api_keys():
            QMessageBox.warning(self, "경고", "설정에서 API 키를 먼저 입력하세요.")
            return
        
        self.tts_engine.set_credentials(config.client_id, config.client_secret)
        
        temp_file = os.path.join(tempfile.gettempdir(), 'tomato_preview.wav')
        
        self.btn_preview.setEnabled(False)
        self.btn_preview.setText("생성 중...")
        QApplication.processEvents()
        
        if self.tts_engine.generate_single(text, temp_file):
            subprocess.run(['afplay', temp_file], check=False)
            self.status_message.emit("미리듣기 완료")
        else:
            QMessageBox.warning(self, "오류", "미리듣기 생성에 실패했습니다.")
            self.status_message.emit("미리듣기 실패")
        
        self.btn_preview.setEnabled(True)
        self.btn_preview.setText("미리듣기")
    
    def generate_wav(self):
        """WAV 파일 생성"""
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        
        if not self.timecode_input.is_valid():
            QMessageBox.warning(self, "경고", "올바른 타임코드를 입력하세요.")
            return
        
        if not self.output_folder:
            QMessageBox.warning(self, "경고", "출력 폴더를 선택하세요.")
            return
        
        # WAV 폴더 생성
        wav_folder = os.path.join(self.output_folder, 'wav')
        os.makedirs(wav_folder, exist_ok=True)
        
        # 파일명 생성
        tc_filename = self.timecode_input.get_timecode_for_filename()
        output_path = os.path.join(wav_folder, f"{tc_filename}.wav")
        
        # 파일 존재 확인
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self, "확인",
                f"파일이 이미 존재합니다:\n{tc_filename}.wav\n\n덮어쓰시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.tts_engine.set_credentials(config.client_id, config.client_secret)
        
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("생성 중...")
        QApplication.processEvents()
        
        success = self.tts_engine.generate_single(text, output_path)
        
        # 기록 추가
        timecode = self.timecode_input.get_timecode()
        self.clip_history.add_record(timecode, text, output_path, success)
        
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("WAV 생성")
        self._update_buttons()
        
        if success:
            self.status_message.emit(f"생성 완료: {tc_filename}.wav")
            self.text_edit.clear()
        else:
            QMessageBox.warning(self, "오류", "WAV 생성에 실패했습니다.")
            self.status_message.emit("WAV 생성 실패")
    
    def _on_clip_selected(self, record):
        """기록 선택 시 입력 필드에 로드"""
        self.timecode_input.set_timecode(record.timecode)
        self.text_edit.setPlainText(record.text)
    
    def export_fcpxml(self):
        """생성된 클립들을 FCPXML로 내보내기"""
        records = self.clip_history.get_success_records()
        if not records:
            QMessageBox.warning(self, "경고", "내보낼 클립이 없습니다.")
            return
        
        from ...core import FCPXMLExporter
        from ...core.srt_parser import SRTEntry
        
        # 레코드를 SRTEntry 형식으로 변환
        entries = []
        for i, record in enumerate(records):
            tc = record.timecode.replace('_', ':')
            parts = tc.split(':')
            if len(parts) == 4:
                hh, mm, ss, ff = map(int, parts)
                start_ms = int((hh * 3600 + mm * 60 + ss + ff / self.fps) * 1000)
            else:
                start_ms = 0
            
            entry = SRTEntry(
                index=i + 1,
                start_ms=start_ms,
                end_ms=start_ms + 5000,
                text=record.text
            )
            entries.append(entry)
        
        wav_folder = os.path.join(self.output_folder, 'wav')
        output_file = os.path.join(self.output_folder, 'single_clips.fcpxml')
        
        exporter = FCPXMLExporter(self.fps)
        if exporter.export(entries, wav_folder, output_file):
            self.status_message.emit(f"FCPXML 내보내기 완료: {len(records)}개 클립")
            QMessageBox.information(
                self, "완료",
                f"FCPXML 파일이 생성되었습니다:\n{output_file}"
            )
        else:
            QMessageBox.warning(self, "오류", "FCPXML 내보내기에 실패했습니다.")
    
    def refresh_api_status(self):
        """API 상태 갱신"""
        self.tts_engine.set_credentials(config.client_id, config.client_secret)
        self._update_buttons()
