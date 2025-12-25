# ui/widgets/waveform_widget.py
# 오디오 파형 시각화 위젯

import os
import wave
import struct
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath

from ..styles import COLORS, FONTS, RADIUS


class WaveformWidget(QFrame):
    """오디오 파형 시각화 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.duration_ms = 0
        self.filename = ""
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
        """)

    def load_wav(self, filepath: str) -> bool:
        """WAV 파일 로드하여 파형 데이터 추출"""
        if not filepath or not os.path.exists(filepath):
            self.samples = []
            self.duration_ms = 0
            self.filename = ""
            self.update()
            return False

        try:
            with wave.open(filepath, 'rb') as wav_file:
                n_channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                n_frames = wav_file.getnframes()

                self.duration_ms = int(n_frames / framerate * 1000)
                self.filename = os.path.basename(filepath)

                # 프레임 읽기
                raw_data = wav_file.readframes(n_frames)

                # 샘플 데이터 변환
                if sample_width == 2:  # 16-bit
                    fmt = f"<{n_frames * n_channels}h"
                    samples = struct.unpack(fmt, raw_data)
                elif sample_width == 1:  # 8-bit
                    samples = [s - 128 for s in raw_data]
                else:
                    self.samples = []
                    self.update()
                    return False

                # 스테레오면 모노로 변환
                if n_channels == 2:
                    samples = [(samples[i] + samples[i + 1]) // 2
                               for i in range(0, len(samples), 2)]

                # 표시를 위해 다운샘플링 (최대 500 포인트)
                target_points = min(500, len(samples))
                if len(samples) > target_points:
                    step = len(samples) // target_points
                    # 구간별 최대값 사용 (피크 보존)
                    self.samples = []
                    for i in range(0, len(samples) - step, step):
                        chunk = samples[i:i + step]
                        peak = max(abs(min(chunk)), abs(max(chunk)))
                        self.samples.append(peak)
                else:
                    self.samples = [abs(s) for s in samples]

                # 정규화 (0~1)
                max_val = max(self.samples) if self.samples else 1
                if max_val > 0:
                    self.samples = [s / max_val for s in self.samples]

            self.update()
            return True

        except Exception as e:
            self.samples = []
            self.duration_ms = 0
            self.filename = ""
            self.update()
            return False

    def clear(self):
        """파형 초기화"""
        self.samples = []
        self.duration_ms = 0
        self.filename = ""
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center_y = height // 2
        padding = 10

        # 배경 (이미 스타일시트로 적용됨)

        if not self.samples:
            # 파형 없음 안내
            painter.setPen(QColor(COLORS['text_muted']))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "WAV 파일을 선택하세요"
            )
            return

        # 파형 그리기
        available_width = width - 2 * padding
        available_height = height - 2 * padding
        half_height = available_height // 2

        # 파형 색상
        wave_color = QColor(COLORS['accent_primary'])
        wave_color.setAlpha(180)
        pen = QPen(wave_color)
        pen.setWidth(2)
        painter.setPen(pen)

        # 중심선
        center_line_color = QColor(COLORS['border_light'])
        painter.setPen(QPen(center_line_color, 1, Qt.PenStyle.DashLine))
        painter.drawLine(padding, center_y, width - padding, center_y)

        # 파형 경로
        painter.setPen(pen)
        if len(self.samples) > 1:
            x_step = available_width / (len(self.samples) - 1)

            # 위쪽 파형
            path_top = QPainterPath()
            path_top.moveTo(padding, center_y)
            for i, sample in enumerate(self.samples):
                x = padding + i * x_step
                y = center_y - sample * half_height * 0.9
                path_top.lineTo(x, y)
            path_top.lineTo(width - padding, center_y)

            # 아래쪽 파형 (대칭)
            path_bottom = QPainterPath()
            path_bottom.moveTo(padding, center_y)
            for i, sample in enumerate(self.samples):
                x = padding + i * x_step
                y = center_y + sample * half_height * 0.9
                path_bottom.lineTo(x, y)
            path_bottom.lineTo(width - padding, center_y)

            # 채우기
            fill_color = QColor(COLORS['accent_primary'])
            fill_color.setAlpha(60)
            painter.fillPath(path_top, fill_color)
            painter.fillPath(path_bottom, fill_color)

            # 테두리
            painter.setPen(QPen(wave_color, 1))
            painter.drawPath(path_top)
            painter.drawPath(path_bottom)

        # 파일명 및 길이 표시
        info_text = f"{self.filename}  ({self.duration_ms}ms)"
        painter.setPen(QColor(COLORS['text_secondary']))
        painter.drawText(
            padding, height - 5,
            info_text
        )

    def get_duration_ms(self) -> int:
        """로드된 WAV 파일의 길이 반환"""
        return self.duration_ms
