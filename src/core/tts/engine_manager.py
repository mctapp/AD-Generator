# core/tts/engine_manager.py
# TTS 엔진 통합 관리자

import os
from typing import Dict, List, Optional, Callable

from .base_engine import BaseTTSEngine, TTSRequest, TTSResult, EngineCapabilities
from .voice_profile import VoiceProfile, VoiceProfileManager, TTSSettings


class TTSEngineManager:
    """TTS 엔진 통합 관리자

    여러 TTS 엔진을 통합 관리하고, 음성 프로파일을 관리합니다.
    """

    _instance = None

    def __new__(cls):
        """싱글톤 패턴"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._engines: Dict[str, BaseTTSEngine] = {}
        self._default_engine_id: str = "clova"
        self._current_settings = TTSSettings()

        # 설정 디렉토리
        self._config_dir = os.path.expanduser("~/.adflow")
        os.makedirs(self._config_dir, exist_ok=True)

        # 프로파일 매니저
        self._profile_manager = VoiceProfileManager(self._config_dir)

        # 콜백
        self.on_engine_status_changed: Optional[Callable[[str, bool], None]] = None

        # 에러 추적
        self._last_clone_error: Optional[str] = None

        self._initialized = True

    def get_last_clone_error(self) -> Optional[str]:
        """마지막 클로닝 에러 메시지 반환"""
        return self._last_clone_error

    # === 엔진 관리 ===

    def register_engine(self, engine: BaseTTSEngine) -> bool:
        """엔진 등록

        Args:
            engine: 등록할 TTS 엔진

        Returns:
            bool: 등록 성공 여부
        """
        engine_id = engine.engine_id
        self._engines[engine_id] = engine

        # 엔진의 음성들을 프로파일로 등록
        self._register_engine_voices(engine)

        return True

    def _register_engine_voices(self, engine: BaseTTSEngine):
        """엔진의 음성들을 프로파일로 등록"""
        # 기존 프로파일 제거
        self._profile_manager.clear_engine_profiles(engine.engine_id)

        # 새 프로파일 등록
        for voice in engine.get_voices():
            profile = VoiceProfile(
                id=f"{engine.engine_id}.{voice.id}",
                name=voice.name,
                engine_id=engine.engine_id,
                gender=voice.gender,
                language=voice.language,
                style=voice.style,
                supports_emotion=voice.supports_emotion,
                metadata=voice.metadata
            )
            self._profile_manager.register_profile(profile)

    def unregister_engine(self, engine_id: str) -> bool:
        """엔진 등록 해제"""
        if engine_id in self._engines:
            engine = self._engines[engine_id]
            engine.shutdown()
            del self._engines[engine_id]
            self._profile_manager.clear_engine_profiles(engine_id)
            return True
        return False

    def get_engine(self, engine_id: str) -> Optional[BaseTTSEngine]:
        """엔진 조회"""
        return self._engines.get(engine_id)

    def get_all_engines(self) -> List[BaseTTSEngine]:
        """전체 엔진 목록"""
        return list(self._engines.values())

    def get_available_engines(self) -> List[BaseTTSEngine]:
        """사용 가능한 엔진 목록"""
        return [e for e in self._engines.values() if e.is_available()[0]]

    # === 기본 엔진 ===

    @property
    def default_engine_id(self) -> str:
        return self._default_engine_id

    @default_engine_id.setter
    def default_engine_id(self, engine_id: str):
        if engine_id in self._engines:
            self._default_engine_id = engine_id

    def get_default_engine(self) -> Optional[BaseTTSEngine]:
        """기본 엔진 반환"""
        return self._engines.get(self._default_engine_id)

    # === TTS 설정 ===

    @property
    def current_settings(self) -> TTSSettings:
        return self._current_settings

    @current_settings.setter
    def current_settings(self, settings: TTSSettings):
        self._current_settings = settings

    def get_settings_dict(self) -> dict:
        """현재 설정을 딕셔너리로 반환 (기존 voice_settings 호환)"""
        profile = self._profile_manager.get_profile(self._current_settings.voice_id)
        if profile:
            # voice_id에서 실제 음성 ID 추출 (예: "clova.vdain" -> "vdain")
            voice_id_parts = self._current_settings.voice_id.split('.')
            speaker = voice_id_parts[-1] if len(voice_id_parts) > 1 else voice_id_parts[0]
        else:
            speaker = "vdain"

        return {
            'speaker': speaker,
            'speed': self._current_settings.speed,
            'pitch': self._current_settings.pitch,
            'volume': self._current_settings.volume,
            'emotion': self._current_settings.emotion,
            'emotion_strength': self._current_settings.emotion_strength
        }

    # === 음성 프로파일 ===

    @property
    def profile_manager(self) -> VoiceProfileManager:
        return self._profile_manager

    def get_all_profiles(self) -> List[VoiceProfile]:
        """전체 음성 프로파일"""
        return self._profile_manager.get_all_profiles()

    def get_current_profile(self) -> Optional[VoiceProfile]:
        """현재 선택된 음성 프로파일"""
        return self._profile_manager.get_profile(self._current_settings.voice_id)

    # === TTS 생성 ===

    def generate(self, text: str, output_path: str,
                 voice_id: str = None, **kwargs) -> TTSResult:
        """TTS 생성

        Args:
            text: 변환할 텍스트
            output_path: 출력 파일 경로
            voice_id: 음성 ID (None이면 현재 설정 사용)
            **kwargs: 추가 옵션 (speed, pitch, volume, emotion 등)

        Returns:
            TTSResult: 생성 결과
        """
        # 음성 ID 결정
        if voice_id is None:
            voice_id = self._current_settings.voice_id

        # 프로파일에서 엔진 찾기
        profile = self._profile_manager.get_profile(voice_id)
        if not profile:
            return TTSResult(
                success=False,
                error_message=f"음성을 찾을 수 없습니다: {voice_id}"
            )

        engine = self._engines.get(profile.engine_id)
        if not engine:
            return TTSResult(
                success=False,
                error_message=f"엔진을 찾을 수 없습니다: {profile.engine_id}"
            )

        # 사용 가능 여부 확인
        available, message = engine.is_available()
        if not available:
            return TTSResult(success=False, error_message=message)

        # 요청 생성
        # voice_id에서 실제 음성 ID 추출
        voice_id_parts = voice_id.split('.')
        actual_voice_id = voice_id_parts[-1] if len(voice_id_parts) > 1 else voice_id_parts[0]

        request = TTSRequest(
            text=text,
            voice_id=actual_voice_id,
            output_path=output_path,
            speed=kwargs.get('speed', self._current_settings.speed),
            pitch=kwargs.get('pitch', self._current_settings.pitch),
            volume=kwargs.get('volume', self._current_settings.volume),
            emotion=kwargs.get('emotion', self._current_settings.emotion),
            emotion_strength=kwargs.get('emotion_strength', self._current_settings.emotion_strength)
        )

        return engine.generate(request)

    # === 클로닝 ===

    def get_cloning_engines(self) -> List[BaseTTSEngine]:
        """클로닝 지원 엔진 목록"""
        return [e for e in self._engines.values() if e.supports_cloning()]

    def clone_voice(self, reference_audio: str, voice_name: str,
                    engine_id: str = None, tags: List[str] = None) -> Optional[VoiceProfile]:
        """음성 클로닝

        Args:
            reference_audio: 참조 오디오 파일 경로
            voice_name: 새 음성 이름
            engine_id: 사용할 엔진 ID (None이면 첫 번째 클로닝 엔진)
            tags: 태그 목록

        Returns:
            VoiceProfile: 생성된 프로파일, 실패 시 None
        """
        # 엔진 선택
        if engine_id:
            engine = self._engines.get(engine_id)
        else:
            cloning_engines = self.get_cloning_engines()
            engine = cloning_engines[0] if cloning_engines else None

        if not engine or not engine.supports_cloning():
            return None

        # 클로닝 실행
        voice_info = engine.clone_voice(reference_audio, voice_name)
        if not voice_info:
            # 에러 메시지 저장
            if hasattr(engine, 'get_last_error'):
                self._last_clone_error = engine.get_last_error()
            return None

        # 프로파일 생성 및 등록
        profile = VoiceProfile(
            id=f"custom.{voice_info.id}",
            name=voice_name,
            engine_id=engine.engine_id,
            gender=voice_info.gender,
            language=voice_info.language,
            style=voice_info.style,
            is_cloned=True,
            reference_audio=os.path.basename(reference_audio),
            tags=tags or []
        )

        self._profile_manager.register_custom_profile(profile)
        return profile

    def delete_cloned_voice(self, profile_id: str) -> bool:
        """클로닝된 음성 삭제"""
        profile = self._profile_manager.get_profile(profile_id)
        if not profile or not profile.is_cloned:
            return False

        # 엔진에서도 삭제
        engine = self._engines.get(profile.engine_id)
        if engine and engine.supports_cloning():
            voice_id = profile_id.split('.')[-1]
            engine.delete_cloned_voice(voice_id)

        # 프로파일 삭제
        return self._profile_manager.delete_custom_profile(profile_id)


# 전역 인스턴스
_manager: Optional[TTSEngineManager] = None


def get_tts_manager() -> TTSEngineManager:
    """TTS 엔진 매니저 싱글톤 인스턴스 반환"""
    global _manager
    if _manager is None:
        _manager = TTSEngineManager()
    return _manager
