# core/export/edl.py
# EDL 파일 생성 (CMX 3600 호환)

import os
from typing import List
from ...utils.audio import get_wav_duration_ms
from ...utils.timecode import ms_to_filename_tc, ms_to_timecode


class EDLExporter:
    """EDL 파일 생성기"""
    
    def __init__(self, fps: float = 24):
        self.fps = fps
    
    def export(self, entries: list, wav_folder: str, output_path: str) -> bool:
        """EDL 파일 생성
        
        Args:
            entries: SRTEntry 리스트
            wav_folder: WAV 파일 폴더
            output_path: 출력 파일 경로
        
        Returns:
            성공 여부
        """
        wav_folder_abs = os.path.abspath(wav_folder)
        
        try:
            with open(output_path, 'w') as f:
                f.write("TITLE: AD_TTS_IMPORT\n")
                f.write("FCM: NON-DROP FRAME\n\n")
                
                edit_num = 1
                for entry in entries:
                    tc_filename = ms_to_filename_tc(entry.start_ms, self.fps)
                    wav_path = os.path.join(wav_folder, f"{tc_filename}.wav")
                    wav_path_abs = os.path.join(wav_folder_abs, f"{tc_filename}.wav")
                    
                    if os.path.exists(wav_path):
                        tts_duration = get_wav_duration_ms(wav_path)
                        
                        tc_in = ms_to_timecode(entry.start_ms, self.fps)
                        tc_out = ms_to_timecode(entry.start_ms + tts_duration, self.fps)
                        src_out = ms_to_timecode(tts_duration, self.fps)
                        
                        # 릴 이름 (8자 제한)
                        reel_name = f"AD{edit_num:04d}"
                        
                        # EDL 라인
                        f.write(f"{edit_num:03d}  {reel_name}  AA     C        ")
                        f.write(f"00:00:00:00 {src_out} {tc_in} {tc_out}\n")
                        
                        # 클립 정보 주석
                        f.write(f"* FROM CLIP NAME: {tc_filename}.wav\n")
                        f.write(f"* SOURCE FILE: {wav_path_abs}\n")
                        f.write(f"* AUDIO LEVEL AT 00:00:00:00 IS 0.00 DB\n")
                        f.write("\n")
                        
                        edit_num += 1
            
            return True
        except Exception:
            return False
