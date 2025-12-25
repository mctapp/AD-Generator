# ui/widgets/clip_history.py
# 단일 클립 생성 기록 테이블

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from typing import List
from dataclasses import dataclass


@dataclass
class ClipRecord:
    """클립 생성 기록"""
    timecode: str
    text: str
    filepath: str
    status: str  # 'success', 'failed'


class ClipHistoryTable(QWidget):
    """클립 생성 기록 테이블"""
    
    clip_selected = pyqtSignal(ClipRecord)
    clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.records: List[ClipRecord] = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 헤더
        header_layout = QHBoxLayout()
        self.header_label = QLabel("생성 기록")
        self.header_label.setStyleSheet("font-weight: bold; padding: 5px;")
        header_layout.addWidget(self.header_label)
        
        header_layout.addStretch()
        
        self.btn_clear = QPushButton("기록 삭제")
        self.btn_clear.setFixedWidth(80)
        self.btn_clear.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                font-size: 11px;
                background-color: #555;
                border: none;
                border-radius: 3px;
                color: #ccc;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        self.btn_clear.clicked.connect(self._on_clear)
        header_layout.addWidget(self.btn_clear)
        
        layout.addLayout(header_layout)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "타임코드", "내용", "상태"])
        
        # 컬럼 너비
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 70)
        
        # 선택 모드
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)  # 행 번호 숨김 (중복 방지)
        
        # 스타일
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3a5a7a;
            }
            QHeaderView::section {
                background-color: #333;
                padding: 5px;
                border: none;
                border-bottom: 1px solid #444;
            }
        """)
        
        self.table.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)
    
    def add_record(self, timecode: str, text: str, filepath: str, success: bool):
        """기록 추가"""
        record = ClipRecord(
            timecode=timecode,
            text=text,
            filepath=filepath,
            status='success' if success else 'failed'
        )
        self.records.append(record)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 번호
        item_num = QTableWidgetItem(str(row + 1))
        item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, item_num)
        
        # 타임코드
        item_tc = QTableWidgetItem(timecode)
        item_tc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, item_tc)
        
        # 내용
        display_text = text[:40] + '...' if len(text) > 40 else text
        item_text = QTableWidgetItem(display_text)
        item_text.setToolTip(text)
        self.table.setItem(row, 2, item_text)
        
        # 상태
        if success:
            item_status = QTableWidgetItem("완료")
            item_status.setForeground(QColor("#4CAF50"))
        else:
            item_status = QTableWidgetItem("실패")
            item_status.setForeground(QColor("#F44336"))
        item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, item_status)
        
        # 스크롤
        self.table.scrollToBottom()
        
        # 헤더 업데이트
        self._update_header()
    
    def _update_header(self):
        """헤더 업데이트"""
        count = len(self.records)
        success = sum(1 for r in self.records if r.status == 'success')
        self.header_label.setText(f"생성 기록 ({success}/{count})")
    
    def _on_double_click(self, item):
        """더블클릭 시 레코드 선택"""
        row = item.row()
        if row < len(self.records):
            self.clip_selected.emit(self.records[row])
    
    def _on_clear(self):
        """기록 삭제"""
        self.records = []
        self.table.setRowCount(0)
        self._update_header()
        self.clear_requested.emit()
    
    def get_records(self) -> List[ClipRecord]:
        """모든 기록 반환"""
        return self.records
    
    def get_success_records(self) -> List[ClipRecord]:
        """성공한 기록만 반환"""
        return [r for r in self.records if r.status == 'success']
