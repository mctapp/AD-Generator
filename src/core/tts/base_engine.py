# core/tts/base_engine.py
# TTS 엔진 추상 기본 클래스

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Callable


class EngineType(Enum):
    """엔진 타입"""
    CLOUD_API = "cloud"      # CLOVA, Google, Azure 등 클라우드 API
    LOCAL = "local"          # MeloTTS, Piper 등 로컬 엔진
    LOCAL_CLONE = "clone"    # OpenVoice 등 클로닝 지원 로컬 엔진


@dataclass
class VoiceInfo:
    """음성 정보 (엔진 내부용)"""
    id: str                          # 음성 ID (예: "vdain", "vyuna")
    name: str                        # 표시 이름 (예: "다인", "유나")
    gender: str                      # "male" / "female"
    language: str = "ko-KR"          # 언어 코드
    style: str = ""                  # 스타일 (예: "calm", "bright")
    description: str = ""            # 설명
    supports_emotion: bool = False   # 감정 지원 여부
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineCapabilities:
    """엔진 기능 정보"""
    engine_type: EngineType
    supports_cloning: bool = False       # 음성 클로닝 지원
    supports_emotion: bool = False       # 감정 표현 지원
    supports_ssml: bool = False          # SSML 지원
    requires_gpu: bool = False           # GPU 필요 여부
    requires_api_key: bool = False       # API 키 필요 여부
    max_text_length: int = 5000          # 최대 텍스트 길이
    supported_formats: List[str] = field(default_factory=lambda: ["wav"])


@dataclass
class TTSRequest:
    """TTS 생성 요청"""
    text: str
    voice_id: str
    output_path: str
    speed: int = 0               # -5 ~ +5 (CLOVA 호환)
    pitch: int = 0               # -5 ~ +5
    volume: int = 0              # -5 ~ +5
    emotion: int = 0             # 0: 중립, 1: 슬픔, 2: 기쁨
    emotion_strength: int = 1    # 0 ~ 2
    format: str = "wav"


@dataclass
class TTSResult:
    """TTS 생성 결과"""
    success: bool
    output_path: str = ""
    duration_ms: int = 0
    error_message: str = ""


class BaseTTSEngine(ABC):
    """TTS 엔진 추상 기본 클래스

    모든 TTS 엔진은 이 클래스를 상속받아 구현합니다.
    """

    def __init__(self):
        self._is_initialized = False
        self.on_progress: Optional[Callable[[int, int, str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """엔진 고유 ID (예: 'clova', 'openvoice', 'melotts')"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """표시 이름 (예: 'NAVER CLOVA', 'OpenVoice v2')"""
        pass

    @abstractmethod
    def get_capabilities(self) -> EngineCapabilities:
        """엔진 기능 정보 반환"""
        pass

    @abstractmethod
    def get_voices(self) -> List[VoiceInfo]:
        """사용 가능한 음성 목록 반환"""
        pass

    @abstractmethod
    def generate(self, request: TTSRequest) -> TTSResult:
        """TTS 생성

        Args:
            request: TTS 생성 요청

        Returns:
            TTSResult: 생성 결과
        """
        pass

    @abstractmethod
    def is_available(self) -> tuple:
        """엔진 사용 가능 여부 확인

        Returns:
            tuple: (사용가능여부: bool, 메시지: str)
        """
        pass

    def initialize(self) -> bool:
        """엔진 초기화 (필요한 경우 오버라이드)

        Returns:
            bool: 초기화 성공 여부
        """
        self._is_initialized = True
        return True

    def shutdown(self):
        """엔진 종료 (필요한 경우 오버라이드)"""
        self._is_initialized = False

    @property
    def is_initialized(self) -> bool:
        """초기화 여부"""
        return self._is_initialized

    # === 클로닝 지원 엔진용 (선택적 구현) ===

    def supports_cloning(self) -> bool:
        """클로닝 지원 여부"""
        return self.get_capabilities().supports_cloning

    def clone_voice(self, reference_audio: str, voice_name: str) -> Optional[VoiceInfo]:
        """음성 클로닝 (지원 엔진만)

        Args:
            reference_audio: 참조 오디오 파일 경로 (6초 이상 권장)
            voice_name: 새 음성 이름

        Returns:
            VoiceInfo: 생성된 음성 정보, 실패 시 None
        """
        raise NotImplementedError("This engine does not support voice cloning")

    def delete_cloned_voice(self, voice_id: str) -> bool:
        """클로닝된 음성 삭제

        Args:
            voice_id: 삭제할 음성 ID

        Returns:
            bool: 삭제 성공 여부
        """
        raise NotImplementedError("This engine does not support voice cloning")

    def get_cloned_voices(self) -> List[VoiceInfo]:
        """클로닝된 음성 목록

        Returns:
            List[VoiceInfo]: 클로닝된 음성 목록
        """
        return []
