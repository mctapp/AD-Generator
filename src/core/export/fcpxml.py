# core/export/fcpxml.py
# FCPXML 파일 생성 (DaVinci Resolve 호환)

import os
from typing import List
from ...utils.audio import get_wav_duration_ms, get_wav_sample_rate
from ...utils.timecode import ms_to_filename_tc, ms_to_frames


class FCPXMLExporter:
    """FCPXML 파일 생성기"""
    
    def __init__(self, fps: float = 24):
        self.fps = fps
    
    def export(self, entries: list, wav_folder: str, output_path: str) -> bool:
        """FCPXML 파일 생성
        
        Args:
            entries: SRTEntry 리스트
            wav_folder: WAV 파일 폴더
            output_path: 출력 파일 경로
        
        Returns:
            성공 여부
        """
        wav_folder_abs = os.path.abspath(wav_folder)
        
        # 클립 데이터 수집
        clips_data = []
        max_end_frame = 0
        
        for entry in entries:
            tc_filename = ms_to_filename_tc(entry.start_ms, self.fps)
            wav_path = os.path.join(wav_folder, f"{tc_filename}.wav")
            wav_path_abs = os.path.join(wav_folder_abs, f"{tc_filename}.wav")
            
            if os.path.exists(wav_path):
                duration_ms = get_wav_duration_ms(wav_path)
                duration_frames = ms_to_frames(duration_ms, self.fps)
                start_frames = ms_to_frames(entry.start_ms, self.fps)
                end_frames = start_frames + duration_frames
                sample_rate = get_wav_sample_rate(wav_path)
                
                if end_frames > max_end_frame:
                    max_end_frame = end_frames
                
                clips_data.append({
                    'filename': f"{tc_filename}.wav",
                    'filepath': wav_path_abs,
                    'start_frames': start_frames,
                    'duration_frames': duration_frames,
                    'duration_ms': duration_ms,
                    'sample_rate': sample_rate
                })
        
        if not clips_data:
            return False
        
        # 타임라인 길이 (여유 있게)
        timeline_duration = max_end_frame + int(self.fps * 10)
        fps_int = int(self.fps)
        
        # FCPXML 생성
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
    <resources>
        <format id="r1" name="FFVideoFormat1080p{fps_int}" frameDuration="1/{fps_int}s" width="1920" height="1080"/>
'''
        
        # 오디오 리소스 추가
        for i, clip in enumerate(clips_data):
            audio_samples = int(clip['duration_ms'] * clip['sample_rate'] / 1000)
            filepath_escaped = clip['filepath'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_content += f'''        <asset id="r{i+2}" name="{clip['filename']}" src="file://{filepath_escaped}" start="0s" duration="{audio_samples}/{clip['sample_rate']}s" hasAudio="1" audioSources="1" audioChannels="1" audioRate="{clip['sample_rate']}"/>
'''
        
        xml_content += f'''    </resources>
    <library>
        <event name="AD_TTS_Import">
            <project name="AD_Timeline">
                <sequence format="r1" duration="{timeline_duration}/{fps_int}s" tcStart="0/{fps_int}s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
                        <gap name="Gap" offset="0/{fps_int}s" duration="{timeline_duration}/{fps_int}s" start="0/{fps_int}s">
'''
        
        # 오디오 클립 배치
        for i, clip in enumerate(clips_data):
            audio_samples = int(clip['duration_ms'] * clip['sample_rate'] / 1000)
            xml_content += f'''                            <audio name="{clip['filename']}" ref="r{i+2}" lane="1" offset="{clip['start_frames']}/{fps_int}s" duration="{audio_samples}/{clip['sample_rate']}s" start="0s"/>
'''
        
        xml_content += '''                        </gap>
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>
'''
        
        # 파일 저장
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            return True
        except Exception:
            return False
