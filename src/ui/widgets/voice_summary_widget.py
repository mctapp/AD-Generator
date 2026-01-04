# ui/widgets/voice_summary_widget.py
# 음성 설정 요약 위젯 (메인 UI용)

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

# 새 TTS 시스템
try:
    from ...core.tts import get_tts_manager
    HAS_TTS_MANAGER = True
except ImportError:
    HAS_TTS_MANAGER = False


class VoiceSummaryWidget(QWidget):
    """음성 설정 요약 위젯

    메인 윈도우에서 간략하게 현재 음성 설정을 표시하고,
    상세 설정 다이얼로그로 이동할 수 있게 함.
    """

    preview_requested = pyqtSignal()  # 미리듣기 요청
    settings_changed = pyqtSignal(dict)  # 설정 변경
    open_settings_requested = pyqtSignal()  # TTS 설정 다이얼로그 열기 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_settings = {
            'speaker': 'vdain',
            'speed': 0,
            'pitch': 0,
            'volume': 0,
            'emotion': 0,
            'emotion_strength': 1
        }
        self._voice_names = {
            'vdain': '다인',
            'vhyeri': '혜리',
            'vyuna': '유나',
            'vmijin': '미진',
            'vdaeseong': '대성',
            'nara': '나라',
            'nminsang': '민상',
            'njihun': '지훈',
            'njiyun': '지윤',
            'nsujin': '수진',
        }
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # 아이콘
        icon_label = QLabel("🎙")
        icon_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(icon_label)

        # 음성 정보
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.label_voice = QLabel("다인 (CLOVA)")
        self.label_voice.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
        """)
        info_layout.addWidget(self.label_voice)

        self.label_params = QLabel("속도: 0  |  피치: 0  |  볼륨: 0")
        self.label_params.setStyleSheet("""
            font-size: 12px;
            color: #888;
        """)
        info_layout.addWidget(self.label_params)

        layout.addLayout(info_layout, 1)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        # 미리듣기 버튼
        self.btn_preview = QPushButton("미리듣기")
        self.btn_preview.setProperty('class', 'success')
        self.btn_preview.setFixedWidth(80)
        self.btn_preview.clicked.connect(self.preview_requested.emit)
        btn_layout.addWidget(self.btn_preview)

        # TTS 설정 버튼
        self.btn_settings = QPushButton("TTS 설정")
        self.btn_settings.setFixedWidth(100)
        self.btn_settings.clicked.connect(self.open_settings_requested.emit)
        btn_layout.addWidget(self.btn_settings)

        layout.addLayout(btn_layout)

    def update_display(self):
        """표시 업데이트 - TTSEngineManager의 커스텀 음성 정보도 표시"""
        settings = self._current_settings

        # 음성 이름 및 엔진 정보 가져오기
        voice_name = None
        engine_name = "CLOVA"
        is_cloned = False

        # TTSEngineManager에서 현재 프로파일 정보 가져오기
        if HAS_TTS_MANAGER:
            try:
                tts_manager = get_tts_manager()
                profile = tts_manager.get_current_profile()
                if profile:
                    voice_name = profile.name
                    engine_name = profile.engine_id.upper()
                    is_cloned = profile.is_cloned
            except Exception:
                pass

        # 폴백: 레거시 설정에서 이름 가져오기
        if voice_name is None:
            speaker = settings.get('speaker', 'vdain')
            voice_name = self._voice_names.get(speaker, speaker)

            # 엔진 표시 (voice_id 형식: "clova.vdain" 또는 "vdain")
            if '.' in speaker:
                engine_id, _ = speaker.split('.', 1)
                engine_name = engine_id.upper()

        # 클로닝된 음성은 아이콘 표시
        if is_cloned:
            self.label_voice.setText(f"🎤 {voice_name} ({engine_name})")
        else:
            self.label_voice.setText(f"{voice_name} ({engine_name})")

        # 파라미터
        speed = settings.get('speed', 0)
        pitch = settings.get('pitch', 0)
        volume = settings.get('volume', 0)

        params_text = f"속도: {speed:+d}  |  피치: {pitch:+d}  |  볼륨: {volume:+d}"

        emotion = settings.get('emotion', 0)
        if emotion > 0:
            emotion_names = {1: '슬픔', 2: '기쁨'}
            params_text += f"  |  감정: {emotion_names.get(emotion, '-')}"

        self.label_params.setText(params_text)

    def get_settings(self) -> dict:
        """현재 설정 반환 (기존 VoicePanel 호환용)"""
        return self._current_settings.copy()

    def set_settings(self, settings: dict):
        """설정 적용 (기존 VoicePanel 호환용)"""
        self._current_settings.update(settings)
        self.update_display()

    def apply_tts_manager_settings(self, tts_manager):
        """TTSEngineManager의 설정을 적용"""
        if hasattr(tts_manager, 'get_settings_dict'):
            settings = tts_manager.get_settings_dict()
            self.set_settings(settings)
        elif hasattr(tts_manager, 'current_settings'):
            cs = tts_manager.current_settings
            self._current_settings = {
                'speaker': cs.voice_id,
                'speed': cs.speed,
                'pitch': cs.pitch,
                'volume': cs.volume,
                'emotion': cs.emotion,
                'emotion_strength': cs.emotion_strength
            }
            self.update_display()

    def register_voice_name(self, voice_id: str, name: str):
        """음성 이름 등록 (커스텀 음성용)"""
        self._voice_names[voice_id] = name
