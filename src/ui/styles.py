# ui/styles.py
# ADFlow UI 스타일 정의 - v2.1.1 컬러 스킴

# 컬러 팔레트 - 다크 테마 + 브라운/옐로우/그린 포인트
COLORS = {
    # 배경 (짙은 회색 기반)
    'bg_primary': '#1A1A1A',
    'bg_secondary': '#242424',
    'bg_tertiary': '#2D2D2D',
    'bg_elevated': '#363636',
    'bg_hover': '#3D3D3D',
    
    # 텍스트
    'text_primary': '#F5F5F5',
    'text_secondary': '#BFBFBF',
    'text_muted': '#808080',
    'text_disabled': '#555555',
    
    # 포인트 컬러 - 브라운 (브랜드)
    'brand_primary': '#6D3B1F',       # 갈색 (토마토 AD 브랜드)
    'brand_light': '#8B4D2B',
    'brand_dark': '#5A3018',
    
    # 포인트 컬러 - 옐로우 (강조/경고)
    'accent_yellow': '#F5C518',
    'accent_yellow_light': '#FFD93D',
    'accent_yellow_dark': '#D4A810',
    
    # 포인트 컬러 - 그린 (액션/성공)
    'accent_green': '#1DB954',
    'accent_green_light': '#1ED760',
    'accent_green_dark': '#169C46',
    
    # 상태 색상
    'accent_primary': '#1DB954',       # 주요 액션 = 그린
    'accent_secondary': '#169C46',
    'accent_hover': '#1ED760',
    'accent_success': '#1DB954',       # 성공 = 그린
    'accent_warning': '#F5C518',       # 경고 = 옐로우
    'accent_error': '#E74C3C',         # 오류 = 레드
    'accent_info': '#3498DB',
    
    # 보더
    'border_default': '#3A3A3A',
    'border_light': '#4A4A4A',
    'border_focus': '#1DB954',
    
    # 버튼
    'btn_primary_bg': '#1DB954',
    'btn_primary_hover': '#1ED760',
    'btn_secondary_bg': '#363636',
    'btn_secondary_hover': '#454545',
    
    # 브랜드
    'tomato': '#6D3B1F',
    
    # 호환성 별칭
    'bg_input': '#2D2D2D',
    'accent_danger': '#E74C3C',
}

# 폰트 설정
FONTS = {
    'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif',
    'mono': '"SF Mono", "Fira Code", "Consolas", monospace',
    'size_xs': '11px',
    'size_sm': '12px',
    'size_base': '13px',
    'size_lg': '14px',
    'size_xl': '16px',
    'size_2xl': '18px',
}

# 둥근 모서리
RADIUS = {
    'sm': '4px',
    'md': '6px',
    'lg': '8px',
    'xl': '12px',
}


