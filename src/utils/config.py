# utils/config.py
# 앱 설정 관리

import json
import os
from pathlib import Path


class Config:
    """앱 설정을 관리하는 클래스"""
    
    DEFAULT_CONFIG = {
        'api': {
            'client_id': '',
            'client_secret': ''
        },
        'voice': {
            'speaker': 'vdain',
            'speed': 0,
            'pitch': 0,
            'volume': 0,
            'emotion': 0,
            'emotion_strength': 1
        },
        'output': {
            'format': 'fcpxml',  # 'fcpxml' or 'edl'
            'frame_rate': 24,
            'last_output_folder': ''
        },
        'app': {
            'last_srt_folder': '',
            'api_delay': 0.3,
            'window_geometry': None
        }
    }
    
    def __init__(self):
        self.config_dir = Path.home() / '.tomato_ad'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load()
    
    def load(self) -> dict:
        """설정 파일 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # 기본값과 병합
                    return self._merge_config(self.DEFAULT_CONFIG.copy(), loaded)
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """설정 파일 저장"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def _merge_config(self, default: dict, loaded: dict) -> dict:
        """기본 설정과 로드된 설정 병합"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_config(result[key], value)
                else:
                    result[key] = value
        return result
    
    def get(self, *keys):
        """설정값 조회 (예: config.get('api', 'client_id'))"""
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def set(self, *args):
        """설정값 저장 (예: config.set('api', 'client_id', 'value'))"""
        if len(args) < 2:
            return
        
        keys = args[:-1]
        value = args[-1]
        
        target = self.config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
        self.save()
    
    @property
    def client_id(self) -> str:
        return self.get('api', 'client_id') or ''
    
    @client_id.setter
    def client_id(self, value: str):
        self.set('api', 'client_id', value)
    
    @property
    def client_secret(self) -> str:
        return self.get('api', 'client_secret') or ''
    
    @client_secret.setter
    def client_secret(self, value: str):
        self.set('api', 'client_secret', value)
    
    @property
    def voice_settings(self) -> dict:
        return self.get('voice') or self.DEFAULT_CONFIG['voice']
    
    @voice_settings.setter
    def voice_settings(self, value: dict):
        self.config['voice'] = value
        self.save()
    
    def has_api_keys(self) -> bool:
        """API 키가 설정되어 있는지 확인"""
        return bool(self.client_id and self.client_secret)


# 전역 설정 인스턴스
config = Config()
