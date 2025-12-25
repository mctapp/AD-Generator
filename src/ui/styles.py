# ui/styles.py
# ADFlow UI 스타일 정의 - v2.2 Modern UI (PyDracula 영감)

# 컬러 팔레트 - 기존 브랜딩 유지 + 모던 개선
COLORS = {
    # 배경 (짙은 회색 기반 - 더 깊은 톤)
    'bg_primary': '#1A1A1F',
    'bg_secondary': '#22222A',
    'bg_tertiary': '#2A2A35',
    'bg_elevated': '#32323E',
    'bg_hover': '#3A3A48',
    'bg_card': '#252530',

    # 텍스트
    'text_primary': '#F8F8F2',
    'text_secondary': '#BFBFBF',
    'text_muted': '#6272A4',
    'text_disabled': '#44475A',

    # 포인트 컬러 - 브라운 (브랜드)
    'brand_primary': '#6D3B1F',
    'brand_light': '#8B4D2B',
    'brand_dark': '#5A3018',

    # 포인트 컬러 - 옐로우 (강조/경고)
    'accent_yellow': '#F1FA8C',
    'accent_yellow_light': '#FFFFA5',
    'accent_yellow_dark': '#E6DB74',

    # 포인트 컬러 - 그린 (액션/성공)
    'accent_green': '#50FA7B',
    'accent_green_light': '#69FF94',
    'accent_green_dark': '#3AD068',

    # 상태 색상
    'accent_primary': '#50FA7B',
    'accent_secondary': '#3AD068',
    'accent_hover': '#69FF94',
    'accent_success': '#50FA7B',
    'accent_warning': '#FFB86C',
    'accent_error': '#FF5555',
    'accent_info': '#8BE9FD',
    'accent_purple': '#BD93F9',
    'accent_pink': '#FF79C6',
    'accent_cyan': '#8BE9FD',

    # 보더
    'border_default': '#44475A',
    'border_light': '#6272A4',
    'border_focus': '#50FA7B',

    # 버튼
    'btn_primary_bg': '#50FA7B',
    'btn_primary_hover': '#69FF94',
    'btn_secondary_bg': '#44475A',
    'btn_secondary_hover': '#6272A4',

    # 브랜드
    'tomato': '#6D3B1F',

    # 호환성 별칭
    'bg_input': '#2A2A35',
    'accent_danger': '#FF5555',
}

# 폰트 설정
FONTS = {
    'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif',
    'mono': '"SF Mono", "Fira Code", "Consolas", "D2Coding", monospace',
    'size_xs': '11px',
    'size_sm': '12px',
    'size_base': '13px',
    'size_lg': '14px',
    'size_xl': '16px',
    'size_2xl': '20px',
    'size_3xl': '24px',
}

# 둥근 모서리 - 더 부드럽게
RADIUS = {
    'sm': '6px',
    'md': '10px',
    'lg': '14px',
    'xl': '18px',
    'full': '9999px',
}

# 그림자 (CSS 호환)
SHADOWS = {
    'sm': '0 2px 4px rgba(0, 0, 0, 0.3)',
    'md': '0 4px 8px rgba(0, 0, 0, 0.4)',
    'lg': '0 8px 16px rgba(0, 0, 0, 0.5)',
    'glow_green': '0 0 20px rgba(80, 250, 123, 0.3)',
    'glow_yellow': '0 0 20px rgba(241, 250, 140, 0.3)',
    'glow_purple': '0 0 20px rgba(189, 147, 249, 0.3)',
}


