# ui/tabs/script_converter_tab.py
# PDF 대본 → SRT 변환 탭

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QSpinBox, QComboBox, QFileDialog,
    QHeaderView, QAbstractItemView, QMessageBox,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent

from ..styles import (
    COLORS, FONTS, RADIUS,
    get_button_style, get_table_style, get_checkbox_style,
    get_combobox_style, get_input_style
)
from ..widgets import CollapsibleSection

try:
    from ...core import PDFParser, ScriptEntry
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    PDFParser = None
    ScriptEntry = None

from ...core import SRTGenerator, Validator

try:
    from ...core import XLSXExporter
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False


class PDFDropZone(QFrame):
    """PDF 드롭존"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.loaded_file = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px dashed {COLORS['border_light']};
                border-radius: {RADIUS['lg']};
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: rgba(16, 185, 129, 0.03);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(16)
        
        # 상태 텍스트
        self.label = QLabel("PDF 대본 파일을 드래그하거나 선택하세요")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_base']};")
        layout.addWidget(self.label, 1)
        
        # 선택 버튼
        self.btn_select = QPushButton("파일 선택")
        self.btn_select.setStyleSheet(get_button_style('primary'))
        self.btn_select.setFixedWidth(100)
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_file)
        layout.addWidget(self.btn_select)
    
    def select_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "PDF 파일 선택", "", "PDF Files (*.pdf)"
        )
        if filepath:
            self.file_dropped.emit(filepath)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: rgba(16, 185, 129, 0.08);
                        border: 2px dashed {COLORS['accent_primary']};
                        border-radius: {RADIUS['lg']};
                    }}
                """)
    
    def dragLeaveEvent(self, event):
        if not self.loaded_file:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border: 2px dashed {COLORS['border_light']};
                    border-radius: {RADIUS['lg']};
                }}
            """)
    
    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filepath = url.toLocalFile()
            if filepath.lower().endswith('.pdf'):
                self.file_dropped.emit(filepath)
    
    def set_loaded(self, filename: str):
        """파일 로드 상태"""
        self.loaded_file = filename
        self.label.setText(f"로드됨: {filename}")
        self.label.setStyleSheet(f"color: {COLORS['accent_success']}; font-size: {FONTS['size_base']}; font-weight: 600;")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(16, 185, 129, 0.05);
                border: 2px solid {COLORS['accent_success']};
                border-radius: {RADIUS['lg']};
            }}
        """)
    
    def reset(self):
        """초기 상태로"""
        self.loaded_file = None
        self.label.setText("PDF 대본 파일을 드래그하거나 선택하세요")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_base']};")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px dashed {COLORS['border_light']};
                border-radius: {RADIUS['lg']};
            }}
        """)


class ScriptConverterTab(QWidget):
    """대본 → SRT 변환 탭"""
    
    status_message = pyqtSignal(str)
    srt_ready = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.generator = SRTGenerator()
        self.validator = Validator()
        self.entries = []
        self.original_entries = []  # 검증용 원본 보관
        self.output_folder = None
        self.current_pdf = None
        self.last_saved_srt = None
        self.last_saved_xlsx = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 12, 0, 0)
        
        # === 드롭존 ===
        self.drop_zone = PDFDropZone()
        self.drop_zone.file_dropped.connect(self.on_pdf_dropped)
        self.drop_zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.drop_zone)
        
        # === 옵션 영역 ===
        options_frame = QFrame()
        options_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
        """)
        options_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(16, 10, 16, 10)
        options_layout.setSpacing(16)
        
        # 체크박스들
        self.chk_remove_slash = QCheckBox("'/' 제거")
        self.chk_remove_slash.setChecked(True)
        self.chk_remove_slash.setStyleSheet(get_checkbox_style())
        options_layout.addWidget(self.chk_remove_slash)
        
        self.chk_remove_period = QCheckBox("'.' 제거")
        self.chk_remove_period.setChecked(False)
        self.chk_remove_period.setStyleSheet(get_checkbox_style())
        options_layout.addWidget(self.chk_remove_period)
        
        self.chk_include_brackets = QCheckBox("지시어 포함")
        self.chk_include_brackets.setChecked(True)
        self.chk_include_brackets.setStyleSheet(get_checkbox_style())
        options_layout.addWidget(self.chk_include_brackets)
        
        self.chk_break_period = QCheckBox("마침표 줄바꿈")
        self.chk_break_period.setChecked(True)
        self.chk_break_period.setStyleSheet(get_checkbox_style())
        options_layout.addWidget(self.chk_break_period)
        
        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background-color: {COLORS['border_default']};")
        sep.setFixedWidth(1)
        options_layout.addWidget(sep)
        
        # 줄당 글자 수
        chars_label = QLabel("줄당 음절:")
        chars_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        options_layout.addWidget(chars_label)
        
        self.spin_chars = QSpinBox()
        self.spin_chars.setRange(20, 80)
        self.spin_chars.setValue(35)
        self.spin_chars.setFixedWidth(80)
        self.spin_chars.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        options_layout.addWidget(self.spin_chars)
        
        # FPS
        fps_label = QLabel("FPS:")
        fps_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        options_layout.addWidget(fps_label)
        
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["24", "23.976", "25", "30"])
        self.combo_fps.setFixedWidth(110)
        self.combo_fps.setStyleSheet(get_combobox_style())
        options_layout.addWidget(self.combo_fps)
        
        options_layout.addStretch()
        
        # 분석 버튼
        self.btn_parse = QPushButton("대본 분석")
        self.btn_parse.setStyleSheet(get_button_style('primary'))
        self.btn_parse.setFixedWidth(100)
        self.btn_parse.clicked.connect(self.parse_script)
        self.btn_parse.setEnabled(False)
        options_layout.addWidget(self.btn_parse)
        
        layout.addWidget(options_frame)
        
        # === 추출 결과 (접힘/펼침) ===
        self.result_section = CollapsibleSection("추출 결과 (0개 항목)", expanded=True)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "타임코드", "지시사항", "음성해설 대본"])
        self.table.setStyleSheet(get_table_style())
        self.table.setMinimumHeight(250)
        
        # 스크롤 정책 설정
        from PyQt6.QtWidgets import QAbstractScrollArea
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        
        # 컬럼 크기 설정
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 140)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # 테이블 편집 활성화
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.itemChanged.connect(self._on_item_changed)
        
        self.result_section.set_content(self.table)
        layout.addWidget(self.result_section, 1)

        # === 검증 결과 라벨 ===
        self.label_validation = QLabel("")
        self.label_validation.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        layout.addWidget(self.label_validation)

        # === 행 편집 버튼 ===
        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.setSpacing(8)
        
        self.btn_add_row = QPushButton("+ 행 추가")
        self.btn_add_row.setStyleSheet(get_button_style('secondary', 'sm'))
        self.btn_add_row.setFixedWidth(90)
        self.btn_add_row.clicked.connect(self._add_row)
        self.btn_add_row.setEnabled(False)
        self.btn_add_row.setToolTip("선택한 행 아래에 새 행 추가")
        edit_btn_layout.addWidget(self.btn_add_row)
        
        self.btn_delete_row = QPushButton("− 행 삭제")
        self.btn_delete_row.setStyleSheet(get_button_style('secondary', 'sm'))
        self.btn_delete_row.setFixedWidth(90)
        self.btn_delete_row.clicked.connect(self._delete_row)
        self.btn_delete_row.setEnabled(False)
        self.btn_delete_row.setToolTip("선택한 행 삭제")
        edit_btn_layout.addWidget(self.btn_delete_row)
        
        edit_btn_layout.addStretch()
        
        self.label_edit_hint = QLabel("더블클릭으로 셀 편집")
        self.label_edit_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        edit_btn_layout.addWidget(self.label_edit_hint)
        
        layout.addLayout(edit_btn_layout)
        
        # 행 선택 시그널
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        # === 하단 버튼 ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 자동 저장 상태
        self.label_auto_save = QLabel("")
        self.label_auto_save.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: {FONTS['size_sm']};")
        btn_layout.addWidget(self.label_auto_save)
        
        btn_layout.addStretch()
        
        self.btn_xlsx = QPushButton("XLSX 저장")
        self.btn_xlsx.setStyleSheet(get_button_style('secondary'))
        self.btn_xlsx.setFixedWidth(100)
        self.btn_xlsx.clicked.connect(self.export_xlsx)
        self.btn_xlsx.setEnabled(False)
        btn_layout.addWidget(self.btn_xlsx)
        
        self.btn_srt = QPushButton("SRT 저장")
        self.btn_srt.setStyleSheet(get_button_style('secondary'))
        self.btn_srt.setFixedWidth(100)
        self.btn_srt.clicked.connect(self.export_srt)
        self.btn_srt.setEnabled(False)
        btn_layout.addWidget(self.btn_srt)
        
        self.btn_to_tts = QPushButton("TTS 탭으로 전송")
        self.btn_to_tts.setStyleSheet(get_button_style('primary'))
        self.btn_to_tts.setFixedWidth(130)
        self.btn_to_tts.clicked.connect(self.send_to_tts)
        self.btn_to_tts.setEnabled(False)
        btn_layout.addWidget(self.btn_to_tts)
        
        layout.addLayout(btn_layout)
    
    def on_pdf_dropped(self, filepath: str):
        """PDF 파일 드롭/선택"""
        if not HAS_PDF:
            QMessageBox.warning(
                self, "경고", 
                "PyMuPDF가 설치되지 않았습니다.\n\npip install PyMuPDF"
            )
            return
        
        self.current_pdf = filepath
        filename = os.path.basename(filepath)
        self.drop_zone.set_loaded(filename)
        self.btn_parse.setEnabled(True)
        self.status_message.emit(f"PDF 로드: {filename}")
    
    def parse_script(self):
        """PDF에서 대본 파싱"""
        if not self.current_pdf:
            return
        
        try:
            pdf_parser = PDFParser()
            self.entries = pdf_parser.parse(
                self.current_pdf,
                remove_slashes=self.chk_remove_slash.isChecked(),
                remove_periods=self.chk_remove_period.isChecked(),
                include_brackets=self.chk_include_brackets.isChecked()
            )
            
            if not self.entries:
                QMessageBox.warning(
                    self, "경고",
                    "음성해설 대본을 찾을 수 없습니다.\n"
                    "PDF에 밑줄이 그어진 텍스트가 있는지 확인하세요."
                )
                return

            # 검증용 원본 보관 (깊은 복사)
            import copy
            self.original_entries = copy.deepcopy(self.entries)

            self._update_table()
            self._enable_buttons(True)
            self.result_section.set_title(f"추출 결과 ({len(self.entries)}개 항목)")
            self.status_message.emit(f"대본 분석 완료: {len(self.entries)}개 항목")

            # 자동 저장 + 검증
            self._auto_save()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"PDF 파싱 실패:\n{str(e)}")
    
    def _auto_save(self):
        """출력폴더에 자동 저장"""
        if not self.output_folder or not self.entries:
            return

        base_name = os.path.splitext(os.path.basename(self.current_pdf))[0]
        saved_files = []

        # XLSX 저장
        if HAS_XLSX:
            try:
                xlsx_path = os.path.join(self.output_folder, f"{base_name}.xlsx")
                exporter = XLSXExporter()
                exporter.export(self.entries, xlsx_path)
                self.last_saved_xlsx = xlsx_path
                saved_files.append("XLSX")
            except Exception as e:
                self.status_message.emit(f"XLSX 자동 저장 실패: {e}")

        # SRT 저장
        try:
            srt_path = os.path.join(self.output_folder, f"{base_name}.srt")
            content = self.generator.generate(
                self.entries,
                max_chars_per_line=self.spin_chars.value(),
                break_on_period=self.chk_break_period.isChecked(),
                remove_brackets=not self.chk_include_brackets.isChecked()
            )
            self.generator.save(content, srt_path)
            self.last_saved_srt = srt_path
            saved_files.append("SRT")
        except Exception as e:
            self.status_message.emit(f"SRT 자동 저장 실패: {e}")

        if saved_files:
            self.label_auto_save.setText(f"자동 저장됨: {', '.join(saved_files)}")
            self.status_message.emit(f"자동 저장 완료: {', '.join(saved_files)}")

        # === 검증 실행 ===
        self._run_validation(base_name)

    def _run_validation(self, base_name: str):
        """PDF → SRT 변환 검증 실행"""
        if not self.original_entries or not self.entries:
            return

        try:
            # 검증 실행
            result = self.validator.validate(
                original_entries=self.original_entries,
                converted_entries=self.entries,
                pdf_path=self.current_pdf,
                srt_path=self.last_saved_srt
            )

            # UI에 결과 표시
            summary_text = result.get_summary_text()

            # 검증 실패 시 경고 색상
            if result.is_valid:
                self.label_validation.setStyleSheet(
                    f"color: {COLORS['accent_success']}; font-size: {FONTS['size_sm']};"
                )
            else:
                self.label_validation.setStyleSheet(
                    f"color: {COLORS['accent_warning']}; font-size: {FONTS['size_sm']};"
                )

            self.label_validation.setText(summary_text)

            # 검증 보고서 저장
            if self.output_folder:
                report_path = os.path.join(self.output_folder, f"{base_name}_validation.txt")
                self.validator.save_report(report_path)

            # 검증 실패 시 경고 메시지
            if not result.is_valid:
                warning_msg = "검증 결과 불일치가 발견되었습니다:\n\n"
                if not result.timecode_match:
                    diff = result.timecode_converted - result.timecode_original
                    warning_msg += f"- 타임코드: {result.timecode_original}개 → {result.timecode_converted}개 ({diff:+d})\n"
                if not result.syllable_match:
                    diff = result.syllable_converted - result.syllable_original
                    warning_msg += f"- 음절수: {result.syllable_original:,} → {result.syllable_converted:,} ({diff:+d})\n"
                warning_msg += f"\n검증 보고서: {base_name}_validation.txt"

                QMessageBox.warning(self, "검증 경고", warning_msg)

        except Exception as e:
            self.status_message.emit(f"검증 실패: {e}")

    def _update_table(self):
        """테이블 업데이트"""
        self.table.setRowCount(len(self.entries))
        
        mono_font = QFont("SF Mono, Consolas, monospace")
        mono_font.setPointSize(11)
        
        for row, entry in enumerate(self.entries):
            # 번호
            item_num = QTableWidgetItem(str(entry.index))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setForeground(QColor(COLORS['text_muted']))
            self.table.setItem(row, 0, item_num)
            
            # 타임코드
            item_tc = QTableWidgetItem(entry.timecode_formatted)
            item_tc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tc.setForeground(QColor(COLORS['accent_primary']))
            item_tc.setFont(mono_font)
            self.table.setItem(row, 1, item_tc)
            
            # 지시사항
            item_bracket = QTableWidgetItem(entry.bracket_content if entry.bracket_content else "-")
            item_bracket.setForeground(QColor(COLORS['accent_warning'] if entry.bracket_content else COLORS['text_muted']))
            self.table.setItem(row, 2, item_bracket)
            
            # 대본
            item_script = QTableWidgetItem(entry.script_text)
            item_script.setForeground(QColor(COLORS['text_primary']))
            self.table.setItem(row, 3, item_script)
        
        self.table.resizeRowsToContents()
    
    def _enable_buttons(self, enabled: bool):
        """버튼 활성화"""
        self.btn_xlsx.setEnabled(enabled and HAS_XLSX)
        self.btn_srt.setEnabled(enabled)
        self.btn_to_tts.setEnabled(enabled)
    
    def export_xlsx(self):
        """XLSX 내보내기"""
        if not self.entries:
            return
        
        default_name = os.path.splitext(os.path.basename(self.current_pdf))[0] + ".xlsx"
        default_path = os.path.join(self.output_folder, default_name) if self.output_folder else default_name
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "XLSX 저장", default_path, "Excel Files (*.xlsx)"
        )
        
        if filepath:
            try:
                exporter = XLSXExporter()
                exporter.export(self.entries, filepath)
                self.last_saved_xlsx = filepath
                self.status_message.emit(f"XLSX 저장 완료: {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"XLSX 저장 실패:\n{str(e)}")
    
    def export_srt(self):
        """SRT 내보내기"""
        if not self.entries:
            return
        
        default_name = os.path.splitext(os.path.basename(self.current_pdf))[0] + ".srt"
        default_path = os.path.join(self.output_folder, default_name) if self.output_folder else default_name
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "SRT 저장", default_path, "SRT Files (*.srt)"
        )
        
        if filepath:
            try:
                content = self.generator.generate(
                    self.entries,
                    max_chars_per_line=self.spin_chars.value(),
                    break_on_period=self.chk_break_period.isChecked(),
                    remove_brackets=not self.chk_include_brackets.isChecked()
                )
                self.generator.save(content, filepath)
                self.last_saved_srt = filepath
                self.status_message.emit(f"SRT 저장 완료: {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"SRT 저장 실패:\n{str(e)}")
    
    def send_to_tts(self):
        """TTS 탭으로 전송"""
        if not self.entries:
            return
        
        # 자동 저장된 SRT가 있으면 그것을 사용
        if self.last_saved_srt and os.path.exists(self.last_saved_srt):
            self.srt_ready.emit(self.last_saved_srt)
            self.status_message.emit("SRT가 TTS 탭으로 전송되었습니다.")
            return
        
        # 없으면 임시 파일 생성
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_srt = os.path.join(temp_dir, "tomato_ad_temp.srt")
        
        content = self.generator.generate(
            self.entries,
            max_chars_per_line=self.spin_chars.value(),
            break_on_period=self.chk_break_period.isChecked(),
            remove_brackets=not self.chk_include_brackets.isChecked()
        )
        
        self.generator.save(content, temp_srt)
        self.srt_ready.emit(temp_srt)
        self.status_message.emit("SRT가 TTS 탭으로 전송되었습니다.")
    
    def set_fps(self, fps: float):
        """FPS 설정"""
        fps_str = str(fps) if fps != int(fps) else str(int(fps))
        index = self.combo_fps.findText(fps_str)
        if index >= 0:
            self.combo_fps.setCurrentIndex(index)
        self.generator.set_fps(fps)
    
    def set_output_folder(self, folder: str):
        """출력 폴더 설정"""
        self.output_folder = folder
    
    def get_last_saved_srt(self) -> str:
        """마지막 저장된 SRT 경로 반환"""
        return self.last_saved_srt
    
    def _on_row_selected(self):
        """행 선택 시 버튼 활성화"""
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_add_row.setEnabled(has_selection or len(self.entries) > 0)
        self.btn_delete_row.setEnabled(has_selection)
    
    def _add_row(self):
        """선택된 행 아래에 새 행 추가"""
        if not self.entries:
            return
        
        # 선택된 행 찾기
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            insert_at = selected_rows[0].row() + 1
        else:
            insert_at = len(self.entries)
        
        # 새 엔트리 생성 (이전 행의 타임코드 + 1초)
        if insert_at > 0 and insert_at <= len(self.entries):
            prev_entry = self.entries[insert_at - 1]
            new_tc_ms = prev_entry.timecode_ms + 1000
        else:
            new_tc_ms = 0
        
        # 타임코드 변환
        hours = new_tc_ms // 3600000
        minutes = (new_tc_ms % 3600000) // 60000
        seconds = (new_tc_ms % 60000) // 1000
        tc_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}:00"
        tc_raw = f"{minutes:02d}{seconds:02d}"
        
        # ScriptEntry 생성
        new_entry = ScriptEntry(
            index=insert_at + 1,
            timecode_raw=tc_raw,
            timecode_formatted=tc_formatted,
            timecode_ms=new_tc_ms,
            bracket_content="",
            script_text="새 대본 텍스트"
        )
        
        # entries 리스트에 삽입
        self.entries.insert(insert_at, new_entry)
        
        # 인덱스 재정렬
        for i, entry in enumerate(self.entries):
            self.entries[i] = ScriptEntry(
                index=i + 1,
                timecode_raw=entry.timecode_raw,
                timecode_formatted=entry.timecode_formatted,
                timecode_ms=entry.timecode_ms,
                bracket_content=entry.bracket_content,
                script_text=entry.script_text
            )
        
        # 테이블 갱신
        self._update_table()
        
        # 새 행 선택
        self.table.selectRow(insert_at)
        self.status_message.emit(f"행 추가됨: #{insert_at + 1}")
    
    def _delete_row(self):
        """선택된 행 삭제"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.entries):
            return
        
        # 확인
        reply = QMessageBox.question(
            self, "행 삭제",
            f"#{row + 1} 행을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # entries에서 삭제
        del self.entries[row]
        
        # 인덱스 재정렬
        for i, entry in enumerate(self.entries):
            self.entries[i] = ScriptEntry(
                index=i + 1,
                timecode_raw=entry.timecode_raw,
                timecode_formatted=entry.timecode_formatted,
                timecode_ms=entry.timecode_ms,
                bracket_content=entry.bracket_content,
                script_text=entry.script_text
            )
        
        # 테이블 갱신
        self._update_table()
        self.status_message.emit(f"행 삭제됨")
        
        # 버튼 상태 갱신
        self._on_row_selected()
    
    def _on_item_changed(self, item):
        """셀 편집 후 entries 업데이트"""
        row = item.row()
        col = item.column()
        
        if row >= len(self.entries):
            return
        
        entry = self.entries[row]
        
        # 편집 가능한 컬럼: 1(타임코드), 2(지시사항), 3(대본)
        if col == 1:
            # 타임코드 변경 - HH:MM:SS:FF 형식
            new_tc = item.text()
            try:
                parts = new_tc.split(':')
                if len(parts) == 4:
                    h, m, s, f = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                    new_ms = (h * 3600 + m * 60 + s) * 1000
                    self.entries[row] = ScriptEntry(
                        index=entry.index,
                        timecode_raw=entry.timecode_raw,
                        timecode_formatted=new_tc,
                        timecode_ms=new_ms,
                        bracket_content=entry.bracket_content,
                        script_text=entry.script_text
                    )
            except:
                pass
        elif col == 2:
            # 지시사항 변경
            self.entries[row] = ScriptEntry(
                index=entry.index,
                timecode_raw=entry.timecode_raw,
                timecode_formatted=entry.timecode_formatted,
                timecode_ms=entry.timecode_ms,
                bracket_content=item.text(),
                script_text=entry.script_text
            )
        elif col == 3:
            # 대본 변경
            self.entries[row] = ScriptEntry(
                index=entry.index,
                timecode_raw=entry.timecode_raw,
                timecode_formatted=entry.timecode_formatted,
                timecode_ms=entry.timecode_ms,
                bracket_content=entry.bracket_content,
                script_text=item.text()
            )

