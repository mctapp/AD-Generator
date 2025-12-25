# core/tts/engines/clova_engine.py
# NAVER CLOVA Voice TTS 엔진

import os
import ssl
import urllib.request
import urllib.parse
from typing import List, Optional

from ..base_engine import (
    BaseTTSEngine, EngineType, EngineCapabilities,
    VoiceInfo, TTSRequest, TTSResult
)

# SSL 인증서 우회 (macOS 호환성)
ssl._create_default_https_context = ssl._create_unverified_context


class CLOVAEngine(BaseTTSEngine):
    """NAVER CLOVA Voice TTS 엔진"""

    API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

    # 기본 음성 목록
    DEFAULT_VOICES = [
        VoiceInfo(
            id="vdain", name="다인", gender="female",
            style="차분한 톤", supports_emotion=True,
            description="AD 나레이션에 적합"
        ),
        VoiceInfo(
            id="vhyeri", name="혜리", gender="female",
            style="밝은 톤", supports_emotion=False,
            description="밝고 경쾌한 느낌"
        ),
        VoiceInfo(
            id="vyuna", name="유나", gender="female",
            style="또렷한 톤", supports_emotion=True,
            description="명확한 발음"
        ),
        VoiceInfo(
            id="vmijin", name="미진", gender="female",
            style="부드러운 톤", supports_emotion=False,
            description="부드럽고 차분함"
        ),
        VoiceInfo(
            id="vdaeseong", name="대성", gender="male",
            style="차분한 톤", supports_emotion=False,
            description="남성 나레이션"
        ),
        VoiceInfo(
            id="nara", name="나라", gender="female",
            style="기본", supports_emotion=False,
            description="기본 여성 음성"
        ),
        VoiceInfo(
            id="nminsang", name="민상", gender="male",
            style="기본", supports_emotion=False,
            description="기본 남성 음성"
        ),
        VoiceInfo(
            id="njihun", name="지훈", gender="male",
            style="뉴스", supports_emotion=False,
            description="뉴스 앵커 스타일"
        ),
        VoiceInfo(
            id="njiyun", name="지윤", gender="female",
            style="뉴스", supports_emotion=False,
            description="뉴스 앵커 스타일"
        ),
        VoiceInfo(
            id="nsujin", name="수진", gender="female",
            style="밝은 톤", supports_emotion=False,
            description="밝은 여성 음성"
        ),
    ]

    def __init__(self, client_id: str = "", client_secret: str = ""):
        super().__init__()
        self._client_id = client_id
        self._client_secret = client_secret
        self.api_delay = 0.3  # API 호출 간 대기 시간 (초)

    @property
    def engine_id(self) -> str:
        return "clova"

    @property
    def display_name(self) -> str:
        return "NAVER CLOVA"

    def get_capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            engine_type=EngineType.CLOUD_API,
            supports_cloning=False,
            supports_emotion=True,  # 일부 음성만
            supports_ssml=False,
            requires_gpu=False,
            requires_api_key=True,
            max_text_length=5000,
            supported_formats=["wav", "mp3"]
        )

    def get_voices(self) -> List[VoiceInfo]:
        return self.DEFAULT_VOICES.copy()

    def set_credentials(self, client_id: str, client_secret: str):
        """API 인증 정보 설정"""
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def has_credentials(self) -> bool:
        """API 키 설정 여부"""
        return bool(self._client_id and self._client_secret)

    def is_available(self) -> tuple:
        """엔진 사용 가능 여부"""
        if not self._client_id or not self._client_secret:
            return False, "API 키가 설정되지 않았습니다"
        return True, "사용 가능"

    def generate(self, request: TTSRequest) -> TTSResult:
        """TTS 생성"""
        if not self.has_credentials:
            return TTSResult(
                success=False,
                error_message="API 키가 설정되지 않았습니다"
            )

        # 요청 데이터 구성
        enc_text = urllib.parse.quote(request.text)

        params = [
            f"speaker={request.voice_id}",
            f"text={enc_text}",
            f"volume={request.volume}",
            f"speed={request.speed}",
            f"pitch={request.pitch}",
            f"format={request.format}"
        ]

        # 감정 설정 (지원 음성만)
        if request.emotion > 0:
            params.append(f"emotion={request.emotion}")
            params.append(f"emotion-strength={request.emotion_strength}")

        data = "&".join(params)

        # API 요청
        http_request = urllib.request.Request(self.API_URL)
        http_request.add_header("X-NCP-APIGW-API-KEY-ID", self._client_id)
        http_request.add_header("X-NCP-APIGW-API-KEY", self._client_secret)
        http_request.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            response = urllib.request.urlopen(
                http_request,
                data=data.encode('utf-8'),
                timeout=30
            )

            if response.getcode() == 200:
                # 출력 디렉토리 생성
                os.makedirs(os.path.dirname(request.output_path), exist_ok=True)

                with open(request.output_path, 'wb') as f:
                    f.write(response.read())

                return TTSResult(
                    success=True,
                    output_path=request.output_path
                )
            else:
                return TTSResult(
                    success=False,
                    error_message=f"HTTP {response.getcode()}"
                )

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP 오류: {e.code}"
            if e.code == 401:
                error_msg = "인증 실패: API 키를 확인하세요"
            elif e.code == 429:
                error_msg = "요청 한도 초과"
            return TTSResult(success=False, error_message=error_msg)

        except Exception as e:
            return TTSResult(
                success=False,
                error_message=f"오류: {str(e)}"
            )

    def test_connection(self) -> tuple:
        """API 연결 테스트

        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.has_credentials:
            return False, "API 키가 설정되지 않았습니다"

        # 짧은 테스트 요청
        test_text = "테스트"
        enc_text = urllib.parse.quote(test_text)
        data = f"speaker=nara&text={enc_text}&volume=0&speed=0&pitch=0&format=wav"

        http_request = urllib.request.Request(self.API_URL)
        http_request.add_header("X-NCP-APIGW-API-KEY-ID", self._client_id)
        http_request.add_header("X-NCP-APIGW-API-KEY", self._client_secret)
        http_request.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            response = urllib.request.urlopen(
                http_request,
                data=data.encode('utf-8'),
                timeout=10
            )

            if response.getcode() == 200:
                return True, "연결 성공"
            else:
                return False, f"HTTP {response.getcode()}"

        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "인증 실패: API 키를 확인하세요"
            elif e.code == 429:
                return False, "요청 한도 초과"
            else:
                return False, f"HTTP 오류: {e.code}"
        except Exception as e:
            return False, f"연결 오류: {str(e)}"