def get_button_style(variant: str = 'primary', size: str = 'md') -> str:
    """모던 버튼 스타일"""

    padding = {
        'sm': '8px 14px',
        'md': '10px 20px',
        'lg': '12px 28px',
    }.get(size, '10px 20px')

    font_size = {
        'sm': FONTS['size_sm'],
        'md': FONTS['size_base'],
        'lg': FONTS['size_lg'],
    }.get(size, FONTS['size_base'])

    border_radius = {
        'sm': RADIUS['sm'],
        'md': RADIUS['md'],
        'lg': RADIUS['lg'],
    }.get(size, RADIUS['md'])

    if variant == 'primary':
        return f"""
            QPushButton {{
                background-color: {COLORS['btn_primary_bg']};
                color: #1A1A1F;
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 700;
                letter-spacing: 0.3px;
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
                border: 2px solid {COLORS['border_default']};
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['btn_secondary_hover']};
                border-color: {COLORS['accent_primary']};
                color: {COLORS['accent_primary']};
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
        return f"""
            QPushButton {{
                background-color: {COLORS['brand_primary']};
                color: #FFFFFF;
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {COLORS['brand_light']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['brand_dark']};
            }}
        """

    elif variant == 'warning':
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_warning']};
                color: #1A1A1F;
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #FFCB8E;
            }}
        """

    elif variant == 'outline':
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent_primary']};
                border: 2px solid {COLORS['accent_primary']};
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(80, 250, 123, 0.15);
            }}
            QPushButton:pressed {{
                background-color: rgba(80, 250, 123, 0.25);
            }}
        """

    elif variant == 'danger':
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_error']};
                color: #FFFFFF;
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #FF6E6E;
            }}
        """

    elif variant == 'ghost':
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_hover']};
                color: {COLORS['text_primary']};
            }}
        """

    elif variant == 'purple':
        return f"""
            QPushButton {{
                background-color: {COLORS['accent_purple']};
                color: #1A1A1F;
                border: none;
                border-radius: {border_radius};
                padding: {padding};
                font-size: {font_size};
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #CAA6FF;
            }}
        """

    return ""


def get_input_style() -> str:
    """모던 입력 필드 스타일"""
    return f"""
        QLineEdit, QSpinBox, QDoubleSpinBox {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 10px 14px;
            font-size: {FONTS['size_base']};
            selection-background-color: {COLORS['accent_primary']};
            selection-color: #1A1A1F;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLORS['accent_primary']};
            background-color: {COLORS['bg_elevated']};
        }}
        QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {COLORS['border_light']};
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background-color: {COLORS['bg_hover']};
            border: none;
            width: 24px;
            border-radius: 4px;
            margin: 2px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover,
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {COLORS['accent_primary']};
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-bottom: 6px solid {COLORS['text_secondary']};
            width: 0;
            height: 0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
            width: 0;
            height: 0;
        }}
    """


def get_combobox_style() -> str:
    """모던 콤보박스 스타일"""
    return f"""
        QComboBox {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 10px 14px;
            padding-right: 36px;
            font-size: {FONTS['size_base']};
            min-width: 100px;
        }}
        QComboBox:hover {{
            border-color: {COLORS['border_light']};
        }}
        QComboBox:focus {{
            border-color: {COLORS['accent_primary']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 36px;
            border-top-right-radius: {RADIUS['md']};
            border-bottom-right-radius: {RADIUS['md']};
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 6px solid transparent;
            border-right: 6px solid transparent;
            border-top: 7px solid {COLORS['accent_primary']};
            margin-right: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['bg_elevated']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_light']};
            border-radius: {RADIUS['md']};
            selection-background-color: {COLORS['accent_primary']};
            selection-color: #1A1A1F;
            padding: 6px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: {RADIUS['sm']};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {COLORS['bg_hover']};
        }}
    """


def get_table_style() -> str:
    """모던 테이블 스타일"""
    return f"""
        QTableWidget {{
            background-color: {COLORS['bg_card']};
            color: {COLORS['text_primary']};
            border: 2px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
            gridline-color: {COLORS['border_default']};
            font-size: {FONTS['size_base']};
            selection-background-color: rgba(80, 250, 123, 0.2);
            selection-color: {COLORS['text_primary']};
            outline: none;
        }}
        QTableWidget::item {{
            padding: 12px 14px;
            border-bottom: 1px solid {COLORS['border_default']};
        }}
        QTableWidget::item:selected {{
            background-color: rgba(80, 250, 123, 0.15);
            border-left: 3px solid {COLORS['accent_primary']};
        }}
        QTableWidget::item:hover {{
            background-color: {COLORS['bg_hover']};
        }}
        QHeaderView::section {{
            background-color: {COLORS['bg_tertiary']};
            color: {COLORS['text_muted']};
            border: none;
            border-bottom: 3px solid {COLORS['accent_purple']};
            padding: 14px 14px;
            font-size: {FONTS['size_sm']};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        QHeaderView::section:hover {{
            color: {COLORS['text_primary']};
        }}
        QTableWidget QScrollBar:vertical {{
            background-color: {COLORS['bg_secondary']};
            width: 12px;
            border-radius: 6px;
            margin: 4px;
        }}
        QTableWidget QScrollBar::handle:vertical {{
            background-color: {COLORS['border_light']};
            border-radius: 6px;
            min-height: 40px;
        }}
        QTableWidget QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['accent_primary']};
        }}
        QTableWidget QScrollBar::add-line:vertical,
        QTableWidget QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QTableWidget QScrollBar:horizontal {{
            background-color: {COLORS['bg_secondary']};
            height: 12px;
            border-radius: 6px;
            margin: 4px;
        }}
        QTableWidget QScrollBar::handle:horizontal {{
            background-color: {COLORS['border_light']};
            border-radius: 6px;
            min-width: 40px;
        }}
        QTableWidget QScrollBar::handle:horizontal:hover {{
            background-color: {COLORS['accent_primary']};
        }}
    """


def get_checkbox_style() -> str:
    """모던 체크박스 스타일 (토글 느낌)"""
    return f"""
        QCheckBox {{
            color: {COLORS['text_secondary']};
            font-size: {FONTS['size_base']};
            spacing: 10px;
        }}
        QCheckBox::indicator {{
            width: 22px;
            height: 22px;
            border-radius: {RADIUS['sm']};
            border: 2px solid {COLORS['border_light']};
            background-color: {COLORS['bg_tertiary']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {COLORS['accent_primary']};
            background-color: {COLORS['bg_hover']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLORS['accent_primary']};
            border-color: {COLORS['accent_primary']};
            image: none;
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {COLORS['accent_hover']};
            border-color: {COLORS['accent_hover']};
        }}
        QCheckBox:hover {{
            color: {COLORS['text_primary']};
        }}
    """


def get_slider_style() -> str:
    """모던 슬라이더 스타일"""
    return f"""
        QSlider::groove:horizontal {{
            background-color: {COLORS['bg_tertiary']};
            height: 8px;
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background-color: {COLORS['accent_primary']};
            width: 20px;
            height: 20px;
            margin: -6px 0;
            border-radius: 10px;
            border: 3px solid {COLORS['bg_primary']};
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {COLORS['accent_hover']};
            border-color: {COLORS['bg_secondary']};
        }}
        QSlider::sub-page:horizontal {{
            background-color: {COLORS['accent_primary']};
            border-radius: 4px;
        }}
        QSlider::add-page:horizontal {{
            background-color: {COLORS['border_default']};
            border-radius: 4px;
        }}
    """


def get_tab_style() -> str:
    """모던 탭 스타일"""
    return f"""
        QTabWidget::pane {{
            background-color: {COLORS['bg_primary']};
            border: none;
            border-top: 2px solid {COLORS['border_default']};
        }}
        QTabBar {{
            background-color: transparent;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {COLORS['text_muted']};
            border: none;
            padding: 14px 28px;
            font-size: {FONTS['size_base']};
            font-weight: 600;
            margin-right: 4px;
            border-top-left-radius: {RADIUS['md']};
            border-top-right-radius: {RADIUS['md']};
        }}
        QTabBar::tab:hover {{
            color: {COLORS['text_secondary']};
            background-color: {COLORS['bg_hover']};
        }}
        QTabBar::tab:selected {{
            color: {COLORS['accent_primary']};
            background-color: {COLORS['bg_tertiary']};
            border-bottom: 3px solid {COLORS['accent_primary']};
        }}
    """


def get_groupbox_style() -> str:
    """모던 그룹박스 스타일 (카드 스타일)"""
    return f"""
        QGroupBox {{
            background-color: {COLORS['bg_card']};
            border: 2px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
            margin-top: 20px;
            padding: 24px 20px 20px 20px;
            font-size: {FONTS['size_base']};
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 20px;
            top: 6px;
            color: {COLORS['accent_purple']};
            background-color: {COLORS['bg_card']};
            padding: 2px 12px;
            border-radius: {RADIUS['sm']};
        }}
    """


def get_progressbar_style() -> str:
    """모던 프로그레스바 스타일"""
    return f"""
        QProgressBar {{
            background-color: {COLORS['bg_tertiary']};
            border: none;
            border-radius: {RADIUS['md']};
            height: 12px;
            text-align: center;
            font-size: {FONTS['size_xs']};
            color: {COLORS['text_primary']};
        }}
        QProgressBar::chunk {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['accent_primary']},
                stop:1 {COLORS['accent_cyan']}
            );
            border-radius: {RADIUS['md']};
        }}
    """


def get_scrollarea_style() -> str:
    """모던 스크롤 영역 스타일"""
    return f"""
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background-color: {COLORS['bg_secondary']};
            width: 10px;
            border-radius: 5px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {COLORS['border_light']};
            border-radius: 5px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {COLORS['accent_primary']};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0;
        }}
    """


def get_card_style() -> str:
    """카드 컨테이너 스타일"""
    return f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 2px solid {COLORS['border_default']};
            border-radius: {RADIUS['lg']};
        }}
        QFrame:hover {{
            border-color: {COLORS['border_light']};
        }}
    """


