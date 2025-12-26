#!/usr/bin/env python3
# main.py
# ADFlow - AD Voice Generator 앱 진입점

import sys
import os

# 패키지 경로 추가
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    app_path = os.path.dirname(sys.executable)
    sys.path.insert(0, app_path)
else:
    # 개발 모드 - src의 상위 폴더를 경로에 추가
    app_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.dirname(app_path)
    sys.path.insert(0, parent_path)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.ui import MainWindow
from src.utils import config
from src.core.tts import initialize_tts_engines


def apply_theme(app):
    """Qt-Material 테마 적용"""
    try:
        from qt_material import apply_stylesheet

        # 테마 파일 경로
        theme_path = os.path.join(
            os.path.dirname(__file__),
            'resources',
            'adflow_theme.xml'
        )

        # 액센트 색상 정의 (버튼 클래스용)
        extra = {
            # 버튼 액센트 색상
            'danger': '#E74C3C',
            'warning': '#F5C518',      # 옐로우
            'success': '#1DB954',      # 그린

            # 폰트 설정
            'font_family': 'Apple SD Gothic Neo, Noto Sans KR, sans-serif',
            'font_size': '13px',

            # 밀도 (density_scale: -2 ~ 2, 기본 0)
            'density_scale': '0',
        }

        # 테마 적용
        if os.path.exists(theme_path):
            apply_stylesheet(app, theme=theme_path, extra=extra)
        else:
            # 테마 파일이 없으면 기본 dark_amber 사용
            apply_stylesheet(app, theme='dark_amber.xml', extra=extra)

        return True
    except ImportError:
        print("qt-material not installed. Using default style.")
        return False


def main():
    # High DPI 지원
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ADFlow - AD Voice Generator")
    app.setOrganizationName("MediaCenter Tomorrow")
    app.setOrganizationDomain("mct.kr")

    # 기본 폰트
    font = QFont("Apple SD Gothic Neo", 12)
    app.setFont(font)

    # Qt-Material 테마 적용
    apply_theme(app)

    # TTS 엔진 초기화
    initialize_tts_engines(
        client_id=config.client_id or "",
        client_secret=config.client_secret or ""
    )

    # 메인 윈도우
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
