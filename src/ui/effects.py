# ui/effects.py
# PyQt6 그래픽 효과 유틸리티 - 모던 UI

from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint


def apply_shadow(widget: QWidget,
                 blur_radius: int = 20,
                 x_offset: int = 0,
                 y_offset: int = 4,
                 color: str = "#000000",
                 opacity: float = 0.3) -> QGraphicsDropShadowEffect:
    """
    위젯에 드롭 섀도우 효과 적용

    Args:
        widget: 대상 위젯
        blur_radius: 블러 반경 (기본 20)
        x_offset: X 오프셋 (기본 0)
        y_offset: Y 오프셋 (기본 4)
        color: 그림자 색상 (기본 검정)
        opacity: 불투명도 (0.0 ~ 1.0)

    Returns:
        QGraphicsDropShadowEffect 객체
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)

    shadow_color = QColor(color)
    shadow_color.setAlphaF(opacity)
    shadow.setColor(shadow_color)

    widget.setGraphicsEffect(shadow)
    return shadow


def apply_card_shadow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """카드 스타일 그림자 (부드러운 그림자)"""
    return apply_shadow(
        widget,
        blur_radius=25,
        y_offset=8,
        color="#000000",
        opacity=0.4
    )


def apply_button_shadow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """버튼용 미묘한 그림자"""
    return apply_shadow(
        widget,
        blur_radius=12,
        y_offset=4,
        color="#000000",
        opacity=0.25
    )


def apply_glow_effect(widget: QWidget,
                      color: str = "#50FA7B",
                      blur_radius: int = 30,
                      opacity: float = 0.4) -> QGraphicsDropShadowEffect:
    """
    글로우 효과 적용 (네온 느낌)

    Args:
        widget: 대상 위젯
        color: 글로우 색상
        blur_radius: 블러 반경
        opacity: 불투명도
    """
    glow = QGraphicsDropShadowEffect(widget)
    glow.setBlurRadius(blur_radius)
    glow.setXOffset(0)
    glow.setYOffset(0)

    glow_color = QColor(color)
    glow_color.setAlphaF(opacity)
    glow.setColor(glow_color)

    widget.setGraphicsEffect(glow)
    return glow


def apply_green_glow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """그린 글로우 효과"""
    return apply_glow_effect(widget, "#50FA7B", 25, 0.35)


def apply_purple_glow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """퍼플 글로우 효과"""
    return apply_glow_effect(widget, "#BD93F9", 25, 0.35)


def apply_cyan_glow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """시안 글로우 효과"""
    return apply_glow_effect(widget, "#8BE9FD", 25, 0.35)


def apply_warning_glow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """경고 글로우 효과 (오렌지)"""
    return apply_glow_effect(widget, "#FFB86C", 25, 0.35)


def apply_error_glow(widget: QWidget) -> QGraphicsDropShadowEffect:
    """에러 글로우 효과 (레드)"""
    return apply_glow_effect(widget, "#FF5555", 25, 0.35)


class HoverShadowEffect:
    """
    호버 시 그림자 강화 효과

    사용법:
        effect = HoverShadowEffect(button)
        button.enterEvent = effect.on_enter
        button.leaveEvent = effect.on_leave
    """

    def __init__(self, widget: QWidget,
                 normal_blur: int = 10,
                 hover_blur: int = 25,
                 color: str = "#000000"):
        self.widget = widget
        self.normal_blur = normal_blur
        self.hover_blur = hover_blur
        self.color = color

        self.shadow = apply_shadow(
            widget,
            blur_radius=normal_blur,
            color=color
        )

    def on_enter(self, event):
        """마우스 진입 시"""
        self.shadow.setBlurRadius(self.hover_blur)

    def on_leave(self, event):
        """마우스 이탈 시"""
        self.shadow.setBlurRadius(self.normal_blur)


class FadeAnimation:
    """페이드 인/아웃 애니메이션"""

    def __init__(self, widget: QWidget, duration: int = 300):
        self.widget = widget
        self.duration = duration
        self.opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(duration)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def fade_in(self):
        """페이드 인"""
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def fade_out(self):
        """페이드 아웃"""
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.start()


def remove_effect(widget: QWidget):
    """위젯의 그래픽 효과 제거"""
    widget.setGraphicsEffect(None)


__all__ = [
    'apply_shadow',
    'apply_card_shadow',
    'apply_button_shadow',
    'apply_glow_effect',
    'apply_green_glow',
    'apply_purple_glow',
    'apply_cyan_glow',
    'apply_warning_glow',
    'apply_error_glow',
    'HoverShadowEffect',
    'FadeAnimation',
    'remove_effect',
]
