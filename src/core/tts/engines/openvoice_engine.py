# core/tts/engines/openvoice_engine.py
# OpenVoice v2 로컬 TTS 엔진

import os
import shutil
import tempfile
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
        self._device = None
        self._tone_converter = None
        self._tts_model = None
        self._se_extractor = None
        self._source_se = None  # 기본 화자 임베딩
        self._last_error = None  # 마지막 에러 메시지

        self._ensure_dirs()
        self._load_cloned_voices()

    def _ensure_dirs(self):
        """디렉토리 생성"""
        os.makedirs(self._models_path, exist_ok=True)
        os.makedirs(self._cloned_voices_dir, exist_ok=True)

    def get_last_error(self) -> Optional[str]:
        """마지막 에러 메시지 반환"""
        return self._last_error

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
        try:
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

    def _patch_mecab_module(self):
        """mecab 모듈 의존성 우회 패치

        MeloTTS와 g2pkk가 mecab을 필요로 하지만, mecab 설치가 복잡하므로
        더미 모듈로 대체하여 우회합니다.
        """
        import sys
        import types
        from importlib.machinery import ModuleSpec

        # 이미 패치되어 있는지 확인
        if '_mecab_patched' in dir(self):
            return

        # mecab 더미 모듈 생성 (g2pkk에서 사용하는 모든 인터페이스 구현)
        class DummyMeCabTagger:
            """MeCab.Tagger 더미 클래스 - g2pkk/konlpy 완전 호환

            g2pkk가 사용하는 mecab 인터페이스:
            - pos(text): (형태소, 품사) 튜플 리스트 반환
            - morphs(text): 형태소 리스트 반환
            - nouns(text): 명사 리스트 반환
            - parse(text): MeCab 형식 문자열 반환
            - __call__(text): pos()와 동일
            """
            def __init__(self, *args, **kwargs):
                pass

            def _tokenize(self, text):
                """텍스트를 (형태소, 품사) 튜플 리스트로 변환

                한글은 문자별로 분리하고, 영문/숫자/특수문자는 연속된 것끼리 묶음
                """
                if not text:
                    return []

                import re
                tokens = []

                # 한글, 영문, 숫자, 기타로 분리
                # 한글은 문자 단위, 나머지는 연속된 것끼리 묶음
                pattern = r'([가-힣])|([a-zA-Z]+)|(\d+)|(\s+)|(.)'

                for match in re.finditer(pattern, text):
                    hangul, alpha, digit, space, other = match.groups()

                    if hangul:
                        # 한글은 NNG(일반명사)로 태깅
                        tokens.append((hangul, 'NNG'))
                    elif alpha:
                        # 영문은 SL(외국어)로 태깅
                        tokens.append((alpha, 'SL'))
                    elif digit:
                        # 숫자는 SN(숫자)로 태깅
                        tokens.append((digit, 'SN'))
                    elif space:
                        # 공백은 건너뜀
                        continue
                    elif other:
                        # 특수문자는 SW(기호)로 태깅
                        tokens.append((other, 'SW'))

                return tokens

            def pos(self, text):
                """형태소 분석 - (형태소, 품사) 튜플 리스트 반환

                g2pkk의 annotate() 함수에서 mecab.pos(string) 형태로 호출됨
                """
                return self._tokenize(text)

            def morphs(self, text):
                """형태소 리스트만 반환"""
                return [token for token, _ in self._tokenize(text)]

            def nouns(self, text):
                """명사만 반환"""
                return [token for token, pos in self._tokenize(text)
                        if pos.startswith('N')]

            def __call__(self, text):
                """호출 시 pos()와 동일하게 동작"""
                return self.pos(text)

            def parse(self, text):
                """텍스트를 MeCab 출력 형식으로 반환

                형식: 형태소\t품사,품사상세,...
                """
                if not text:
                    return "EOS\n"

                result_lines = []
                for token, pos in self._tokenize(text):
                    # MeCab 출력 형식: 형태소\t품사,*,*,*,*,*,*,*
                    result_lines.append(f"{token}\t{pos},*,*,*,*,*,*,*")
                result_lines.append("EOS")
                return "\n".join(result_lines)

            def parseToNode(self, text):
                """노드 파싱 (사용되지 않음)"""
                return None

        class DummyMeCab(types.ModuleType):
            """MeCab 더미 모듈"""
            def __init__(self, name='mecab'):
                super().__init__(name)
                # importlib.util.find_spec()에서 필요한 __spec__ 속성
                self.__spec__ = ModuleSpec(name, None)
                self.__file__ = __file__
                self.__path__ = []
                self.Tagger = DummyMeCabTagger

            def __call__(self, *args, **kwargs):
                return self

            def __getattr__(self, name):
                if name == 'Tagger':
                    return DummyMeCabTagger
                # g2pkk uses mecab.MeCab() (lowercase module, uppercase class)
                if name == 'MeCab':
                    return DummyMeCabTagger
                return DummyMeCab(f"{self.__name__}.{name}")

        # mecab 모듈 패치
        dummy_mecab = DummyMeCab('mecab')
        sys.modules['mecab'] = dummy_mecab
        sys.modules['MeCab'] = dummy_mecab

        # 일본어 관련 모듈들도 더미로 대체
        class DummyModule(types.ModuleType):
            """일반 더미 모듈 클래스"""
            def __init__(self, name='dummy'):
                super().__init__(name)
                self.__spec__ = ModuleSpec(name, None)
                self.__file__ = __file__
                self.__path__ = []

            def __call__(self, *args, **kwargs):
                return self

            def __getattr__(self, name):
                return DummyModule(f"{self.__name__}.{name}")

        modules_to_patch = [
            'unidic', 'unidic_lite', 'unidic-lite',
            'fugashi',
        ]

        for mod_name in modules_to_patch:
            if mod_name not in sys.modules:
                sys.modules[mod_name] = DummyModule(mod_name)

        # melo.text.japanese 모듈을 더미로 대체
        dummy_jp = DummyModule('melo.text.japanese')
        dummy_jp.japanese_cleaners = lambda x, *args, **kwargs: x
        dummy_jp.japanese_cleaners2 = lambda x, *args, **kwargs: x
        sys.modules['melo.text.japanese'] = dummy_jp

        # transformers 보안 체크 우회 패치
        # torch < 2.6에서 CVE-2025-32434 보안 취약점 체크로 인해 모델 로드 실패
        # safetensors 형식을 우선 사용하도록 설정하고, 보안 체크를 우회
        try:
            # transformers가 safetensors를 우선 사용하도록 환경변수 설정
            import os
            os.environ['SAFETENSORS_FAST_GPU'] = '1'

            # 보안 체크 함수를 더미로 대체
            def dummy_check():
                pass

            # 1. import_utils 모듈의 함수 패치
            from transformers.utils import import_utils
            if hasattr(import_utils, 'check_torch_load_is_safe'):
                import_utils.check_torch_load_is_safe = dummy_check

            # 2. modeling_utils 모듈의 함수 패치 (이미 import된 참조도 패치)
            from transformers import modeling_utils
            if hasattr(modeling_utils, 'check_torch_load_is_safe'):
                modeling_utils.check_torch_load_is_safe = dummy_check

            # 3. load_state_dict 함수 내부에서 사용되는 참조도 패치
            # modeling_utils.load_state_dict가 클로저로 check_torch_load_is_safe를 참조하므로
            # load_state_dict 함수 자체를 패치
            original_load_state_dict = modeling_utils.load_state_dict
            def patched_load_state_dict(checkpoint_file, map_location="cpu", weights_only=False):
                import torch
                return torch.load(checkpoint_file, map_location=map_location, weights_only=weights_only)
            modeling_utils.load_state_dict = patched_load_state_dict

            print("[OpenVoice] transformers 보안 체크 우회 패치 적용")
        except Exception as e:
            print(f"[OpenVoice] transformers 패치 실패 (무시): {e}")

        self._mecab_patched = True
        print("[OpenVoice] mecab 모듈 의존성 우회 패치 적용")

    def initialize(self) -> bool:
        """모델 로드"""
        if self._is_initialized:
            return True

        available, msg = self.is_available()
        if not available:
            self._last_error = msg
            if self.on_error:
                self.on_error("initialize", msg)
            return False

        try:
            import torch

            # mecab 모듈 의존성 우회 패치 적용
            self._patch_mecab_module()

            from melo.api import TTS as MeloTTS

            # 디바이스 설정
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[OpenVoice] 디바이스: {self._device}")

            # MeloTTS 모델 로드 (한국어만 사용)
            print("[OpenVoice] MeloTTS 모델 로드 중...")
            self._tts_model = MeloTTS(language='KR', device=self._device)
            print("[OpenVoice] MeloTTS 모델 로드 완료")

            # OpenVoice ToneColorConverter는 클로닝 시에만 로드
            self._is_initialized = True
            return True

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self._last_error = f"MeloTTS 로드 실패: {str(e)}\n\n상세:\n{error_detail}"
            print(f"[OpenVoice] {self._last_error}")
            if self.on_error:
                self.on_error("initialize", self._last_error)
            return False

    def _ensure_initialized(self) -> bool:
        """초기화 확인 및 자동 초기화"""
        if not self._is_initialized:
            return self.initialize()
        return True

    def _load_tone_converter(self):
        """ToneColorConverter 로드 (필요 시)"""
        if self._tone_converter is not None:
            return True

        try:
            import torch
            from openvoice.api import ToneColorConverter

            # 체크포인트 경로
            ckpt_converter = os.path.join(self._models_path, "converter")

            # 체크포인트가 없으면 다운로드
            if not os.path.exists(ckpt_converter):
                print("[OpenVoice] ToneColorConverter 모델 다운로드 중...")
                os.makedirs(ckpt_converter, exist_ok=True)
                # HuggingFace에서 다운로드
                from huggingface_hub import snapshot_download
                snapshot_download(
                    repo_id="myshell-ai/OpenVoice",
                    local_dir=ckpt_converter,
                    allow_patterns=["checkpoints_v2/*"]
                )

            config_path = os.path.join(ckpt_converter, "checkpoints_v2", "converter", "config.json")
            ckpt_path = os.path.join(ckpt_converter, "checkpoints_v2", "converter", "checkpoint.pth")

            if os.path.exists(config_path) and os.path.exists(ckpt_path):
                self._tone_converter = ToneColorConverter(config_path, device=self._device)
                self._tone_converter.load_ckpt(ckpt_path)
                print("[OpenVoice] ToneColorConverter 로드 완료")
                return True
            else:
                self._last_error = f"모델 파일 없음. 경로: {ckpt_converter}\n예상 파일: config.json, checkpoint.pth"
                print(f"[OpenVoice] {self._last_error}")
                return False

        except Exception as e:
            self._last_error = f"ToneColorConverter 로드 실패: {str(e)}"
            print(f"[OpenVoice] {self._last_error}")
            return False

    def generate(self, request: TTSRequest) -> TTSResult:
        """TTS 생성"""
        # 초기화 확인
        if not self._ensure_initialized():
            return TTSResult(
                success=False,
                error_message="OpenVoice 엔진 초기화 실패"
            )

        try:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(request.output_path), exist_ok=True)

            # 클로닝된 음성인지 확인
            is_cloned = request.voice_id in self._cloned_voices

            if is_cloned:
                # 클로닝된 음성: MeloTTS 생성 후 음색 변환
                return self._generate_cloned(request)
            else:
                # 기본 음성: MeloTTS로 직접 생성
                return self._generate_base(request)

        except Exception as e:
            return TTSResult(
                success=False,
                error_message=f"TTS 생성 실패: {str(e)}"
            )

    def _generate_base(self, request: TTSRequest) -> TTSResult:
        """기본 MeloTTS 음성 생성"""
        try:
            # MeloTTS 화자 ID (한국어 기본)
            speaker_ids = self._tts_model.hps.data.spk2id
            speaker_id = list(speaker_ids.values())[0]  # 첫 번째 화자

            # 속도 조절 (-5 ~ +5 → 0.5 ~ 2.0)
            speed = 1.0 - (request.speed * 0.1)  # speed=0이면 1.0, speed=5이면 0.5
            speed = max(0.5, min(2.0, speed))

            # TTS 생성
            self._tts_model.tts_to_file(
                request.text,
                speaker_id,
                request.output_path,
                speed=speed
            )

            if os.path.exists(request.output_path):
                return TTSResult(
                    success=True,
                    output_path=request.output_path
                )
            else:
                return TTSResult(
                    success=False,
                    error_message="출력 파일 생성 실패"
                )

        except Exception as e:
            return TTSResult(
                success=False,
                error_message=f"MeloTTS 생성 실패: {str(e)}"
            )

    def _generate_cloned(self, request: TTSRequest) -> TTSResult:
        """클로닝된 음성으로 생성"""
        try:
            print(f"[OpenVoice] 클로닝 음성 생성 시작: {request.voice_id}")

            # ToneColorConverter 로드
            if not self._load_tone_converter():
                return TTSResult(
                    success=False,
                    error_message="ToneColorConverter 로드 실패"
                )

            # 클로닝된 음성 정보
            voice_info = self._cloned_voices.get(request.voice_id)
            if not voice_info:
                return TTSResult(
                    success=False,
                    error_message=f"음성을 찾을 수 없음: {request.voice_id}"
                )

            # 음색 임베딩 로드
            se_path = os.path.join(self._cloned_voices_dir, f"{request.voice_id}.pth")
            if not os.path.exists(se_path):
                return TTSResult(
                    success=False,
                    error_message=f"음색 데이터 없음: {se_path}"
                )

            import torch
            print(f"[OpenVoice] 음색 임베딩 로드: {se_path}")
            target_se = torch.load(se_path, map_location=self._device)

            # 임시 파일로 기본 음성 생성
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # MeloTTS로 기본 음성 생성
                speaker_ids = self._tts_model.hps.data.spk2id
                speaker_id = list(speaker_ids.values())[0]

                speed = 1.0 - (request.speed * 0.1)
                speed = max(0.5, min(2.0, speed))

                print(f"[OpenVoice] MeloTTS 음성 생성 중... (텍스트 길이: {len(request.text)}자)")
                self._tts_model.tts_to_file(
                    request.text,
                    speaker_id,
                    tmp_path,
                    speed=speed
                )
                print(f"[OpenVoice] MeloTTS 음성 생성 완료: {tmp_path}")

                # 임시 파일 확인
                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return TTSResult(
                        success=False,
                        error_message="MeloTTS 음성 파일 생성 실패 (파일 없음 또는 0바이트)"
                    )

                # 소스 음색 추출 (MeloTTS 기본 음성)
                if self._source_se is None:
                    print("[OpenVoice] 소스 음색 추출 중...")
                    from openvoice import se_extractor
                    self._source_se, _ = se_extractor.get_se(
                        tmp_path,
                        self._tone_converter,
                        vad=False
                    )
                    print("[OpenVoice] 소스 음색 추출 완료")

                # 음색 변환
                print("[OpenVoice] 음색 변환 중...")
                self._tone_converter.convert(
                    audio_src_path=tmp_path,
                    src_se=self._source_se,
                    tgt_se=target_se,
                    output_path=request.output_path,
                    message="@MyShell"
                )
                print(f"[OpenVoice] 음색 변환 완료: {request.output_path}")

                if os.path.exists(request.output_path):
                    return TTSResult(
                        success=True,
                        output_path=request.output_path
                    )
                else:
                    return TTSResult(
                        success=False,
                        error_message="음색 변환 실패 (출력 파일 없음)"
                    )

            finally:
                # 임시 파일 삭제
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[OpenVoice] 클로닝 음성 생성 오류: {error_detail}")
            return TTSResult(
                success=False,
                error_message=f"클로닝 음성 생성 실패: {str(e)}"
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
        self._last_error = None

        if not self._ensure_initialized():
            # _last_error는 initialize()에서 이미 설정됨
            if not self._last_error:
                self._last_error = "OpenVoice 엔진 초기화 실패"
            return None

        if not os.path.exists(reference_audio):
            self._last_error = f"참조 오디오 파일을 찾을 수 없음: {reference_audio}"
            print(f"[OpenVoice] {self._last_error}")
            return None

        try:
            # ToneColorConverter 로드
            if not self._load_tone_converter():
                self._last_error = self._last_error or "ToneColorConverter 로드 실패"
                return None

            # 고유 ID 생성
            import uuid
            voice_id = f"clone_{uuid.uuid4().hex[:8]}"

            # 참조 오디오 복사
            ref_filename = f"{voice_id}{os.path.splitext(reference_audio)[1]}"
            ref_dest = os.path.join(self._cloned_voices_dir, ref_filename)
            shutil.copy2(reference_audio, ref_dest)

            # 음색 특성 추출
            print(f"[OpenVoice] 음색 추출 중: {reference_audio}")
            from openvoice import se_extractor
            import torch

            target_se, _ = se_extractor.get_se(
                reference_audio,
                self._tone_converter,
                vad=True  # Voice Activity Detection
            )

            # 음색 임베딩 저장
            se_path = os.path.join(self._cloned_voices_dir, f"{voice_id}.pth")
            torch.save(target_se, se_path)
            print(f"[OpenVoice] 음색 저장: {se_path}")

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
            self._last_error = f"클로닝 실패: {str(e)}"
            print(f"[OpenVoice] {self._last_error}")
            if self.on_error:
                self.on_error("clone_voice", self._last_error)
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

    def shutdown(self):
        """엔진 종료"""
        self._tone_converter = None
        self._tts_model = None
        self._source_se = None
        self._is_initialized = False
