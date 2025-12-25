# core/tts/__init__.py
# TTS 모듈

from .base_engine import (
    BaseTTSEngine,
    EngineType,
    EngineCapabilities,
    VoiceInfo,
    TTSRequest,
    TTSResult
)
from .voice_profile import VoiceProfile, VoiceProfileManager, TTSSettings
from .engine_manager import TTSEngineManager, get_tts_manager
from .engines import CLOVAEngine, OpenVoiceEngine


def initialize_tts_engines(client_id: str = "", client_secret: str = "",
                           enable_openvoice: bool = True):
    """TTS 엔진 초기화

    앱 시작 시 호출하여 기본 엔진들을 등록합니다.

    Args:
        client_id: CLOVA API Client ID
        client_secret: CLOVA API Client Secret
        enable_openvoice: OpenVoice 엔진 활성화 여부
    """
    manager = get_tts_manager()

    # CLOVA 엔진 등록
    clova = CLOVAEngine(client_id, client_secret)
    manager.register_engine(clova)

    # OpenVoice 엔진 등록 (설치되어 있는 경우)
    if enable_openvoice:
        openvoice = OpenVoiceEngine()
        available, _ = openvoice.is_available()
        # 설치 여부와 관계없이 등록 (UI에서 상태 표시)
        manager.register_engine(openvoice)

    # 기본 음성 설정
    if not manager.current_settings.voice_id:
        manager.current_settings.voice_id = "clova.vdain"
        manager.current_settings.engine_id = "clova"

    return manager
