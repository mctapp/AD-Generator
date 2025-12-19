# ui/widgets/drop_zone.py
# 파일 드래그앤드롭 영역 (모던 스타일)

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame, QPushButton, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from ..styles import COLORS, RADIUS, FONTS, get_button_style


class DropZone(QFrame):
    """파일 드래그앤드롭 영역"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        self.setMinimumHeight(140)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px dashed {COLORS['border_light']};
                border-radius: {RADIUS['xl']};
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: rgba(29, 185, 84, 0.03);
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 아이콘 (텍스트 기반)
        self.icon = QLabel("⬚")
        self.icon.setStyleSheet(f"font-size: 32px; color: {COLORS['text_muted']};")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon)
        
        # 텍스트
        self.label = QLabel("SRT 파일을 드래그하거나")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_lg']};")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # 버튼
        self.btn_browse = QPushButton("파일 선택")
        self.btn_browse.setStyleSheet(get_button_style('primary'))
        self.btn_browse.setMinimumHeight(40)
        self.btn_browse.setMinimumWidth(100)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.filepath = None
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.srt'):
                event.acceptProposedAction()
                self.setStyleSheet(f"""
                    QFrame {{
                        background-color: rgba(29, 185, 84, 0.08);
                        border: 2px dashed {COLORS['accent_primary']};
                        border-radius: {RADIUS['xl']};
                    }}
                """)
    
    def dragLeaveEvent(self, event):
        if not self.filepath:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border: 2px dashed {COLORS['border_light']};
                    border-radius: {RADIUS['xl']};
                }}
            """)
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath.lower().endswith('.srt'):
                self.set_file(filepath)
                self.file_dropped.emit(filepath)
        
        self.dragLeaveEvent(event)
    
    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "SRT 파일 선택",
            "",
            "SRT 파일 (*.srt);;모든 파일 (*.*)"
        )
        if filepath:
            self.set_file(filepath)
            self.file_dropped.emit(filepath)
    
    def set_file(self, filepath: str):
        """파일 설정"""
        self.filepath = filepath
        filename = filepath.split('/')[-1]
        self.icon.setText("✓")
        self.icon.setStyleSheet(f"font-size: 28px; color: {COLORS['accent_success']};")
        self.label.setText(filename)
        self.label.setStyleSheet(f"color: {COLORS['accent_success']}; font-size: {FONTS['size_lg']}; font-weight: 600;")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(29, 185, 84, 0.05);
                border: 2px solid {COLORS['accent_success']};
                border-radius: {RADIUS['xl']};
            }}
        """)
    
    def clear(self):
        """초기화"""
        self.filepath = None
        self.icon.setText("⬚")
        self.icon.setStyleSheet(f"font-size: 32px; color: {COLORS['text_muted']};")
        self.label.setText("SRT 파일을 드래그하거나")
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONTS['size_lg']};")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 2px dashed {COLORS['border_light']};
                border-radius: {RADIUS['xl']};
            }}
        """)
