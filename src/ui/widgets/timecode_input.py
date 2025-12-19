# ui/widgets/timecode_input.py
# 타임코드 입력 위젯

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
import re


class TimecodeInput(QWidget):
    """타임코드 입력 위젯 (HH:MM:SS:FF)"""
    
    timecode_changed = pyqtSignal(str)  # 타임코드 변경 시그널
    
    def __init__(self, fps: float = 24, parent=None):
        super().__init__(parent)
        self.fps = fps
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 스타일
        input_style = """
            QLineEdit {
                background-color: #333;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                color: #4CAF50;
                text-align: center;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """
        
        separator_style = """
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 16px;
                color: #888;
                padding: 0 2px;
            }
        """
        
        # Hours
        self.edit_hh = QLineEdit("00")
        self.edit_hh.setFixedWidth(45)
        self.edit_hh.setMaxLength(2)
        self.edit_hh.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_hh.setStyleSheet(input_style)
        self.edit_hh.textChanged.connect(self._on_change)
        layout.addWidget(self.edit_hh)
        
        layout.addWidget(QLabel(":"))
        self.findChild(QLabel).setStyleSheet(separator_style)
        
        # Minutes
        self.edit_mm = QLineEdit("00")
        self.edit_mm.setFixedWidth(45)
        self.edit_mm.setMaxLength(2)
        self.edit_mm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_mm.setStyleSheet(input_style)
        self.edit_mm.textChanged.connect(self._on_change)
        layout.addWidget(self.edit_mm)
        
        sep2 = QLabel(":")
        sep2.setStyleSheet(separator_style)
        layout.addWidget(sep2)
        
        # Seconds
        self.edit_ss = QLineEdit("00")
        self.edit_ss.setFixedWidth(45)
        self.edit_ss.setMaxLength(2)
        self.edit_ss.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_ss.setStyleSheet(input_style)
        self.edit_ss.textChanged.connect(self._on_change)
        layout.addWidget(self.edit_ss)
        
        sep3 = QLabel(":")
        sep3.setStyleSheet(separator_style)
        layout.addWidget(sep3)
        
        # Frames
        self.edit_ff = QLineEdit("00")
        self.edit_ff.setFixedWidth(45)
        self.edit_ff.setMaxLength(2)
        self.edit_ff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_ff.setStyleSheet(input_style)
        self.edit_ff.textChanged.connect(self._on_change)
        layout.addWidget(self.edit_ff)
        
        layout.addStretch()
    
    def _on_change(self):
        """값 변경 시 시그널 발생"""
        self.timecode_changed.emit(self.get_timecode())
    
    def get_timecode(self) -> str:
        """현재 타임코드 반환 (HH:MM:SS:FF)"""
        hh = self.edit_hh.text().zfill(2)
        mm = self.edit_mm.text().zfill(2)
        ss = self.edit_ss.text().zfill(2)
        ff = self.edit_ff.text().zfill(2)
        return f"{hh}:{mm}:{ss}:{ff}"
    
    def get_timecode_for_filename(self) -> str:
        """파일명용 타임코드 반환 (HH_MM_SS_FF)"""
        return self.get_timecode().replace(':', '_')
    
    def get_milliseconds(self) -> int:
        """밀리초로 변환"""
        try:
            hh = int(self.edit_hh.text() or 0)
            mm = int(self.edit_mm.text() or 0)
            ss = int(self.edit_ss.text() or 0)
            ff = int(self.edit_ff.text() or 0)
            
            total_seconds = hh * 3600 + mm * 60 + ss + ff / self.fps
            return int(total_seconds * 1000)
        except ValueError:
            return 0
    
    def set_timecode(self, timecode: str):
        """타임코드 설정 (HH:MM:SS:FF 또는 HH_MM_SS_FF)"""
        tc = timecode.replace('_', ':')
        parts = tc.split(':')
        if len(parts) == 4:
            self.edit_hh.setText(parts[0])
            self.edit_mm.setText(parts[1])
            self.edit_ss.setText(parts[2])
            self.edit_ff.setText(parts[3])
    
    def set_fps(self, fps: float):
        """FPS 설정"""
        self.fps = fps
    
    def clear(self):
        """초기화"""
        self.edit_hh.setText("00")
        self.edit_mm.setText("00")
        self.edit_ss.setText("00")
        self.edit_ff.setText("00")
    
    def is_valid(self) -> bool:
        """유효한 타임코드인지 확인"""
        try:
            hh = int(self.edit_hh.text() or 0)
            mm = int(self.edit_mm.text() or 0)
            ss = int(self.edit_ss.text() or 0)
            ff = int(self.edit_ff.text() or 0)
            
            return (0 <= hh <= 23 and 
                    0 <= mm <= 59 and 
                    0 <= ss <= 59 and 
                    0 <= ff < self.fps)
        except ValueError:
            return False
