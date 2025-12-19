# core/tts_engine.py
# CLOVA Voice TTS 엔진

import ssl
import os
import time
import urllib.request
import urllib.parse
from typing import Optional, Callable
from dataclasses import dataclass

# SSL 인증서 우회 (macOS 호환성)
ssl._create_default_https_context = ssl._create_unverified_context


@dataclass
class TTSOptions:
    """TTS 옵션"""
    speaker: str = "vdain"
    speed: int = 0      # -5 ~ +5
    pitch: int = 0      # -5 ~ +5
    volume: int = 0     # -5 ~ +5
    emotion: int = 0    # 0: 중립, 1: 슬픔, 2: 기쁨
    emotion_strength: int = 1  # 0 ~ 2
    format: str = "wav"


class TTSEngine:
    """CLOVA Voice TTS 엔진"""
    
    API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
    
    def __init__(self, client_id: str = "", client_secret: str = ""):
        self.client_id = client_id
        self.client_secret = client_secret
        self.options = TTSOptions()
        self.api_delay = 0.3  # API 호출 간 대기 시간
        
        # 콜백 함수들
        self.on_progress: Optional[Callable[[int, int, str], None]] = None
        self.on_complete: Optional[Callable[[bool, str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        
        # 상태
        self._cancel_requested = False
        self._is_running = False
    
    def set_credentials(self, client_id: str, client_secret: str):
        """API 인증 정보 설정"""
        self.client_id = client_id
        self.client_secret = client_secret
    
    def set_options(self, options: TTSOptions):
        """TTS 옵션 설정"""
        self.options = options
    
    def generate_single(self, text: str, output_path: str) -> bool:
        """단일 텍스트 TTS 생성"""
        if not self.client_id or not self.client_secret:
            if self.on_error:
                self.on_error("API 키가 설정되지 않았습니다.", output_path)
            return False
        
        # 요청 데이터 구성
        enc_text = urllib.parse.quote(text)
        
        params = [
            f"speaker={self.options.speaker}",
            f"text={enc_text}",
            f"volume={self.options.volume}",
            f"speed={self.options.speed}",
            f"pitch={self.options.pitch}",
            f"format={self.options.format}"
        ]
        
        # 감정 설정 (지원 음성만)
        if self.options.emotion > 0:
            params.append(f"emotion={self.options.emotion}")
            params.append(f"emotion-strength={self.options.emotion_strength}")
        
        data = "&".join(params)
        
        # API 요청
        request = urllib.request.Request(self.API_URL)
        request.add_header("X-NCP-APIGW-API-KEY-ID", self.client_id)
        request.add_header("X-NCP-APIGW-API-KEY", self.client_secret)
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        try:
            response = urllib.request.urlopen(
                request, 
                data=data.encode('utf-8'), 
                timeout=30
            )
            
            if response.getcode() == 200:
                # 출력 디렉토리 생성
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.read())
                return True
            else:
                if self.on_error:
                    self.on_error(f"HTTP {response.getcode()}", output_path)
                return False
                
        except urllib.error.HTTPError as e:
            if self.on_error:
                self.on_error(f"HTTP 오류: {e.code} - {e.reason}", output_path)
            return False
        except Exception as e:
            if self.on_error:
                self.on_error(f"오류: {str(e)}", output_path)
            return False
    
    def generate_batch(self, items: list, output_folder: str, 
                       filename_generator: Callable) -> dict:
        """배치 TTS 생성
        
        Args:
            items: SRTEntry 리스트
            output_folder: 출력 폴더
            filename_generator: 파일명 생성 함수 (entry -> filename)
        
        Returns:
            결과 딕셔너리 {'success': int, 'failed': int, 'cancelled': bool}
        """
        self._cancel_requested = False
        self._is_running = True
        
        results = {
            'success': 0,
            'failed': 0,
            'cancelled': False,
            'files': []
        }
        
        total = len(items)
        
        for i, entry in enumerate(items):
            # 취소 확인
            if self._cancel_requested:
                results['cancelled'] = True
                break
            
            filename = filename_generator(entry)
            output_path = os.path.join(output_folder, filename)
            
            # 이미 존재하는 파일 건너뛰기
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                results['success'] += 1
                results['files'].append(output_path)
                if self.on_progress:
                    self.on_progress(i + 1, total, f"기존 파일: {filename}")
                continue
            
            # 진행 상황 콜백
            if self.on_progress:
                self.on_progress(i + 1, total, f"생성 중: {filename}")
            
            # TTS 생성
            if self.generate_single(entry.text, output_path):
                results['success'] += 1
                results['files'].append(output_path)
            else:
                results['failed'] += 1
            
            # API 호출 간 대기
            if i < total - 1:
                time.sleep(self.api_delay)
        
        self._is_running = False
        
        # 완료 콜백
        if self.on_complete:
            success = not results['cancelled'] and results['failed'] == 0
            message = f"완료: {results['success']}/{total} 성공"
            if results['cancelled']:
                message = "취소됨"
            self.on_complete(success, message)
        
        return results
    
    def cancel(self):
        """작업 취소 요청"""
        self._cancel_requested = True
    
    @property
    def is_running(self) -> bool:
        """실행 중 여부"""
        return self._is_running
    
    def test_connection(self) -> tuple:
        """API 연결 테스트
        
        Returns:
            (success: bool, message: str)
        """
        if not self.client_id or not self.client_secret:
            return False, "API 키가 설정되지 않았습니다."
        
        # 짧은 테스트 문장
        test_text = "테스트"
        enc_text = urllib.parse.quote(test_text)
        data = f"speaker=nara&text={enc_text}&volume=0&speed=0&pitch=0&format=wav"
        
        request = urllib.request.Request(self.API_URL)
        request.add_header("X-NCP-APIGW-API-KEY-ID", self.client_id)
        request.add_header("X-NCP-APIGW-API-KEY", self.client_secret)
        request.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        try:
            response = urllib.request.urlopen(
                request,
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
