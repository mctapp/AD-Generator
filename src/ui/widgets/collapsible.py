# ui/widgets/collapsible.py
# 접힘/펼침 섹션 위젯

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

from ..styles import COLORS, FONTS, RADIUS


class CollapsibleSection(QWidget):
    """접힘/펼침 가능한 섹션 위젯"""
    
    toggled = pyqtSignal(bool)  # 펼침 상태 시그널
    
    def __init__(self, title: str, parent=None, expanded: bool = True):
        super().__init__(parent)
        self._expanded = expanded
        self._title = title
        self._content_widget = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 헤더 버튼
        self.header_btn = QPushButton()
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(self._expanded)
        self._update_header_text()
        self.header_btn.clicked.connect(self._on_toggle)
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
                padding: 10px 14px;
                text-align: left;
                font-size: {FONTS['size_base']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                border-color: {COLORS['border_light']};
            }}
            QPushButton:checked {{
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
                border-bottom: none;
            }}
        """)
        layout.addWidget(self.header_btn)
        
        # 컨텐츠 컨테이너
        self.content_container = QFrame()
        self.content_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-top: none;
                border-bottom-left-radius: {RADIUS['md']};
                border-bottom-right-radius: {RADIUS['md']};
            }}
        """)
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(12, 12, 12, 24)  # 하단 여백 더 증가
        self.content_layout.setSpacing(8)
        
        layout.addWidget(self.content_container)
        
        # 초기 상태 설정
        self._apply_expanded_state()
    
    def _update_header_text(self):
        """헤더 텍스트 업데이트 (화살표 포함)"""
        arrow = "▼" if self._expanded else "▶"
        self.header_btn.setText(f"{arrow}  {self._title}")
    
    def _apply_expanded_state(self):
        """펼침/접힘 상태 적용"""
        self.content_container.setVisible(self._expanded)
        
        # SizePolicy 조정 - 접힘 시 공간 축소
        if self._expanded:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 부모 레이아웃 갱신
        if self.parent():
            self.parent().updateGeometry()
    
    def _on_toggle(self):
        """토글 처리"""
        self._expanded = self.header_btn.isChecked()
        self._update_header_text()
        self._apply_expanded_state()
        self.toggled.emit(self._expanded)
    
    def set_content(self, widget: QWidget):
        """컨텐츠 위젯 설정"""
        # 기존 컨텐츠 제거
        if self._content_widget:
            self.content_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)
        
        self._content_widget = widget
        self.content_layout.addWidget(widget)
    
    def add_widget(self, widget: QWidget):
        """컨텐츠에 위젯 추가"""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """컨텐츠에 레이아웃 추가"""
        self.content_layout.addLayout(layout)
    
    def expand(self):
        """펼치기"""
        if not self._expanded:
            self.header_btn.setChecked(True)
            self._on_toggle()
    
    def collapse(self):
        """접기"""
        if self._expanded:
            self.header_btn.setChecked(False)
            self._on_toggle()
    
    def is_expanded(self) -> bool:
        """펼침 상태 반환"""
        return self._expanded
    
    def set_title(self, title: str):
        """제목 변경"""
        self._title = title
        self._update_header_text()


class CollapsibleTable(CollapsibleSection):
    """테이블용 접힘/펼침 섹션 (더 넓은 패딩)"""
    
    def __init__(self, title: str, parent=None, expanded: bool = True):
        super().__init__(title, parent, expanded)
        # 테이블용으로 패딩 조정
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-top: none;
                border-bottom-left-radius: {RADIUS['md']};
                border-bottom-right-radius: {RADIUS['md']};
                padding: 8px;
            }}
        """)
