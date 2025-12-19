# ui/widgets/srt_table.py
# SRT 항목 테이블

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from typing import List
from ...utils.timecode import ms_to_timecode
from ..styles import COLORS, FONTS, RADIUS, get_table_style


class SRTTable(QWidget):
    """SRT 항목 테이블"""
    
    item_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "타임코드", "내용", "상태"])
        
        # 컬럼 너비 - 내용 컬럼을 최대화
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(3, 70)
        
        # 선택 모드
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # 스타일
        self.table.setStyleSheet(get_table_style())
        
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)
    
    def load_entries(self, entries: List, fps: float = 24):
        """SRT 항목 로드"""
        self.entries = entries
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
            tc = ms_to_timecode(entry.start_ms, fps)
            item_tc = QTableWidgetItem(tc)
            item_tc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tc.setForeground(QColor(COLORS['accent_primary']))
            item_tc.setFont(mono_font)
            self.table.setItem(row, 1, item_tc)
            
            # 내용
            item_text = QTableWidgetItem(entry.text)
            item_text.setToolTip(entry.text)
            item_text.setForeground(QColor(COLORS['text_primary']))
            self.table.setItem(row, 2, item_text)
            
            # 상태
            item_status = QTableWidgetItem("대기")
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setForeground(QColor(COLORS['text_muted']))
            self.table.setItem(row, 3, item_status)
    
    def update_status(self, row: int, status: str, diff_ms: int = 0):
        """항목 상태 업데이트"""
        if row < 0 or row >= self.table.rowCount():
            return
        
        item = self.table.item(row, 3)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, 3, item)
        
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if status == 'processing':
            item.setText("생성중")
            item.setForeground(QColor(COLORS['accent_warning']))
        elif status == 'success':
            item.setText("OK")
            item.setForeground(QColor(COLORS['accent_success']))
        elif status == 'skipped':
            item.setText("OK")
            item.setForeground(QColor(COLORS['accent_success']))
        elif status == 'failed':
            item.setText("실패")
            item.setForeground(QColor(COLORS['accent_error']))
        elif status == 'over':
            diff_sec = diff_ms / 1000
            item.setText(f"+{diff_sec:.1f}s")
            item.setForeground(QColor(COLORS['accent_warning']))
            for col in range(self.table.columnCount()):
                cell = self.table.item(row, col)
                if cell:
                    cell.setBackground(QColor("#3a3020"))
        elif status == 'ok':
            item.setText("OK")
            item.setForeground(QColor(COLORS['accent_success']))
        else:
            item.setText(status)
    
    def scroll_to_row(self, row: int):
        if row >= 0 and row < self.table.rowCount():
            self.table.scrollToItem(self.table.item(row, 0))
    
    def on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.item_selected.emit(rows[0].row())
    
    def get_selected_entry(self):
        rows = self.table.selectionModel().selectedRows()
        if rows and self.entries:
            row = rows[0].row()
            if row < len(self.entries):
                return self.entries[row]
        return None
    
    def clear(self):
        self.entries = []
        self.table.setRowCount(0)
