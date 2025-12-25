# ui/dialogs/tts_settings_dialog.py
# TTS 설정 다이얼로그

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QSlider, QSpinBox, QComboBox, QFrame, QGroupBox,
    QMessageBox, QFileDialog, QLineEdit, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ..styles import COLORS, FONTS, RADIUS, get_button_style


class TTSSettingsDialog(QDialog):
    """TTS 설정 다이얼로그"""

    settings_changed = pyqtSignal(dict)  # 설정 변경 시그널

    def __init__(self, tts_manager, parent=None):
        super().__init__(parent)
        self.tts_manager = tts_manager
        self.setWindowTitle("TTS 설정")
        self.setMinimumSize(700, 550)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # 탭 1: 엔진 관리
        self.engine_tab = self._create_engine_tab()
        self.tab_widget.addTab(self.engine_tab, "엔진 관리")

        # 탭 2: 음성 선택
        self.voice_tab = self._create_voice_tab()
        self.tab_widget.addTab(self.voice_tab, "음성 선택")

        # 탭 3: 커스텀 음성
        self.custom_tab = self._create_custom_tab()
        self.tab_widget.addTab(self.custom_tab, "커스텀 음성")

        layout.addWidget(self.tab_widget, 1)

        # 하단 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setStyleSheet(get_button_style('secondary'))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("적용")
        self.btn_apply.setStyleSheet(get_button_style('primary'))
        self.btn_apply.clicked.connect(self.apply_settings)
        btn_layout.addWidget(self.btn_apply)

        layout.addLayout(btn_layout)

    def _create_engine_tab(self) -> QWidget:
        """엔진 관리 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 설명
        desc = QLabel("사용할 TTS 엔진을 관리합니다. 클라우드 API는 인터넷 연결이 필요하고, "
                      "로컬 엔진은 오프라인에서도 사용 가능합니다.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 8px;")
        layout.addWidget(desc)

        # 엔진 목록
        self.engine_list = QListWidget()
        self.engine_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {COLORS['border_default']};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['bg_secondary']};
            }}
        """)
        self.engine_list.setMinimumHeight(200)
        layout.addWidget(self.engine_list)

        # 기본 엔진 선택
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("기본 엔진:"))
        self.combo_default_engine = QComboBox()
        self.combo_default_engine.setFixedWidth(200)
        default_layout.addWidget(self.combo_default_engine)
        default_layout.addStretch()
        layout.addLayout(default_layout)

        # 안내 메시지
        info = QLabel("ℹ️ 로컬 엔진은 오프라인에서도 사용할 수 있습니다.\n"
                      "   OpenVoice는 음성 클로닝을 지원합니다.")
        info.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; margin-top: 8px;")
        layout.addWidget(info)

        layout.addStretch()
        return widget

    def _create_voice_tab(self) -> QWidget:
        """음성 선택 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 필터 영역
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("엔진:"))
        self.combo_engine_filter = QComboBox()
        self.combo_engine_filter.addItem("전체", "all")
        self.combo_engine_filter.setFixedWidth(150)
        self.combo_engine_filter.currentIndexChanged.connect(self._filter_voices)
        filter_layout.addWidget(self.combo_engine_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 음성 목록
        self.voice_list = QListWidget()
        self.voice_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {COLORS['border_default']};
            }}
            QListWidget::item:selected {{
                background-color: rgba(29, 185, 84, 0.2);
            }}
        """)
        self.voice_list.itemSelectionChanged.connect(self._on_voice_selected)
        layout.addWidget(self.voice_list, 1)

        # 음성 조절
        adjust_group = QGroupBox("음성 조절")
        adjust_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        adjust_layout = QVBoxLayout(adjust_group)

        # 속도
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("속도:"))
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(-5, 5)
        self.slider_speed.setValue(0)
        self.slider_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        speed_layout.addWidget(self.slider_speed, 1)
        self.label_speed = QLabel("0")
        self.label_speed.setFixedWidth(30)
        self.slider_speed.valueChanged.connect(lambda v: self.label_speed.setText(str(v)))
        speed_layout.addWidget(self.label_speed)
        adjust_layout.addLayout(speed_layout)

        # 피치
        pitch_layout = QHBoxLayout()
        pitch_layout.addWidget(QLabel("피치:"))
        self.slider_pitch = QSlider(Qt.Orientation.Horizontal)
        self.slider_pitch.setRange(-5, 5)
        self.slider_pitch.setValue(0)
        self.slider_pitch.setTickPosition(QSlider.TickPosition.TicksBelow)
        pitch_layout.addWidget(self.slider_pitch, 1)
        self.label_pitch = QLabel("0")
        self.label_pitch.setFixedWidth(30)
        self.slider_pitch.valueChanged.connect(lambda v: self.label_pitch.setText(str(v)))
        pitch_layout.addWidget(self.label_pitch)
        adjust_layout.addLayout(pitch_layout)

        # 볼륨
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("볼륨:"))
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(-5, 5)
        self.slider_volume.setValue(0)
        self.slider_volume.setTickPosition(QSlider.TickPosition.TicksBelow)
        volume_layout.addWidget(self.slider_volume, 1)
        self.label_volume = QLabel("0")
        self.label_volume.setFixedWidth(30)
        self.slider_volume.valueChanged.connect(lambda v: self.label_volume.setText(str(v)))
        volume_layout.addWidget(self.label_volume)
        adjust_layout.addLayout(volume_layout)

        # 감정
        emotion_layout = QHBoxLayout()
        emotion_layout.addWidget(QLabel("감정:"))
        self.combo_emotion = QComboBox()
        self.combo_emotion.addItem("중립", 0)
        self.combo_emotion.addItem("슬픔", 1)
        self.combo_emotion.addItem("기쁨", 2)
        self.combo_emotion.setFixedWidth(100)
        emotion_layout.addWidget(self.combo_emotion)

        emotion_layout.addWidget(QLabel("강도:"))
        self.spin_emotion_strength = QSpinBox()
        self.spin_emotion_strength.setRange(0, 2)
        self.spin_emotion_strength.setValue(1)
        self.spin_emotion_strength.setFixedWidth(60)
        emotion_layout.addWidget(self.spin_emotion_strength)
        emotion_layout.addStretch()
        adjust_layout.addLayout(emotion_layout)

        layout.addWidget(adjust_group)

        return widget

    def _create_custom_tab(self) -> QWidget:
        """커스텀 음성 탭"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # 설명
        desc = QLabel("🎤 6초 이상의 깨끗한 음성 샘플로 새 음성을 만들 수 있습니다.\n"
                      "   OpenVoice 엔진이 필요합니다.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 8px;")
        layout.addWidget(desc)

        # 등록된 커스텀 음성 목록
        self.custom_voice_list = QListWidget()
        self.custom_voice_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['md']};
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {COLORS['border_default']};
            }}
        """)
        self.custom_voice_list.setMinimumHeight(200)
        layout.addWidget(self.custom_voice_list, 1)

        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_add_voice = QPushButton("+ 새 음성 등록")
        self.btn_add_voice.setStyleSheet(get_button_style('primary'))
        self.btn_add_voice.clicked.connect(self._add_custom_voice)
        btn_layout.addWidget(self.btn_add_voice)

        self.btn_delete_voice = QPushButton("삭제")
        self.btn_delete_voice.setStyleSheet(get_button_style('secondary'))
        self.btn_delete_voice.clicked.connect(self._delete_custom_voice)
        self.btn_delete_voice.setEnabled(False)
        btn_layout.addWidget(self.btn_delete_voice)

        layout.addLayout(btn_layout)

        # 안내
        info = QLabel("⚠️ 클로닝된 음성은 로컬에 저장됩니다.\n"
                      "   저작권 및 초상권에 유의하세요.")
        info.setStyleSheet(f"color: {COLORS['accent_warning']}; font-size: 12px;")
        layout.addWidget(info)

        # 선택 변경 시그널
        self.custom_voice_list.itemSelectionChanged.connect(
            lambda: self.btn_delete_voice.setEnabled(len(self.custom_voice_list.selectedItems()) > 0)
        )

        return widget

    def load_settings(self):
        """현재 설정 로드"""
        # 엔진 목록 로드
        self._load_engines()

        # 음성 목록 로드
        self._load_voices()

        # 커스텀 음성 로드
        self._load_custom_voices()

        # 현재 설정 적용
        settings = self.tts_manager.current_settings
        self.slider_speed.setValue(settings.speed)
        self.slider_pitch.setValue(settings.pitch)
        self.slider_volume.setValue(settings.volume)

        idx = self.combo_emotion.findData(settings.emotion)
        if idx >= 0:
            self.combo_emotion.setCurrentIndex(idx)
        self.spin_emotion_strength.setValue(settings.emotion_strength)

        # 현재 음성 선택
        for i in range(self.voice_list.count()):
            item = self.voice_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == settings.voice_id:
                self.voice_list.setCurrentItem(item)
                break

    def _load_engines(self):
        """엔진 목록 로드"""
        self.engine_list.clear()
        self.combo_default_engine.clear()
        self.combo_engine_filter.clear()
        self.combo_engine_filter.addItem("전체", "all")

        for engine in self.tts_manager.get_all_engines():
            # 목록 아이템
            available, status_msg = engine.is_available()
            caps = engine.get_capabilities()

            engine_type = "클라우드" if caps.engine_type.value == "cloud" else "로컬"
            if caps.supports_cloning:
                engine_type += " (클로닝)"

            status_icon = "✓" if available else "⚠️"
            text = f"{engine.display_name}\n   {engine_type} | {status_icon} {status_msg}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, engine.engine_id)
            self.engine_list.addItem(item)

            # 기본 엔진 콤보박스
            self.combo_default_engine.addItem(engine.display_name, engine.engine_id)

            # 필터 콤보박스
            self.combo_engine_filter.addItem(engine.display_name, engine.engine_id)

        # 기본 엔진 선택
        idx = self.combo_default_engine.findData(self.tts_manager.default_engine_id)
        if idx >= 0:
            self.combo_default_engine.setCurrentIndex(idx)

    def _load_voices(self):
        """음성 목록 로드"""
        self.voice_list.clear()

        for profile in self.tts_manager.get_all_profiles():
            # 아이템 텍스트
            engine_name = profile.engine_id.upper()
            gender = "여성" if profile.gender == "female" else "남성"
            emotion_mark = "★감정" if profile.supports_emotion else ""
            clone_mark = "🎤클론" if profile.is_cloned else ""

            text = f"{profile.name} ({engine_name})\n   {gender} / {profile.style}  {emotion_mark} {clone_mark}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, profile.engine_id)
            self.voice_list.addItem(item)

    def _load_custom_voices(self):
        """커스텀 음성 로드"""
        self.custom_voice_list.clear()

        for profile in self.tts_manager.profile_manager.get_custom_profiles():
            gender = "여성" if profile.gender == "female" else "남성"
            text = f"🎤 {profile.name}\n   {gender} | {profile.created_at[:10] if profile.created_at else ''}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            self.custom_voice_list.addItem(item)

        # 클로닝 엔진 없으면 버튼 비활성화
        if not self.tts_manager.get_cloning_engines():
            self.btn_add_voice.setEnabled(False)
            self.btn_add_voice.setToolTip("OpenVoice 엔진이 필요합니다")

    def _filter_voices(self):
        """엔진별 필터링"""
        filter_engine = self.combo_engine_filter.currentData()

        for i in range(self.voice_list.count()):
            item = self.voice_list.item(i)
            engine_id = item.data(Qt.ItemDataRole.UserRole + 1)

            if filter_engine == "all" or engine_id == filter_engine:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _on_voice_selected(self):
        """음성 선택 시"""
        items = self.voice_list.selectedItems()
        if not items:
            return

        voice_id = items[0].data(Qt.ItemDataRole.UserRole)
        profile = self.tts_manager.profile_manager.get_profile(voice_id)

        if profile:
            # 감정 지원 여부에 따라 활성화
            self.combo_emotion.setEnabled(profile.supports_emotion)
            self.spin_emotion_strength.setEnabled(profile.supports_emotion)

    def _add_custom_voice(self):
        """커스텀 음성 추가"""
        # 클로닝 엔진 확인
        cloning_engines = self.tts_manager.get_cloning_engines()
        if not cloning_engines:
            QMessageBox.warning(self, "경고", "음성 클로닝을 지원하는 엔진이 없습니다.\nOpenVoice를 설치해주세요.")
            return

        # 파일 선택
        filepath, _ = QFileDialog.getOpenFileName(
            self, "참조 음성 선택",
            "", "Audio Files (*.wav *.mp3)"
        )
        if not filepath:
            return

        # 이름 입력 (간단히 다이얼로그)
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "음성 이름", "새 음성의 이름을 입력하세요:")
        if not ok or not name:
            return

        # 클로닝 실행
        try:
            profile = self.tts_manager.clone_voice(filepath, name)
            if profile:
                QMessageBox.information(self, "성공", f"'{name}' 음성이 등록되었습니다.")
                self._load_custom_voices()
                self._load_voices()
            else:
                QMessageBox.warning(self, "실패", "음성 클로닝에 실패했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"클로닝 오류: {str(e)}")

    def _delete_custom_voice(self):
        """커스텀 음성 삭제"""
        items = self.custom_voice_list.selectedItems()
        if not items:
            return

        voice_id = items[0].data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self, "음성 삭제",
            "선택한 커스텀 음성을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.tts_manager.delete_cloned_voice(voice_id):
                self._load_custom_voices()
                self._load_voices()

    def apply_settings(self):
        """설정 적용"""
        # 기본 엔진
        self.tts_manager.default_engine_id = self.combo_default_engine.currentData()

        # 음성 선택
        items = self.voice_list.selectedItems()
        if items:
            voice_id = items[0].data(Qt.ItemDataRole.UserRole)
            self.tts_manager.current_settings.voice_id = voice_id

            # 엔진 ID도 업데이트
            profile = self.tts_manager.profile_manager.get_profile(voice_id)
            if profile:
                self.tts_manager.current_settings.engine_id = profile.engine_id

        # 음성 조절
        self.tts_manager.current_settings.speed = self.slider_speed.value()
        self.tts_manager.current_settings.pitch = self.slider_pitch.value()
        self.tts_manager.current_settings.volume = self.slider_volume.value()
        self.tts_manager.current_settings.emotion = self.combo_emotion.currentData()
        self.tts_manager.current_settings.emotion_strength = self.spin_emotion_strength.value()

        # 시그널 발생
        self.settings_changed.emit(self.tts_manager.get_settings_dict())

        self.accept()

    def get_settings(self) -> dict:
        """현재 설정 반환 (기존 호환용)"""
        return self.tts_manager.get_settings_dict()
