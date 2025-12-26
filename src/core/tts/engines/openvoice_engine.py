# core/tts/engines/openvoice_engine.py
# OpenVoice v2 로컬 TTS 엔진 (스텁)

import os
import shutil
from typing import List, Optional, Dict

from ..base_engine import (
    BaseTTSEngine, EngineType, EngineCapabilities,
    VoiceInfo, TTSRequest, TTSResult
)


class OpenVoiceEngine(BaseTTSEngine):
    """OpenVoice v2 로컬 TTS 엔진

    음성 클로닝을 지원하는 로컬 TTS 엔진입니다.
    6초 이상의 참조 오디오로 새 음성을 생성할 수 있습니다.

    참고:
    - OpenVoice v2: https://github.com/myshell-ai/OpenVoice
    - 한국어 지원을 위해 MeloTTS와 함께 사용
    - GPU 권장 (CPU에서도 동작 가능하나 느림)
    """

    def __init__(self, models_path: str = None):
        super().__init__()
        self._models_path = models_path or os.path.expanduser("~/.adflow/models/openvoice")
        self._cloned_voices_dir = os.path.join(self._models_path, "cloned_voices")
        self._cloned_voices: Dict[str, VoiceInfo] = {}

        # OpenVoice 및 MeloTTS 모듈 (동적 로드)
        self._openvoice = None
        self._melotts = None
        self._device = None
        self._tone_converter = None
        self._tts_model = None

        self._ensure_dirs()
        self._load_cloned_voices()

    def _ensure_dirs(self):
        """디렉토리 생성"""
        os.makedirs(self._models_path, exist_ok=True)
        os.makedirs(self._cloned_voices_dir, exist_ok=True)

    @property
    def engine_id(self) -> str:
        return "openvoice"

    @property
    def display_name(self) -> str:
        return "OpenVoice v2"

    def get_capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            engine_type=EngineType.LOCAL_CLONE,
            supports_cloning=True,
            supports_emotion=False,
            supports_ssml=False,
            requires_gpu=False,  # CPU에서도 동작 가능
            requires_api_key=False,
            max_text_length=1000,
            supported_formats=["wav"]
        )

    def get_voices(self) -> List[VoiceInfo]:
        """기본 음성 + 클로닝된 음성 목록"""
        voices = []

        # 기본 음성 (MeloTTS 기본 화자들)
        default_voices = [
            VoiceInfo(
                id="melo_kr",
                name="MeloTTS KR",
                gender="female",
                language="ko-KR",
                style="기본 한국어 TTS",
                description="MeloTTS 기본 한국어 음성"
            ),
        ]
        voices.extend(default_voices)

        # 클로닝된 음성
        voices.extend(self._cloned_voices.values())

        return voices

    def is_available(self) -> tuple:
        """OpenVoice 사용 가능 여부 확인"""
        # OpenVoice 모듈 확인
        try:
            # 실제 구현 시: import openvoice, melo_tts
            # 현재는 스텁이므로 설치 여부만 확인
            import importlib.util

            openvoice_spec = importlib.util.find_spec("openvoice")
            melo_spec = importlib.util.find_spec("melo")

            if openvoice_spec is None:
                return (False, "OpenVoice가 설치되지 않음")

            if melo_spec is None:
                return (False, "MeloTTS가 설치되지 않음")

            return (True, "사용 가능")

        except Exception as e:
            return (False, f"확인 실패: {str(e)}")

    def initialize(self) -> bool:
        """모델 로드"""
        available, msg = self.is_available()
        if not available:
            if self.on_error:
                self.on_error("initialize", msg)
            return False

        try:
            # 실제 구현 시 모델 로드
            # import torch
            # from openvoice import se_extractor
            # from openvoice.api import ToneColorConverter
            # from melo.api import TTS as MeloTTS
            #
            # self._device = "cuda" if torch.cuda.is_available() else "cpu"
            # self._tone_converter = ToneColorConverter(...)
            # self._tts_model = MeloTTS(language='KR', device=self._device)

            self._is_initialized = True
            return True

        except Exception as e:
            if self.on_error:
                self.on_error("initialize", f"초기화 실패: {str(e)}")
            return False

    def generate(self, request: TTSRequest) -> TTSResult:
        """TTS 생성"""
        # 사용 가능 여부 확인
        available, msg = self.is_available()
        if not available:
            return TTSResult(
                success=False,
                error_message=f"OpenVoice를 사용할 수 없습니다: {msg}"
            )

        # 스텁: 실제 구현 필요
        # 실제 구현 시:
        # 1. MeloTTS로 기본 음성 생성
        # 2. 클로닝된 음성인 경우 ToneColorConverter로 음색 변환
        # 3. 속도/피치 조절 적용

        return TTSResult(
            success=False,
            error_message="OpenVoice 엔진은 아직 완전히 구현되지 않았습니다. "
                          "pip install openvoice melo 명령으로 설치 후 사용하세요."
        )

    # === 음성 클로닝 ===

    def clone_voice(self, reference_audio: str, voice_name: str) -> Optional[VoiceInfo]:
        """음성 클로닝

        참조 오디오에서 음색을 추출하여 새 음성을 생성합니다.

        Args:
            reference_audio: 참조 오디오 파일 경로 (6초 이상 권장)
            voice_name: 새 음성의 이름

        Returns:
            VoiceInfo: 생성된 음성 정보
        """
        available, msg = self.is_available()
        if not available:
            return None

        if not os.path.exists(reference_audio):
            return None

        try:
            # 고유 ID 생성
            import uuid
            voice_id = f"clone_{uuid.uuid4().hex[:8]}"

            # 참조 오디오 복사
            ref_filename = f"{voice_id}{os.path.splitext(reference_audio)[1]}"
            ref_dest = os.path.join(self._cloned_voices_dir, ref_filename)
            shutil.copy2(reference_audio, ref_dest)

            # 실제 구현 시: 음색 특성 추출 및 저장
            # se = se_extractor.get_se(reference_audio, ...)
            # torch.save(se, os.path.join(self._cloned_voices_dir, f"{voice_id}.pth"))

            # 음성 정보 생성
            voice_info = VoiceInfo(
                id=voice_id,
                name=voice_name,
                gender="unknown",
                language="ko-KR",
                style="클로닝됨",
                description=f"'{os.path.basename(reference_audio)}'에서 클로닝",
                metadata={
                    "is_cloned": True,
                    "reference_file": ref_filename
                }
            )

            self._cloned_voices[voice_id] = voice_info
            self._save_cloned_voices()

            return voice_info

        except Exception as e:
            if self.on_error:
                self.on_error("clone_voice", f"클로닝 실패: {str(e)}")
            return None

    def delete_cloned_voice(self, voice_id: str) -> bool:
        """클로닝된 음성 삭제"""
        if voice_id not in self._cloned_voices:
            return False

        try:
            voice_info = self._cloned_voices[voice_id]

            # 참조 파일 삭제
            ref_file = voice_info.metadata.get("reference_file", "")
            if ref_file:
                ref_path = os.path.join(self._cloned_voices_dir, ref_file)
                if os.path.exists(ref_path):
                    os.remove(ref_path)

            # 음색 데이터 삭제
            se_path = os.path.join(self._cloned_voices_dir, f"{voice_id}.pth")
            if os.path.exists(se_path):
                os.remove(se_path)

            del self._cloned_voices[voice_id]
            self._save_cloned_voices()

            return True

        except Exception as e:
            if self.on_error:
                self.on_error("delete_cloned_voice", f"삭제 실패: {str(e)}")
            return False

    def get_cloned_voices(self) -> List[VoiceInfo]:
        """클로닝된 음성 목록"""
        return list(self._cloned_voices.values())

    def _load_cloned_voices(self):
        """저장된 클로닝 음성 로드"""
        voices_file = os.path.join(self._cloned_voices_dir, "voices.json")
        if os.path.exists(voices_file):
            try:
                import json
                with open(voices_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for voice_data in data.get('voices', []):
                        voice = VoiceInfo(
                            id=voice_data['id'],
                            name=voice_data['name'],
                            gender=voice_data.get('gender', 'unknown'),
                            language=voice_data.get('language', 'ko-KR'),
                            style=voice_data.get('style', ''),
                            description=voice_data.get('description', ''),
                            metadata=voice_data.get('metadata', {})
                        )
                        self._cloned_voices[voice.id] = voice
            except Exception:
                pass

    def _save_cloned_voices(self):
        """클로닝 음성 저장"""
        voices_file = os.path.join(self._cloned_voices_dir, "voices.json")
        try:
            import json
            data = {
                'voices': [
                    {
                        'id': v.id,
                        'name': v.name,
                        'gender': v.gender,
                        'language': v.language,
                        'style': v.style,
                        'description': v.description,
                        'metadata': v.metadata
                    }
                    for v in self._cloned_voices.values()
                ]
            }
            with open(voices_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
