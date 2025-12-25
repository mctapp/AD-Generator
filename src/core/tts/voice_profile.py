# core/tts/voice_profile.py
# 음성 프로파일 관리

import os
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class VoiceProfile:
    """통합 음성 프로파일

    여러 엔진의 음성을 통합 관리하기 위한 프로파일입니다.
    """
    id: str                          # 고유 ID (예: "clova.vdain", "custom.narrator1")
    name: str                        # 표시 이름
    engine_id: str                   # 소속 엔진 ID
    gender: str                      # "male" / "female"
    language: str = "ko-KR"          # 언어 코드
    style: str = ""                  # 스타일 설명

    # 옵션 지원 여부
    supports_emotion: bool = False
    supports_speed: bool = True
    supports_pitch: bool = True
    supports_volume: bool = True

    # 클로닝 관련
    is_cloned: bool = False          # 클로닝된 음성 여부
    reference_audio: str = ""        # 참조 오디오 경로 (클로닝용)
    created_at: str = ""             # 생성 일시

    # 태그 및 메타데이터
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'VoiceProfile':
        """딕셔너리에서 생성"""
        return cls(**data)

    @property
    def display_name(self) -> str:
        """UI 표시용 이름"""
        gender_icon = "♀" if self.gender == "female" else "♂"
        engine_name = self.engine_id.upper()
        if self.is_cloned:
            return f"🎤 {self.name} ({gender_icon})"
        return f"{self.name} ({engine_name}, {gender_icon})"

    @property
    def short_info(self) -> str:
        """짧은 정보"""
        parts = []
        if self.gender:
            parts.append("여성" if self.gender == "female" else "남성")
        if self.style:
            parts.append(self.style)
        return " / ".join(parts)


@dataclass
class TTSSettings:
    """TTS 설정 (현재 선택된 음성 + 옵션)"""
    voice_id: str = ""               # 선택된 음성 ID
    engine_id: str = "clova"         # 선택된 엔진 ID
    speed: int = 0                   # -5 ~ +5
    pitch: int = 0                   # -5 ~ +5
    volume: int = 0                  # -5 ~ +5
    emotion: int = 0                 # 0: 중립, 1: 슬픔, 2: 기쁨
    emotion_strength: int = 1        # 0 ~ 2

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'TTSSettings':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class VoiceProfileManager:
    """음성 프로파일 매니저

    기본 음성과 커스텀(클로닝) 음성을 통합 관리합니다.
    """

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.adflow")
        self.config_dir = config_dir
        self.custom_voices_dir = os.path.join(config_dir, "custom_voices")
        self.references_dir = os.path.join(self.custom_voices_dir, "references")
        self.profiles_file = os.path.join(self.custom_voices_dir, "profiles.json")

        self._profiles: Dict[str, VoiceProfile] = {}
        self._custom_profiles: Dict[str, VoiceProfile] = {}

        self._ensure_dirs()
        self._load_custom_profiles()

    def _ensure_dirs(self):
        """디렉토리 생성"""
        os.makedirs(self.custom_voices_dir, exist_ok=True)
        os.makedirs(self.references_dir, exist_ok=True)

    def _load_custom_profiles(self):
        """커스텀 프로파일 로드"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for profile_data in data.get('custom_voices', []):
                        profile = VoiceProfile.from_dict(profile_data)
                        self._custom_profiles[profile.id] = profile
            except Exception as e:
                print(f"커스텀 프로파일 로드 실패: {e}")

    def _save_custom_profiles(self):
        """커스텀 프로파일 저장"""
        try:
            data = {
                'custom_voices': [p.to_dict() for p in self._custom_profiles.values()]
            }
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"커스텀 프로파일 저장 실패: {e}")

    def register_profile(self, profile: VoiceProfile):
        """프로파일 등록 (엔진에서 호출)"""
        self._profiles[profile.id] = profile

    def register_custom_profile(self, profile: VoiceProfile) -> bool:
        """커스텀 프로파일 등록"""
        profile.is_cloned = True
        if not profile.created_at:
            profile.created_at = datetime.now().isoformat()
        self._custom_profiles[profile.id] = profile
        self._save_custom_profiles()
        return True

    def delete_custom_profile(self, profile_id: str) -> bool:
        """커스텀 프로파일 삭제"""
        if profile_id in self._custom_profiles:
            profile = self._custom_profiles[profile_id]
            # 참조 오디오 삭제
            if profile.reference_audio:
                ref_path = os.path.join(self.references_dir, profile.reference_audio)
                if os.path.exists(ref_path):
                    try:
                        os.remove(ref_path)
                    except:
                        pass
            del self._custom_profiles[profile_id]
            self._save_custom_profiles()
            return True
        return False

    def get_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        """프로파일 조회"""
        return self._profiles.get(profile_id) or self._custom_profiles.get(profile_id)

    def get_all_profiles(self) -> List[VoiceProfile]:
        """전체 프로파일 목록 (기본 + 커스텀)"""
        all_profiles = list(self._profiles.values()) + list(self._custom_profiles.values())
        return sorted(all_profiles, key=lambda p: (p.is_cloned, p.name))

    def get_profiles_by_engine(self, engine_id: str) -> List[VoiceProfile]:
        """엔진별 프로파일 목록"""
        return [p for p in self.get_all_profiles() if p.engine_id == engine_id]

    def get_custom_profiles(self) -> List[VoiceProfile]:
        """커스텀 프로파일만"""
        return list(self._custom_profiles.values())

    def clear_engine_profiles(self, engine_id: str):
        """특정 엔진의 기본 프로파일 제거"""
        self._profiles = {
            k: v for k, v in self._profiles.items()
            if v.engine_id != engine_id
        }

    def get_reference_path(self, filename: str) -> str:
        """참조 오디오 전체 경로"""
        return os.path.join(self.references_dir, filename)
