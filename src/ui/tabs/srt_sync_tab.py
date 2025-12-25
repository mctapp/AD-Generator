# ui/tabs/srt_sync_tab.py
# SRT-WAV 동기화 탭

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QHeaderView, QAbstractItemView, 
    QMessageBox, QFrame, QDialog, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent

from ..styles import COLORS, FONTS, RADIUS, get_button_style, get_table_style
from ..widgets import CollapsibleSection, WaveformWidget
from ...core import SRTSync
from ...utils import ms_to_filename_tc

try:
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False


class SRTDropZone(QFrame):
    """SRT 드롭존"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, label_text="선택되지 않음", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.filepath = None
        self.default_text = label_text
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        self.label = QLabel(self.default_text)
        self.label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(self.label, 1)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.toLocalFile().lower().endswith('.srt'):
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: rgba(16, 185, 129, 0.1);
                        border: 2px dashed {COLORS['accent_primary']};
                        border-radius: {RADIUS['md']};
                    }}
                """)
    
    def dragLeaveEvent(self, event):
        self._reset_style()
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filepath = url.toLocalFile()
            if filepath.lower().endswith('.srt'):
                self.set_file(filepath)
                self.file_dropped.emit(filepath)
        self._reset_style()
    
    def set_file(self, filepath: str):
        """파일 설정"""
        self.filepath = filepath
        filename = os.path.basename(filepath)
        self.label.setText(filename)
        self.label.setToolTip(filepath)
        self.label.setStyleSheet(f"color: {COLORS['accent_success']}; font-weight: 600;")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['accent_success']};
                border-radius: {RADIUS['md']};
            }}
        """)
    
    def _reset_style(self):
        if self.filepath:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_tertiary']};
                    border: 1px solid {COLORS['accent_success']};
                    border-radius: {RADIUS['md']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_tertiary']};
                    border: 1px solid {COLORS['border_default']};
                    border-radius: {RADIUS['md']};
                }}
            """)
    
    def clear(self):
        self.filepath = None
        self.label.setText(self.default_text)
        self.label.setToolTip("")
        self.label.setStyleSheet(f"color: {COLORS['text_muted']};")
        self._reset_style()


class OverlapReportDialog(QDialog):
    """겹치는 자막 보고 다이얼로그"""
    
    def __init__(self, overlaps: list, fps: float = 24, parent=None):
        super().__init__(parent)
        self.setWindowTitle("겹치는 자막 보고")
        self.setMinimumSize(600, 400)
        self.fps = fps
        
        layout = QVBoxLayout(self)
        
        label = QLabel(f"총 {len(overlaps)}개의 겹침 발견:")
        label.setStyleSheet(f"color: {COLORS['accent_warning']}; font-weight: 600;")
        layout.addWidget(label)
        
        self.text_edit = QTextEdit()
        
        lines = []
        for item in overlaps:
            overlap_ms = item['overlap_ms']
            overlap_sec = overlap_ms / 1000
            overlap_frames = int(overlap_ms / 1000 * fps)
            
            lines.append(f"#{item['index']} [{item['timecode']}]")
            lines.append(f"  현재 종료: {item['end_time']}ms")
            lines.append(f"  다음 시작: {item['next_start']}ms")
            lines.append(f"  겹침: {overlap_ms}ms ({overlap_sec:.2f}초 / {overlap_frames}프레임)")
            lines.append("")
        
        self.text_edit.setPlainText("\n".join(lines))
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
        QApplication.clipboard().setText(self.text_edit.toPlainText())


