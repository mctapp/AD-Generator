# ui/tabs/srt_batch_tab.py
# SRT → TTS 일괄 생성 탭

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QMessageBox, QApplication,
    QFrame, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from ..styles import COLORS, FONTS, RADIUS, get_button_style, get_progressbar_style
from ..widgets import DropZone, SRTTable, CollapsibleSection
from ...core import SRTParser, TTSEngine, TTSOptions, OverlapChecker
from ...core import FCPXMLExporter, EDLExporter
from ...utils import config, ms_to_filename_tc


class ErrorReportDialog(QDialog):
    """오류 파일 보고 다이얼로그"""
    
    def __init__(self, title: str, files: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 설명
        label = QLabel(f"총 {len(files)}개 파일:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(label)
        
        # 파일 목록
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("\n".join(files))
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
                padding: 8px;
                font-family: monospace;
            }}
        """)
        layout.addWidget(self.text_edit)
        
        # 버튼
        btn_layout = QHBoxLayout()
        
        btn_copy = QPushButton("복사")
        btn_copy.setStyleSheet(get_button_style('secondary'))
        btn_copy.clicked.connect(self.copy_to_clipboard)
        btn_layout.addWidget(btn_copy)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton("닫기")
        btn_close.setStyleSheet(get_button_style('primary'))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def copy_to_clipboard(self):
        """클립보드에 복사"""
        QApplication.clipboard().setText(self.text_edit.toPlainText())


class TTSWorker(QThread):
    """TTS 생성 워커 스레드"""
    
    progress = pyqtSignal(int, int, str)
    item_complete = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    
    def __init__(self, engine, entries, wav_folder, fps):
        super().__init__()
        self.engine = engine
        self.entries = entries
        self.wav_folder = wav_folder
        self.fps = fps
        self._cancelled = False
    
    def run(self):
        results = {'success': 0, 'failed': 0, 'cancelled': False, 'failed_files': []}
        total = len(self.entries)
        
        for i, entry in enumerate(self.entries):
            if self._cancelled:
                results['cancelled'] = True
                break
            
            filename = f"{ms_to_filename_tc(entry.start_ms, self.fps)}.wav"
            output_path = os.path.join(self.wav_folder, filename)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                results['success'] += 1
                self.progress.emit(i + 1, total, f"기존 파일: {filename}")
                self.item_complete.emit(i, 'skipped')
                continue
            
            self.progress.emit(i + 1, total, f"생성 중: {filename}")
            
            if self.engine.generate_single(entry.text, output_path):
                # 생성 후 0KB 체크
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    results['success'] += 1
                    self.item_complete.emit(i, 'success')
                else:
                    results['failed'] += 1
                    results['failed_files'].append(filename)
                    self.item_complete.emit(i, 'failed')
            else:
                results['failed'] += 1
                results['failed_files'].append(filename)
                self.item_complete.emit(i, 'failed')
            
            if i < total - 1 and not self._cancelled:
                self.msleep(int(self.engine.api_delay * 1000))
        
        self.finished.emit(results)
    
    def cancel(self):
        self._cancelled = True


class SRTBatchTab(QWidget):
    """SRT → TTS 일괄 생성 탭"""
    
    request_output_folder = pyqtSignal()
    request_settings = pyqtSignal()
    status_message = pyqtSignal(str)
    generation_complete = pyqtSignal(str)  # SRT 경로 전달
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.srt_parser = SRTParser()
        self.tts_engine = TTSEngine()
        self.worker = None
        self.output_folder = None
        self.fps = 24
        self.output_format = 'fcpxml'
        self.last_failed_files = []
        self.current_srt_path = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)
        
        # 드롭존
        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self.on_file_dropped)
        self.drop_zone.setMinimumHeight(140)
        layout.addWidget(self.drop_zone)
        
        # SRT 내용 (접힘/펼침)
        self.srt_section = CollapsibleSection("SRT 내용 (0개 항목)", expanded=True)
        self.srt_table = SRTTable()
        self.srt_table.setMinimumHeight(250)
        self.srt_section.set_content(self.srt_table)
        layout.addWidget(self.srt_section, 1)
        
        # 진행 상태 영역 (별도 프레임)
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(16, 12, 16, 12)
        progress_layout.setSpacing(8)
        
        # 상태 라벨
        self.label_progress = QLabel("대기 중")
        self.label_progress.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_base']};")
        progress_layout.addWidget(self.label_progress)
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {RADIUS['sm']};
                background-color: {COLORS['bg_tertiary']};
                text-align: center;
                color: {COLORS['text_primary']};
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent_primary']};
                border-radius: {RADIUS['sm']};
            }}
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 오류 파일 보기 버튼
        self.btn_show_errors = QPushButton("오류 파일 보기")
        self.btn_show_errors.setStyleSheet(get_button_style('secondary'))
        self.btn_show_errors.setFixedWidth(120)
        self.btn_show_errors.clicked.connect(self.show_error_files)
        self.btn_show_errors.setVisible(False)
        btn_layout.addWidget(self.btn_show_errors)
        
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setStyleSheet(get_button_style('secondary'))
        self.btn_cancel.setFixedWidth(80)
        self.btn_cancel.clicked.connect(self.cancel_generation)
        self.btn_cancel.setEnabled(False)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_start = QPushButton("일괄 생성")
        self.btn_start.setStyleSheet(get_button_style('primary'))
        self.btn_start.setFixedWidth(100)
        self.btn_start.clicked.connect(self.start_generation)
        self.btn_start.setEnabled(False)
        btn_layout.addWidget(self.btn_start)
        
        layout.addLayout(btn_layout)
    
    def on_file_dropped(self, filepath):
        """SRT 파일 드롭"""
        try:
            self.current_srt_path = filepath
            entries = self.srt_parser.parse(filepath)
            self.srt_table.load_entries(entries, self.fps)
            self.srt_section.set_title(f"SRT 내용 ({len(entries)}개 항목)")
            self.update_start_button()
            
            folder = os.path.dirname(filepath)
            config.set('app', 'last_srt_folder', folder)
            
            if not self.output_folder:
                self.output_folder = os.path.join(folder, 'output')
            
            self.status_message.emit(f"SRT 로드: {len(entries)}개 항목")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"SRT 파일을 읽을 수 없습니다:\n{str(e)}")
    
    def set_output_folder(self, folder: str):
        self.output_folder = folder
        self.update_start_button()
    
    def set_fps(self, fps: float):
        self.fps = fps
        if self.srt_parser.entries:
            self.srt_table.load_entries(self.srt_parser.entries, fps)
    
    def set_output_format(self, fmt: str):
        self.output_format = fmt
    
    def set_voice_settings(self, settings: dict):
        options = TTSOptions(**settings)
        self.tts_engine.set_options(options)
    
    def update_start_button(self):
        has_entries = len(self.srt_parser.entries) > 0
        has_output = self.output_folder is not None
        has_api = config.has_api_keys()
        
        self.btn_start.setEnabled(has_entries and has_output and has_api)
        
        if not has_api:
            self.btn_start.setToolTip("설정에서 API 키를 입력하세요")
        elif not has_entries:
            self.btn_start.setToolTip("SRT 파일을 불러오세요")
        elif not has_output:
            self.btn_start.setToolTip("출력 폴더를 선택하세요")
        else:
            self.btn_start.setToolTip("")
    
    def start_generation(self):
        if not self.srt_parser.entries:
            return
        
        wav_folder = os.path.join(self.output_folder, 'wav')
        os.makedirs(wav_folder, exist_ok=True)
        
        self.tts_engine.set_credentials(config.client_id, config.client_secret)
        self.tts_engine.api_delay = config.get('app', 'api_delay') or 0.3
        
        self.worker = TTSWorker(
            self.tts_engine,
            self.srt_parser.entries,
            wav_folder,
            self.fps
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.item_complete.connect(self.on_item_complete)
        self.worker.finished.connect(self.on_generation_finished)
        
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.drop_zone.setEnabled(False)
        self.btn_show_errors.setVisible(False)
        self.last_failed_files = []
        
        self.progress_bar.setMaximum(len(self.srt_parser.entries))
        self.progress_bar.setValue(0)
        
        self.worker.start()
    
    def cancel_generation(self):
        if self.worker:
            self.worker.cancel()
            self.label_progress.setText("취소 중...")
    
    def on_progress(self, current, total, message):
        self.progress_bar.setValue(current)
        self.label_progress.setText(f"{current}/{total} - {message}")
        self.srt_table.scroll_to_row(current - 1)
    
    def on_item_complete(self, row, status):
        self.srt_table.update_status(row, status)
    
    def on_generation_finished(self, results):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.drop_zone.setEnabled(True)
        
        if results['cancelled']:
            self.label_progress.setText("취소됨")
            self.status_message.emit("생성 취소됨")
            return
        
        wav_folder = os.path.join(self.output_folder, 'wav')
        
        # 0KB 파일 검사
        zero_kb_files = self._check_zero_kb_files(wav_folder)
        self.last_failed_files = results.get('failed_files', []) + zero_kb_files
        
        if self.last_failed_files:
            self.btn_show_errors.setVisible(True)
        
        # 오버랩 검사
        checker = OverlapChecker(self.fps)
        checker.check(self.srt_parser.entries, wav_folder)
        
        for result in checker.results:
            row = result.index - 1
            if result.status == 'OVER':
                self.srt_table.update_status(row, 'over', result.diff_ms)
            elif result.status == 'OK':
                self.srt_table.update_status(row, 'ok')
        
        # 리포트 저장
        report_path = os.path.join(self.output_folder, 'overlap_report.txt')
        checker.save_report(report_path)
        
        # 타임라인 파일 생성
        if self.output_format == 'fcpxml':
            exporter = FCPXMLExporter(self.fps)
            output_file = os.path.join(self.output_folder, 'ad_import.fcpxml')
        else:
            exporter = EDLExporter(self.fps)
            output_file = os.path.join(self.output_folder, 'ad_import.edl')
        
        exporter.export(self.srt_parser.entries, wav_folder, output_file)
        
        # 완료 메시지
        summary = checker.get_summary()
        msg = f"완료!\n\n"
        msg += f"성공: {results['success']}개\n"
        msg += f"실패: {results['failed']}개\n"
        
        if self.last_failed_files:
            msg += f"\n0KB/오류 파일: {len(self.last_failed_files)}개\n"
        
        msg += f"\n분량 초과: {summary['over']}개\n"
        msg += f"\n출력 폴더: {self.output_folder}"
        
        self.label_progress.setText(f"완료 - {results['success']}개 생성")
        self.status_message.emit(f"일괄 생성 완료: {results['success']}개")
        
        QMessageBox.information(self, "완료", msg)
        
        # 생성 완료 시그널 발생 (통합실행용)
        if self.current_srt_path:
            self.generation_complete.emit(self.current_srt_path)
    
    def _check_zero_kb_files(self, wav_folder: str) -> list:
        """0KB 파일 검사"""
        zero_files = []
        if os.path.exists(wav_folder):
            for f in os.listdir(wav_folder):
                if f.endswith('.wav'):
                    fpath = os.path.join(wav_folder, f)
                    if os.path.getsize(fpath) == 0:
                        zero_files.append(f)
        return zero_files
    
    def show_error_files(self):
        """오류 파일 목록 표시"""
        if self.last_failed_files:
            dialog = ErrorReportDialog(
                "오류/0KB 파일 목록",
                self.last_failed_files,
                self
            )
            dialog.exec()
    
    def refresh_api_status(self):
        self.tts_engine.set_credentials(config.client_id, config.client_secret)
        self.update_start_button()
