# ui/widgets/voice_panel.py
# 음성 설정 패널

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QSlider, QPushButton, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os


class VoicePanel(QWidget):
    """음성 설정 패널"""
    
    preview_requested = pyqtSignal()  # 미리듣기 요청
    settings_changed = pyqtSignal(dict)  # 설정 변경
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.voices = {}
        self.load_voices()
        self.setup_ui()
    
    def load_voices(self):
        """음성 목록 로드"""
        # 리소스 파일 경로 찾기
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'voices.json'),
            os.path.join(os.path.dirname(__file__), '..', 'resources', 'voices.json'),
            'src/resources/voices.json',
            'resources/voices.json'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.voices = data.get('voices', {})
                        return
                except Exception:
                    pass
        
        # 기본 음성 목록
        self.voices = {
            "vdain": {"name": "다인", "gender": "여성", "style": "차분한 톤", "emotion": True},
            "vhyeri": {"name": "혜리", "gender": "여성", "style": "밝은 톤", "emotion": False},
            "vyuna": {"name": "유나", "gender": "여성", "style": "또렷한 톤", "emotion": True},
            "vmijin": {"name": "미진", "gender": "여성", "style": "부드러운 톤", "emotion": False},
            "vdaeseong": {"name": "대성", "gender": "남성", "style": "차분한 톤", "emotion": False},
            "nara": {"name": "나라", "gender": "여성", "style": "기본", "emotion": False},
        }
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 음성 설정 그룹
        group = QGroupBox("음성 설정")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        group_layout = QVBoxLayout(group)
        
        # 음성 선택
        voice_row = QHBoxLayout()
        voice_row.addWidget(QLabel("음성:"))
        
        self.combo_voice = QComboBox()
        for voice_id, voice_info in self.voices.items():
            display = f"{voice_info['name']} ({voice_info['gender']}, {voice_info['style']})"
            self.combo_voice.addItem(display, voice_id)
        self.combo_voice.currentIndexChanged.connect(self.on_voice_changed)
        voice_row.addWidget(self.combo_voice, 1)
        
        self.btn_preview = QPushButton("미리듣기")
        self.btn_preview.setFixedWidth(100)
        self.btn_preview.setProperty('class', 'success')  # Qt-Material 그린 버튼
        self.btn_preview.clicked.connect(self.preview_requested.emit)
        voice_row.addWidget(self.btn_preview)
        
        group_layout.addLayout(voice_row)
        
        # 속도 슬라이더
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("속도:"))
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(-5, 5)
        self.slider_speed.setValue(0)
        self.slider_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_speed.setTickInterval(1)
        self.slider_speed.valueChanged.connect(self.on_settings_changed)
        speed_row.addWidget(self.slider_speed, 1)
        self.label_speed = QLabel("0")
        self.label_speed.setFixedWidth(30)
        self.label_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_speed.valueChanged.connect(lambda v: self.label_speed.setText(str(v)))
        speed_row.addWidget(self.label_speed)
        group_layout.addLayout(speed_row)
        
        # 피치 슬라이더
        pitch_row = QHBoxLayout()
        pitch_row.addWidget(QLabel("피치:"))
        self.slider_pitch = QSlider(Qt.Orientation.Horizontal)
        self.slider_pitch.setRange(-5, 5)
        self.slider_pitch.setValue(0)
        self.slider_pitch.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_pitch.setTickInterval(1)
        self.slider_pitch.valueChanged.connect(self.on_settings_changed)
        pitch_row.addWidget(self.slider_pitch, 1)
        self.label_pitch = QLabel("0")
        self.label_pitch.setFixedWidth(30)
        self.label_pitch.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_pitch.valueChanged.connect(lambda v: self.label_pitch.setText(str(v)))
        pitch_row.addWidget(self.label_pitch)
        group_layout.addLayout(pitch_row)
        
        # 볼륨 슬라이더
        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("볼륨:"))
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(-5, 5)
        self.slider_volume.setValue(0)
        self.slider_volume.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_volume.setTickInterval(1)
        self.slider_volume.valueChanged.connect(self.on_settings_changed)
        volume_row.addWidget(self.slider_volume, 1)
        self.label_volume = QLabel("0")
        self.label_volume.setFixedWidth(30)
        self.label_volume.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_volume.valueChanged.connect(lambda v: self.label_volume.setText(str(v)))
        volume_row.addWidget(self.label_volume)
        group_layout.addLayout(volume_row)
        
        # 감정 설정 (선택적)
        emotion_row = QHBoxLayout()
        emotion_row.addWidget(QLabel("감정:"))
        self.combo_emotion = QComboBox()
        self.combo_emotion.addItem("중립", 0)
        self.combo_emotion.addItem("슬픔", 1)
        self.combo_emotion.addItem("기쁨", 2)
        self.combo_emotion.currentIndexChanged.connect(self.on_settings_changed)
        emotion_row.addWidget(self.combo_emotion, 1)
        
        emotion_row.addWidget(QLabel("강도:"))
        self.spin_emotion_strength = QSpinBox()
        self.spin_emotion_strength.setRange(0, 2)
        self.spin_emotion_strength.setValue(1)
        self.spin_emotion_strength.valueChanged.connect(self.on_settings_changed)
        emotion_row.addWidget(self.spin_emotion_strength)
        
        group_layout.addLayout(emotion_row)
        
        layout.addWidget(group)
        
        # 초기 감정 설정 상태
        self.on_voice_changed()
    
    def on_voice_changed(self):
        """음성 변경 시"""
        voice_id = self.combo_voice.currentData()
        if voice_id and voice_id in self.voices:
            has_emotion = self.voices[voice_id].get('emotion', False)
            self.combo_emotion.setEnabled(has_emotion)
            self.spin_emotion_strength.setEnabled(has_emotion)
        
        self.on_settings_changed()
    
    def on_settings_changed(self):
        """설정 변경 시"""
        self.settings_changed.emit(self.get_settings())
    
    def get_settings(self) -> dict:
        """현재 설정 반환"""
        return {
            'speaker': self.combo_voice.currentData(),
            'speed': self.slider_speed.value(),
            'pitch': self.slider_pitch.value(),
            'volume': self.slider_volume.value(),
            'emotion': self.combo_emotion.currentData(),
            'emotion_strength': self.spin_emotion_strength.value()
        }
    
    def set_settings(self, settings: dict):
        """설정 적용"""
        if 'speaker' in settings:
            index = self.combo_voice.findData(settings['speaker'])
            if index >= 0:
                self.combo_voice.setCurrentIndex(index)
        
        if 'speed' in settings:
            self.slider_speed.setValue(settings['speed'])
        
        if 'pitch' in settings:
            self.slider_pitch.setValue(settings['pitch'])
        
        if 'volume' in settings:
            self.slider_volume.setValue(settings['volume'])
        
        if 'emotion' in settings:
            index = self.combo_emotion.findData(settings['emotion'])
            if index >= 0:
                self.combo_emotion.setCurrentIndex(index)
        
        if 'emotion_strength' in settings:
            self.spin_emotion_strength.setValue(settings['emotion_strength'])