class SRTSyncTab(QWidget):
    """SRT-WAV 동기화 탭"""
    
    status_message = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sync = SRTSync()
        self.srt_path = None
        self.wav_folder = None
        self.fps = 24
        self.last_overlaps = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)
        
        # === 파일 선택 영역 ===
        file_frame = QFrame()
        file_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['lg']};
            }}
        """)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(16, 16, 16, 16)
        file_layout.setSpacing(12)

        # SRT 파일 선택 (드래그앤드롭 지원)
        srt_layout = QHBoxLayout()
        srt_layout.setSpacing(12)
        
        srt_label = QLabel("원본 SRT")
        srt_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']};")
        srt_label.setFixedWidth(80)
        srt_layout.addWidget(srt_label)
        
        self.srt_drop = SRTDropZone("SRT 파일을 드래그하거나 선택하세요")
        self.srt_drop.file_dropped.connect(self._on_srt_dropped)
        srt_layout.addWidget(self.srt_drop, 1)
        
        self.btn_srt = QPushButton("파일 선택")
        self.btn_srt.setStyleSheet(get_button_style('primary'))
        self.btn_srt.setFixedWidth(100)
        self.btn_srt.clicked.connect(self.select_srt)
        srt_layout.addWidget(self.btn_srt)
        
        file_layout.addLayout(srt_layout)
        
        # WAV 폴더 선택
        wav_layout = QHBoxLayout()
        wav_layout.setSpacing(12)
        
        wav_label = QLabel("WAV 폴더")
        wav_label.setStyleSheet(f"font-weight: 600; color: {COLORS['text_secondary']};")
        wav_label.setFixedWidth(80)
        wav_layout.addWidget(wav_label)
        
        self.label_wav = QLabel("선택되지 않음")
        self.label_wav.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 8px 12px;
        """)
        wav_layout.addWidget(self.label_wav, 1)
        
        self.btn_wav = QPushButton("폴더 선택")
        self.btn_wav.setStyleSheet(get_button_style('primary'))
        self.btn_wav.setFixedWidth(100)
        self.btn_wav.clicked.connect(self.select_wav_folder)
        wav_layout.addWidget(self.btn_wav)
        
        file_layout.addLayout(wav_layout)
        
        # 분석 버튼 행 (설명 텍스트 + 버튼)
        analyze_layout = QHBoxLayout()

        # 설명 텍스트 (왼쪽)
        desc_label = QLabel("SRT 파일의 종료 시간을 WAV 파일 길이에 맞게 동기화합니다.")
        desc_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        analyze_layout.addWidget(desc_label)

        analyze_layout.addStretch()

        self.btn_analyze = QPushButton("분석")
        self.btn_analyze.setStyleSheet(get_button_style('secondary'))
        self.btn_analyze.setFixedWidth(100)
        self.btn_analyze.clicked.connect(self.analyze)
        self.btn_analyze.setEnabled(False)
        analyze_layout.addWidget(self.btn_analyze)
        
        file_layout.addLayout(analyze_layout)
        
        layout.addWidget(file_frame)

        # 요약 정보 (테두리 없음)
        self.label_summary = QLabel("")
        self.label_summary.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        layout.addWidget(self.label_summary)

        # === 분석 결과 (접힘/펼침) ===
        self.result_section = CollapsibleSection("분석 결과", expanded=True)

        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)

        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "타임코드", "원본 길이", "WAV 길이", "차이", "상태"
        ])
        self.table.setStyleSheet(get_table_style())
        self.table.setMinimumHeight(250)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 80)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # 행 선택 시 파형 표시
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        result_layout.addWidget(self.table)

        # 파형 미리보기 위젯
        self.waveform = WaveformWidget()
        result_layout.addWidget(self.waveform)

        self.result_section.set_content(result_widget)
        layout.addWidget(self.result_section, 1)
        
        # === 하단 버튼 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 겹침 보기 버튼
        self.btn_show_overlaps = QPushButton("겹치는 자막 보기")
        self.btn_show_overlaps.setStyleSheet(get_button_style('secondary'))
        self.btn_show_overlaps.setFixedWidth(120)
        self.btn_show_overlaps.clicked.connect(self.show_overlaps)
        self.btn_show_overlaps.setVisible(False)
        btn_layout.addWidget(self.btn_show_overlaps)
        
        btn_layout.addStretch()
        
        self.btn_report = QPushButton("리포트 저장")
        self.btn_report.setStyleSheet(get_button_style('secondary'))
        self.btn_report.setFixedWidth(110)
        self.btn_report.clicked.connect(self.save_report)
        self.btn_report.setEnabled(False)
        btn_layout.addWidget(self.btn_report)
        
        self.btn_save = QPushButton("동기화된 SRT 저장")
        self.btn_save.setStyleSheet(get_button_style('primary'))
        self.btn_save.setFixedWidth(150)
        self.btn_save.clicked.connect(self.save_synced_srt)
        self.btn_save.setEnabled(False)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
    
    def _on_srt_dropped(self, filepath: str):
        """SRT 드롭 처리"""
        self.srt_path = filepath
        self._update_analyze_button()
        self.status_message.emit(f"SRT 로드: {os.path.basename(filepath)}")
    
    def select_srt(self):
        """SRT 파일 선택"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "SRT 파일 선택", "", "SRT Files (*.srt)"
        )
        if filepath:
            self.srt_path = filepath
            self.srt_drop.set_file(filepath)
            self._update_analyze_button()
            self.status_message.emit(f"SRT 로드: {os.path.basename(filepath)}")
    
    def select_wav_folder(self):
        """WAV 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(self, "WAV 폴더 선택")
        if folder:
            self._set_wav_folder(folder)
    
    def _set_wav_folder(self, folder: str):
        """WAV 폴더 설정"""
        self.wav_folder = folder
        folder_name = os.path.basename(folder)
        self.label_wav.setText(folder_name)
        self.label_wav.setToolTip(folder)
        self.label_wav.setStyleSheet(f"""
            color: {COLORS['accent_success']};
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['accent_success']};
            border-radius: {RADIUS['md']};
            padding: 8px 12px;
        """)
        self._update_analyze_button()
        self.status_message.emit(f"WAV 폴더: {folder_name}")
    
    def _update_analyze_button(self):
        """분석 버튼 상태 업데이트"""
        self.btn_analyze.setEnabled(
            self.srt_path is not None and self.wav_folder is not None
        )
    
    def analyze(self):
        """분석 실행"""
        if not self.srt_path or not self.wav_folder:
            return
        
        try:
            # FPS 설정 후 분석
            self.sync.set_fps(self.fps)
            self.sync.analyze(self.srt_path, self.wav_folder)
            
            self._update_table()
            self._check_overlaps()
            
            self.btn_save.setEnabled(True)
            self.btn_report.setEnabled(True)
            
            summary = self.sync.get_summary()
            self.result_section.set_title(f"분석 결과 ({summary['total']}개 항목)")
            self.label_summary.setText(
                f"일치: {summary['synced']}개  |  "
                f"초과: {summary['longer']}개  |  "
                f"여유: {summary['shorter']}개  |  "
                f"누락: {summary['missing']}개"
            )
            
            # 자동 저장
            self._auto_save_synced_srt()
            
            self.status_message.emit(f"분석 완료: {summary['total']}개 항목")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"분석 실패:\n{str(e)}")
    
    def _auto_save_synced_srt(self):
        """동기화된 SRT 자동 저장"""
        if not self.sync.results or not self.srt_path:
            return
        
        try:
            # 출력 경로 생성
            base_name = os.path.splitext(os.path.basename(self.srt_path))[0]
            output_dir = os.path.dirname(self.srt_path)
            
            # _synced 접미사 추가 (이미 있으면 덮어쓰기)
            if not base_name.endswith('_synced'):
                output_name = f"{base_name}_synced.srt"
            else:
                output_name = f"{base_name}.srt"
            
            output_path = os.path.join(output_dir, output_name)
            
            # 저장
            self.sync.save_synced_srt(output_path)
            self.last_saved_path = output_path
            
            # 메시지
            overlap_msg = ""
            if self.last_overlaps:
                overlap_msg = f"\n(경고: {len(self.last_overlaps)}개 겹치는 자막 있음)"
            
            QMessageBox.information(
                self, "분석 완료",
                f"동기화된 SRT가 자동 저장되었습니다:\n{output_name}{overlap_msg}"
            )
            
        except Exception as e:
            # 자동 저장 실패는 경고만
            self.status_message.emit(f"자동 저장 실패: {str(e)}")
    
    def _ms_to_tc(self, ms: int) -> str:
        """밀리초를 타임코드로 변환"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        frames = int((ms % 1000) / 1000 * self.fps)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    def _update_table(self):
        """테이블 업데이트"""
        entries = self.sync.results
        self.table.setRowCount(len(entries))
        
        mono_font = QFont("SF Mono, Consolas, monospace")
        mono_font.setPointSize(11)
        
        for row, entry in enumerate(entries):
            # 번호
            item_num = QTableWidgetItem(str(entry.index))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setForeground(QColor(COLORS['text_muted']))
            self.table.setItem(row, 0, item_num)
            
            # 타임코드
            tc = self._ms_to_tc(entry.start_ms)
            item_tc = QTableWidgetItem(tc)
            item_tc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tc.setForeground(QColor(COLORS['accent_primary']))
            item_tc.setFont(mono_font)
            self.table.setItem(row, 1, item_tc)
            
            # 원본 길이
            orig_duration = entry.original_end_ms - entry.start_ms
            item_orig = QTableWidgetItem(f"{orig_duration}ms")
            item_orig.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_orig.setForeground(QColor(COLORS['text_secondary']))
            self.table.setItem(row, 2, item_orig)
            
            # WAV 길이
            wav_text = f"{entry.wav_duration_ms}ms" if entry.wav_duration_ms else "-"
            item_wav = QTableWidgetItem(wav_text)
            item_wav.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_wav.setForeground(QColor(COLORS['text_secondary']))
            self.table.setItem(row, 3, item_wav)
            
            # 차이
            if entry.diff_ms != 0:
                diff_text = f"+{entry.diff_ms}" if entry.diff_ms > 0 else str(entry.diff_ms)
                item_diff = QTableWidgetItem(f"{diff_text}ms")
                
                if entry.diff_ms > 0:
                    item_diff.setForeground(QColor(COLORS['accent_error']))
                else:
                    item_diff.setForeground(QColor(COLORS['accent_warning']))
            else:
                item_diff = QTableWidgetItem("-")
                item_diff.setForeground(QColor(COLORS['text_muted']))
            
            item_diff.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 4, item_diff)
            
            # 상태
            status_map = {
                'synced': ('OK', COLORS['accent_success']),
                'longer': ('초과', COLORS['accent_error']),
                'shorter': ('여유', COLORS['accent_warning']),
                'missing': ('누락', COLORS['text_muted']),
            }
            status_text, status_color = status_map.get(entry.status, (entry.status, COLORS['text_muted']))
            
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(QColor(status_color))
            self.table.setItem(row, 5, item_status)
        
        self.table.resizeRowsToContents()
    
    def _check_overlaps(self):
        """겹치는 자막 검사"""
        self.last_overlaps = []
        
        entries = self.sync.results
        for i in range(len(entries) - 1):
            current = entries[i]
            next_entry = entries[i + 1]
            
            # 동기화 후 종료 시간 계산
            if current.wav_duration_ms:
                current_end_ms = current.start_ms + current.wav_duration_ms
            else:
                current_end_ms = current.original_end_ms
            
            # 겹침 검사
            if current_end_ms > next_entry.start_ms:
                overlap_ms = current_end_ms - next_entry.start_ms
                self.last_overlaps.append({
                    'index': current.index,
                    'timecode': self._ms_to_tc(current.start_ms),
                    'end_time': f"{current_end_ms}ms",
                    'next_start': f"{next_entry.start_ms}ms",
                    'overlap_ms': overlap_ms
                })
        
        self.btn_show_overlaps.setVisible(len(self.last_overlaps) > 0)
        
        if self.last_overlaps:
            self.status_message.emit(f"경고: {len(self.last_overlaps)}개 겹침 발견")
    
    def show_overlaps(self):
        """겹치는 자막 보기"""
        if self.last_overlaps:
            dialog = OverlapReportDialog(self.last_overlaps, self.fps, self)
            dialog.exec()
    
    def save_synced_srt(self):
        """동기화된 SRT 저장"""
        if not self.sync.results:
            return
        
        default_name = os.path.splitext(os.path.basename(self.srt_path))[0] + "_synced.srt"
        default_path = os.path.join(os.path.dirname(self.srt_path), default_name)
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "동기화된 SRT 저장", default_path, "SRT Files (*.srt)"
        )
        
        if filepath:
            try:
                self.sync.save_synced_srt(filepath)
                self.status_message.emit(f"동기화 SRT 저장: {os.path.basename(filepath)}")
                
                if self.last_overlaps:
                    QMessageBox.warning(
                        self, "경고",
                        f"저장 완료되었지만 {len(self.last_overlaps)}개의 겹치는 자막이 있습니다.\n"
                        "'겹치는 자막 보기' 버튼으로 확인하세요."
                    )
                else:
                    QMessageBox.information(self, "완료", "동기화된 SRT가 저장되었습니다.")
                    
            except Exception as e:
                QMessageBox.critical(self, "오류", f"저장 실패:\n{str(e)}")
    
    def save_report(self):
        """리포트 저장"""
        if not self.sync.results:
            return
        
        default_name = os.path.splitext(os.path.basename(self.srt_path))[0] + "_report.xlsx"
        default_path = os.path.join(os.path.dirname(self.srt_path), default_name)
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "리포트 저장", default_path, "Excel Files (*.xlsx);;Text Files (*.txt)"
        )
        
        if filepath:
            try:
                if filepath.endswith('.xlsx'):
                    self.sync.save_report_xlsx(filepath)
                else:
                    self.sync.save_report_txt(filepath)
                
                self.status_message.emit(f"리포트 저장: {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"리포트 저장 실패:\n{str(e)}")
    
    def set_fps(self, fps: float):
        """FPS 설정"""
        self.fps = fps
        self.sync.set_fps(fps)
    
    def set_wav_folder(self, folder: str):
        """WAV 폴더 자동 설정 (출력 폴더 기반)"""
        wav_path = os.path.join(folder, 'wav')
        if os.path.exists(wav_path):
            self._set_wav_folder(wav_path)
    
    def load_srt(self, srt_path: str):
        """SRT 파일 로드 (외부에서 호출)"""
        if srt_path and os.path.exists(srt_path):
            self.srt_path = srt_path
            self.srt_drop.set_file(srt_path)
            self._update_analyze_button()

    def _on_row_selected(self):
        """테이블 행 선택 시 파형 표시"""
        if not self.wav_folder or not self.sync.results:
            return

        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.waveform.clear()
            return

        row = selected_rows[0].row()
        if row < 0 or row >= len(self.sync.results):
            return

        entry = self.sync.results[row]
        # 타임코드 기반 파일명 생성
        filename = f"{ms_to_filename_tc(entry.start_ms, self.fps)}.wav"
        wav_path = os.path.join(self.wav_folder, filename)

        self.waveform.load_wav(wav_path)