def get_button_style(variant: str = 'primary', size: str = 'md') -> str:
    """버튼 스타일 반환"""
    
    padding = {
        'sm': '6px 12px',
        'md': '8px 16px',
        'lg': '10px 20px',
    }.get(size, '8px 16px')
    
    font_size = {
        'sm': FONTS['size_sm'],
        'md': FONTS['size_base'],
        'lg': FONTS['size_lg'],
    }.get(size, FONTS['size_base'])
    
    if variant == 'primary':
        return f"""
            QPushButton {{
                background-color: {COLORS['btn_primary_bg']};
                color: #FFFFFF;
                border: none;
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['btn_primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_secondary']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_tertiary']};
                color: {COLORS['text_disabled']};
            }}
        """
    
    elif variant == 'secondary':
        return f"""
            QPushButton {{
                background-color: {COLORS['btn_secondary_bg']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border_light']};
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['btn_secondary_hover']};
                border-color: {COLORS['accent_primary']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['bg_tertiary']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_disabled']};
                border-color: {COLORS['border_default']};
            }}
        """
    
    elif variant == 'brand':
        # 브라운 브랜드 버튼
        return f"""
            QPushButton {{
                background-color: {COLORS['brand_primary']};
                color: #FFFFFF;
                border: none;
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['brand_light']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['brand_dark']};
            }}
        """
    
    elif variant == 'warning':
        # 옐로우 경고 버튼
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_yellow']};
                color: #1A1A1A;
                border: none;
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_yellow_light']};
            }}
        """
    
    elif variant == 'outline':
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['accent_primary']};
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: rgba(29, 185, 84, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(29, 185, 84, 0.2);
            }}
        """
    
    elif variant == 'danger':
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_error']};
                color: #FFFFFF;
                border: none;
                border-radius: {RADIUS['md']};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #C0392B;
            }}
        """
    
    return ""


def get_input_style() -> str:
    """입력 필드 스타일"""
    return f"""
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 6px 10px;
            font-size: {FONTS['size_base']};
            selection-background-color: {COLORS['accent_primary']};
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLORS['accent_primary']};
            background-color: {COLORS['bg_elevated']};
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background-color: {COLORS['bg_hover']};
            border: none;
            width: 20px;
            border-radius: 3px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover,
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {COLORS['accent_primary']};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 5px solid {COLORS['text_secondary']};
            width: 0;
            height: 0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {COLORS['text_secondary']};
            width: 0;
            height: 0;
        }}
    """


def get_combobox_style() -> str:
    """콤보박스 스타일"""
    return f"""
        QComboBox {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 8px 12px;
            padding-right: 30px;
            font-size: {FONTS['size_base']};
        }}
        QComboBox:hover {{
            border-color: {COLORS['border_light']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['accent_primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['bg_elevated']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_light']};
            selection-background-color: {COLORS['accent_primary']};
            padding: 4px;
        }}
    """


def get_table_style() -> str:
    """테이블 스타일"""
    return f"""
        QTableWidget {{
            background-color: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
            gridline-color: {COLORS['border_default']};
            font-size: {FONTS['size_base']};
            selection-background-color: rgba(29, 185, 84, 0.2);
            selection-color: {COLORS['text_primary']};
        }}
        QTableWidget::item {{
            padding: 8px 10px;
            border-bottom: 1px solid {COLORS['border_default']};
        }}
        QTableWidget::item:selected {{
            background-color: rgba(29, 185, 84, 0.15);
        }}
        QHeaderView::section {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_secondary']};
            border: none;
            border-bottom: 2px solid {COLORS['brand_primary']};
            padding: 10px 10px;
            font-size: {FONTS['size_sm']};
            font-weight: 600;
        }}
        QTableWidget QScrollBar:vertical {{
            background-color: {COLORS['bg_secondary']};
            width: 10px;
            border-radius: 5px;
        }}
        QTableWidget QScrollBar::handle:vertical {{
            background-color: {COLORS['border_light']};
            border-radius: 5px;
            min-height: 30px;
        }}
        QTableWidget QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['text_muted']};
        }}
        QTableWidget QScrollBar::add-line:vertical,
        QTableWidget QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """


def get_checkbox_style() -> str:
    """체크박스 스타일"""
    return f"""
        QCheckBox {{
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_base']};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: {RADIUS['sm']};
            border: 2px solid {COLORS['border_light']};
            background-color: {COLORS['bg_tertiary']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {COLORS['accent_primary']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLORS['accent_primary']};
            border-color: {COLORS['accent_primary']};
        }}
        QCheckBox:hover {{
            color: {COLORS['text_primary']};
        }}
    """


def get_slider_style() -> str:
    """슬라이더 스타일"""
    return f"""
        QSlider::groove:horizontal {{
            background-color: {COLORS['bg_tertiary']};
            height: 6px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background-color: {COLORS['accent_primary']};
            width: 16px;
            height: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {COLORS['accent_hover']};
        }}
        QSlider::sub-page:horizontal {{
            background-color: {COLORS['accent_primary']};
            border-radius: 3px;
        }}
    """


def get_tab_style() -> str:
    """탭 스타일"""
    return f"""
        QTabWidget::pane {{
            background-color: {COLORS['bg_primary']};
            border: none;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {COLORS['text_muted']};
            border: none;
            padding: 12px 24px;
            font-size: {FONTS['size_base']};
            font-weight: 500;
            min-width: 80px;
        }}
        QTabBar::tab:hover {{
            color: {COLORS['text_secondary']};
        }}
        QTabBar::tab:selected {{
            color: {COLORS['accent_yellow']};
            border-bottom: 2px solid {COLORS['accent_yellow']};
        }}
    """


def get_groupbox_style() -> str:
    """그룹박스 스타일"""
    return f"""
        QGroupBox {{
            background-color: {COLORS['bg_secondary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
            margin-top: 16px;
            padding: 20px 16px 16px 16px;
            font-size: {FONTS['size_base']};
            font-weight: 500;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 16px;
            top: 4px;
            color: {COLORS['text_secondary']};
            background-color: {COLORS['bg_secondary']};
            padding: 0 8px;
        }}
    """


def get_progressbar_style() -> str:
    """프로그레스바 스타일"""
    return f"""
        QProgressBar {{
            background-color: {COLORS['bg_tertiary']};
            border: none;
            border-radius: {RADIUS['sm']};
            height: 8px;
            text-align: center;
        }}
        QProgressBar::chunk {{
            background-color: {COLORS['accent_primary']};
            border-radius: {RADIUS['sm']};
        }}
    """


# 전역 앱 스타일
APP_STYLE = f"""
    QWidget {{
        background-color: {COLORS['bg_primary']};
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
    }}
    
    QMainWindow {{
        background-color: {COLORS['bg_primary']};
    }}
    
    QToolTip {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_light']};
        border-radius: {RADIUS['sm']};
        padding: 6px 10px;
        font-size: {FONTS['size_sm']};
    }}
    
    QMessageBox {{
        background-color: {COLORS['bg_secondary']};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
    }}
    
    QDialog {{
        background-color: {COLORS['bg_secondary']};
    }}
"""

# MAIN_STYLE alias for compatibility
MAIN_STYLE = APP_STYLE