def get_label_style(variant: str = 'default') -> str:
    """라벨 스타일"""
    if variant == 'title':
        return f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: {FONTS['size_xl']};
                font-weight: 700;
            }}
        """
    elif variant == 'subtitle':
        return f"""
            QLabel {{
                color: {COLORS['text_secondary']};
                font-size: {FONTS['size_base']};
                font-weight: 500;
            }}
        """
    elif variant == 'accent':
        return f"""
            QLabel {{
                color: {COLORS['accent_primary']};
                font-size: {FONTS['size_base']};
                font-weight: 600;
            }}
        """
    elif variant == 'muted':
        return f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: {FONTS['size_sm']};
            }}
        """
    return f"""
        QLabel {{
            color: {COLORS['text_primary']};
            font-size: {FONTS['size_base']};
        }}
    """


# 전역 앱 스타일
APP_STYLE = f"""
    * {{
        font-family: {FONTS['family']};
    }}

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
        border: 2px solid {COLORS['accent_purple']};
        border-radius: {RADIUS['md']};
        padding: 8px 12px;
        font-size: {FONTS['size_sm']};
    }}

    QMessageBox {{
        background-color: {COLORS['bg_secondary']};
    }}

    QMessageBox QLabel {{
        color: {COLORS['text_primary']};
        font-size: {FONTS['size_base']};
        padding: 10px;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 16px;
    }}

    QDialog {{
        background-color: {COLORS['bg_secondary']};
        border-radius: {RADIUS['lg']};
    }}

    QMenu {{
        background-color: {COLORS['bg_elevated']};
        color: {COLORS['text_primary']};
        border: 2px solid {COLORS['border_light']};
        border-radius: {RADIUS['md']};
        padding: 6px;
    }}

    QMenu::item {{
        padding: 10px 24px;
        border-radius: {RADIUS['sm']};
    }}

    QMenu::item:selected {{
        background-color: {COLORS['accent_primary']};
        color: #1A1A1F;
    }}

    QMenu::separator {{
        height: 2px;
        background-color: {COLORS['border_default']};
        margin: 6px 12px;
    }}

    QStatusBar {{
        background-color: {COLORS['bg_secondary']};
        color: {COLORS['text_muted']};
        border-top: 1px solid {COLORS['border_default']};
        padding: 6px 12px;
        font-size: {FONTS['size_sm']};
    }}

    QStatusBar::item {{
        border: none;
    }}
"""

# MAIN_STYLE alias for compatibility
MAIN_STYLE = APP_STYLE
