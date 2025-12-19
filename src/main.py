#!/usr/bin/env python3
# main.py
# TOMATO AD Voice Generator - 앱 진입점

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


def main():
    # High DPI 지원
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("TOMATO AD Voice Generator")
    app.setOrganizationName("MediaCenter Tomorrow")
    app.setOrganizationDomain("mct.kr")
    
    # 기본 폰트
    font = QFont("Apple SD Gothic Neo", 12)
    app.setFont(font)
    
    # 메인 윈도우
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
