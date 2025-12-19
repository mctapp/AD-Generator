# ui/main_window.py
# 메인 윈도우 (개선된 UI)

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, 
    QTabWidget, QStatusBar, QFrame, QMessageBox,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .styles import MAIN_STYLE, COLORS, FONTS, RADIUS, get_button_style
from .widgets import VoicePanel, CollapsibleSection
from .tabs import SRTBatchTab, SingleClipTab, ScriptConverterTab, SRTSyncTab
from .settings_dialog import SettingsDialog
from ..utils import config


class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.output_folder = None
        self.setup_ui()
        self.load_config()
        self.connect_signals()
    
    def setup_ui(self):
        self.setWindowTitle("TOMATO AD Voice Generator")
        self.setMinimumSize(1000, 900)
        
        # 메인 스타일 적용
        self.setStyleSheet(MAIN_STYLE)
        
        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # === 헤더 ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        # 로고 & 타이틀
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 토마토 로고 (텍스트)
        logo = QLabel("TOMATO")
        logo.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 800;
            color: {COLORS['tomato']};
            letter-spacing: -1px;
        """)
        title_layout.addWidget(logo)
        
        logo_ad = QLabel("AD")
        logo_ad.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 800;
            color: {COLORS['text_primary']};
            letter-spacing: -1px;
        """)
        title_layout.addWidget(logo_ad)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # 통합실행 버튼
        self.btn_integrated = QPushButton("통합실행")
        self.btn_integrated.setStyleSheet(get_button_style('primary', 'lg'))
        self.btn_integrated.setFixedWidth(120)
        self.btn_integrated.clicked.connect(self.run_integrated_workflow)
        header_layout.addWidget(self.btn_integrated)
        
        # 다빈치리졸브로 내보내기 버튼
        self.btn_resolve = QPushButton("다빈치리졸브로 내보내기")
        self.btn_resolve.setStyleSheet(get_button_style('secondary', 'lg'))
        self.btn_resolve.clicked.connect(self.export_to_resolve)
        header_layout.addWidget(self.btn_resolve)
        
        # 설정 버튼
        self.btn_settings = QPushButton("설정")
        self.btn_settings.setStyleSheet(get_button_style('secondary'))
        self.btn_settings.setFixedWidth(70)
        self.btn_settings.clicked.connect(self.open_settings)
        header_layout.addWidget(self.btn_settings)
        
        layout.addLayout(header_layout)
        
        # === 탭 위젯 ===
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {COLORS['bg_primary']};
                border: none;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 12px 24px;
                min-width: 90px;
                font-size: {FONTS['size_base']};
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_secondary']};
            }}
            QTabBar::tab:selected {{
                color: {COLORS['accent_yellow']};
                border-bottom: 2px solid {COLORS['accent_yellow']};
            }}
        """)
        
        # Tab 1: 대본 변환
        self.script_tab = ScriptConverterTab()
        self.tab_widget.addTab(self.script_tab, "대본 → SRT")
        
        # Tab 2: SRT 일괄 생성
        self.srt_batch_tab = SRTBatchTab()
        self.tab_widget.addTab(self.srt_batch_tab, "SRT → TTS")
        
        # Tab 3: 단일 클립 생성
        self.single_clip_tab = SingleClipTab()
        self.tab_widget.addTab(self.single_clip_tab, "단일 클립")
        
        # Tab 4: SRT 동기화
        self.sync_tab = SRTSyncTab()
        self.tab_widget.addTab(self.sync_tab, "SRT 동기화")
        
        layout.addWidget(self.tab_widget, 1)
        
        # === 음성 설정 (접힘/펼침) ===
        self.voice_section = CollapsibleSection("음성 설정", expanded=False)
        
        voice_content = QWidget()
        voice_layout = QVBoxLayout(voice_content)
        voice_layout.setContentsMargins(0, 0, 0, 0)
        voice_layout.setSpacing(12)
        
        # 음성 패널
        self.voice_panel = VoicePanel()
        self.voice_panel.preview_requested.connect(self.on_preview_requested)
        self.voice_panel.settings_changed.connect(self.on_voice_settings_changed)
        voice_layout.addWidget(self.voice_panel)
        
        self.voice_section.set_content(voice_content)
        layout.addWidget(self.voice_section)
        
        # === 출력 설정 ===
        output_frame = QFrame()
        output_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_default']};
                border-radius: {RADIUS['lg']};
                padding: 12px;
            }}
        """)
        output_layout = QHBoxLayout(output_frame)
        output_layout.setContentsMargins(16, 10, 16, 10)
        output_layout.setSpacing(16)
        
        # 출력 폴더
        folder_label = QLabel("출력 폴더")
        folder_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 500;")
        output_layout.addWidget(folder_label)
        
        self.label_output = QLabel("선택되지 않음")
        self.label_output.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            background-color: {COLORS['bg_tertiary']};
            border: 1px solid {COLORS['border_default']};
            border-radius: {RADIUS['md']};
            padding: 8px 12px;
            min-width: 250px;
        """)
        output_layout.addWidget(self.label_output, 1)
        
        self.btn_output = QPushButton("선택")
        self.btn_output.setStyleSheet(get_button_style('primary'))
        self.btn_output.setFixedWidth(70)
        self.btn_output.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.btn_output)
        
        # 구분자
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet(f"background-color: {COLORS['border_default']};")
        sep1.setFixedWidth(1)
        output_layout.addWidget(sep1)
        
        # 출력 형식
        format_label = QLabel("형식")
        format_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        output_layout.addWidget(format_label)
        
        self.combo_format = QComboBox()
        self.combo_format.addItem("FCPXML", "fcpxml")
        self.combo_format.addItem("EDL", "edl")
        self.combo_format.setFixedWidth(100)
        self.combo_format.currentIndexChanged.connect(self.on_format_changed)
        output_layout.addWidget(self.combo_format)
        
        # FPS
        fps_label = QLabel("FPS")
        fps_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        output_layout.addWidget(fps_label)
        
        self.combo_fps = QComboBox()
        self.combo_fps.addItem("24", 24)
        self.combo_fps.addItem("23.976", 23.976)
        self.combo_fps.addItem("25", 25)
        self.combo_fps.addItem("30", 30)
        self.combo_fps.setFixedWidth(90)
        self.combo_fps.currentIndexChanged.connect(self.on_fps_changed)
        output_layout.addWidget(self.combo_fps)
        
        layout.addWidget(output_frame)
        
        # === 상태바 ===
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_muted']};
                border-top: 1px solid {COLORS['border_default']};
                padding: 4px 8px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")
    
    def connect_signals(self):
        """시그널 연결"""
        # 대본 탭 → SRT 탭 연결
        self.script_tab.srt_ready.connect(self.on_srt_from_script)
        
        # TTS 생성 완료 → SRT 동기화 연결
        self.srt_batch_tab.generation_complete.connect(self.on_tts_complete)
        
        # 상태 메시지
        self.script_tab.status_message.connect(self.show_status)
        self.srt_batch_tab.status_message.connect(self.show_status)
        self.single_clip_tab.status_message.connect(self.show_status)
        self.sync_tab.status_message.connect(self.show_status)
    
    def load_config(self):
        """설정 로드"""
        # 음성 설정
        voice_settings = config.voice_settings
        self.voice_panel.set_settings(voice_settings)
        
        # 출력 설정
        output_format = config.get('output', 'format') or 'fcpxml'
        index = self.combo_format.findData(output_format)
        if index >= 0:
            self.combo_format.setCurrentIndex(index)
        
        fps = config.get('output', 'frame_rate') or 24
        index = self.combo_fps.findData(fps)
        if index >= 0:
            self.combo_fps.setCurrentIndex(index)
        
        # 마지막 출력 폴더
        last_folder = config.get('output', 'last_output_folder')
        if last_folder and os.path.exists(last_folder):
            self.output_folder = last_folder
            folder_name = os.path.basename(last_folder)
            self.label_output.setText(folder_name)
            self.label_output.setToolTip(last_folder)
            self.label_output.setStyleSheet(f"""
                color: {COLORS['accent_success']};
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['accent_success']};
                border-radius: {RADIUS['md']};
                padding: 8px 12px;
                min-width: 250px;
            """)
        
        # 탭에 설정 전달
        self.sync_settings_to_tabs()
    
    def sync_settings_to_tabs(self):
        """탭에 설정 동기화"""
        fps = self.combo_fps.currentData()
        fmt = self.combo_format.currentData()
        voice_settings = self.voice_panel.get_settings()
        
        # 각 탭에 설정 전달
        self.script_tab.set_fps(fps)
        
        self.srt_batch_tab.set_fps(fps)
        self.srt_batch_tab.set_output_format(fmt)
        self.srt_batch_tab.set_voice_settings(voice_settings)
        
        self.single_clip_tab.set_fps(fps)
        self.single_clip_tab.set_voice_settings(voice_settings)
        
        self.sync_tab.set_fps(fps)
        
        if self.output_folder:
            self.script_tab.set_output_folder(self.output_folder)
            self.srt_batch_tab.set_output_folder(self.output_folder)
            self.single_clip_tab.set_output_folder(self.output_folder)
            self.sync_tab.set_wav_folder(self.output_folder)
    
    def select_output_folder(self):
        """출력 폴더 선택"""
        folder = QFileDialog.getExistingDirectory(self, "출력 폴더 선택")
        if folder:
            self.output_folder = folder
            folder_name = os.path.basename(folder)
            self.label_output.setText(folder_name)
            self.label_output.setToolTip(folder)
            self.label_output.setStyleSheet(f"""
                color: {COLORS['accent_success']};
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['accent_success']};
                border-radius: {RADIUS['md']};
                padding: 8px 12px;
                min-width: 250px;
            """)
            config.set('output', 'last_output_folder', folder)
            
            # 탭에 전달
            self.script_tab.set_output_folder(folder)
            self.srt_batch_tab.set_output_folder(folder)
            self.single_clip_tab.set_output_folder(folder)
            self.sync_tab.set_wav_folder(folder)
            
            self.show_status(f"출력 폴더: {folder}")
    
    def on_fps_changed(self):
        """FPS 변경"""
        fps = self.combo_fps.currentData()
        self.script_tab.set_fps(fps)
        self.srt_batch_tab.set_fps(fps)
        self.single_clip_tab.set_fps(fps)
        self.sync_tab.set_fps(fps)
    
    def on_format_changed(self):
        """출력 형식 변경"""
        fmt = self.combo_format.currentData()
        self.srt_batch_tab.set_output_format(fmt)
    
    def on_voice_settings_changed(self, settings):
        """음성 설정 변경"""
        self.srt_batch_tab.set_voice_settings(settings)
        self.single_clip_tab.set_voice_settings(settings)
    
    def on_srt_from_script(self, srt_path):
        """대본 탭에서 SRT 전달받음"""
        # SRT 일괄 생성 탭으로 이동
        self.tab_widget.setCurrentIndex(1)
        
        # SRT 파일 로드
        self.srt_batch_tab.on_file_dropped(srt_path)
        
        # SRT 동기화 탭에도 미리 로드
        self.sync_tab.load_srt(srt_path)
    
    def on_preview_requested(self):
        """미리듣기"""
        import subprocess
        import tempfile
        from PyQt6.QtWidgets import QApplication
        from ..core import TTSEngine, TTSOptions
        
        if not config.has_api_keys():
            QMessageBox.warning(self, "경고", "설정에서 API 키를 먼저 입력하세요.")
            return
        
        # 현재 탭에 따라 텍스트 결정
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 1:  # SRT 탭
            entry = self.srt_batch_tab.srt_table.get_selected_entry()
            text = entry.text if entry else "안녕하세요, 테스트 음성입니다."
        elif current_tab == 2:  # 단일 클립 탭
            text = self.single_clip_tab.text_edit.toPlainText().strip()
            if not text:
                text = "안녕하세요, 테스트 음성입니다."
        else:
            text = "안녕하세요, 테스트 음성입니다."
        
        settings = self.voice_panel.get_settings()
        options = TTSOptions(**settings)
        
        engine = TTSEngine(config.client_id, config.client_secret)
        engine.set_options(options)
        
        temp_file = os.path.join(tempfile.gettempdir(), 'tomato_preview.wav')
        
        self.show_status("미리듣기 생성 중...")
        QApplication.processEvents()
        
        if engine.generate_single(text, temp_file):
            subprocess.run(['afplay', temp_file], check=False)
            self.show_status("미리듣기 완료")
        else:
            QMessageBox.warning(self, "오류", "미리듣기 생성에 실패했습니다.")
            self.show_status("미리듣기 실패")
    
    def run_integrated_workflow(self):
        """통합실행 - 대본→TTS→동기화 원클릭"""
        try:
            if not self.output_folder:
                QMessageBox.warning(self, "경고", "먼저 출력 폴더를 선택하세요.")
                return
            
            if not config.has_api_keys():
                QMessageBox.warning(self, "경고", "설정에서 API 키를 먼저 입력하세요.")
                return
            
            # 대본 탭에 PDF가 로드되어 있는지 확인
            if not self.script_tab.current_pdf:
                QMessageBox.warning(self, "경고", "먼저 대본 PDF 파일을 선택하세요.")
                self.tab_widget.setCurrentIndex(0)
                return
            
            # === Step 1: 대본 분석 ===
            self.show_status("통합실행: 대본 분석 중...")
            self.tab_widget.setCurrentIndex(0)
            QApplication.processEvents()
            
            # 대본 분석 실행
            self.script_tab.parse_script()
            QApplication.processEvents()
            
            if not self.script_tab.entries:
                QMessageBox.warning(self, "경고", "대본 분석에 실패했습니다.")
                return
            
            # 자동 저장된 SRT 경로 확인
            srt_path = self.script_tab.get_last_saved_srt()
            if not srt_path or not os.path.exists(srt_path):
                QMessageBox.warning(self, "경고", "SRT 파일이 자동 저장되지 않았습니다.\n출력 폴더를 확인하세요.")
                return
            
            self.show_status(f"통합실행: 대본 분석 완료 - {len(self.script_tab.entries)}개 항목")
            
            # === Step 2: TTS 탭으로 이동 ===
            self.tab_widget.setCurrentIndex(1)
            QApplication.processEvents()
            
            # SRT 파일 로드
            self.srt_batch_tab.on_file_dropped(srt_path)
            QApplication.processEvents()
            
            # TTS 생성 시작 여부 확인
            reply = QMessageBox.question(
                self, "통합실행",
                f"대본 분석 완료: {len(self.script_tab.entries)}개 항목\n"
                f"SRT 저장: {os.path.basename(srt_path)}\n\n"
                "TTS 음성 생성을 시작하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.show_status("통합실행: TTS 생성 시작...")
                # TTS 생성 시작
                self.srt_batch_tab.start_generation()
            else:
                self.show_status("통합실행: TTS 생성 건너뜀")
                # 동기화 탭으로 이동
                self._move_to_sync_tab(srt_path)
        
        except Exception as e:
            QMessageBox.critical(self, "오류", f"통합실행 중 오류 발생:\n{str(e)}")
            self.show_status("통합실행 오류")
    
    def _move_to_sync_tab(self, srt_path: str):
        """SRT 동기화 탭으로 이동"""
        self.tab_widget.setCurrentIndex(3)
        self.sync_tab.load_srt(srt_path)
        
        # WAV 폴더 자동 설정
        wav_folder = os.path.join(self.output_folder, 'wav')
        if os.path.exists(wav_folder):
            self.sync_tab._set_wav_folder(wav_folder)
        
        self.show_status("통합실행: SRT 동기화 탭으로 이동 - '분석' 버튼을 클릭하세요")
    
    def on_tts_complete(self, srt_path: str):
        """TTS 생성 완료 후 자동으로 SRT 동기화 진행"""
        reply = QMessageBox.question(
            self, "TTS 생성 완료",
            "TTS 음성 생성이 완료되었습니다.\n\n"
            "SRT 동기화를 자동으로 진행하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._move_to_sync_tab(srt_path)
            QApplication.processEvents()
            
            # 자동 분석 실행
            if self.sync_tab.srt_path and self.sync_tab.wav_folder:
                self.show_status("통합실행: SRT 동기화 분석 중...")
                self.sync_tab.analyze()
                self.show_status("통합실행 완료!")
    
    def export_to_resolve(self):
        """다빈치리졸브로 내보내기"""
        if not self.output_folder:
            QMessageBox.warning(self, "경고", "먼저 출력 폴더를 선택하세요.")
            return
        
        # 출력 파일 확인
        wav_folder = os.path.join(self.output_folder, 'wav')
        fcpxml_path = os.path.join(self.output_folder, 'ad_import.fcpxml')
        
        # WAV 파일 존재 확인
        if not os.path.exists(wav_folder):
            QMessageBox.warning(self, "경고", "WAV 폴더가 없습니다.\n먼저 TTS 생성을 실행하세요.")
            return
        
        wav_files = [f for f in os.listdir(wav_folder) if f.endswith('.wav')]
        if not wav_files:
            QMessageBox.warning(self, "경고", "WAV 파일이 없습니다.\n먼저 TTS 생성을 실행하세요.")
            return
        
        # 영상 파일 찾기
        video_file = self._find_video_file()
        
        # _synced.srt 파일 찾기
        srt_file = self._find_synced_srt()
        
        # DaVinci Resolve API 시도
        resolve = self._get_resolve()
        
        if resolve:
            # API를 통한 직접 임포트
            self._import_to_resolve_full(resolve, wav_folder, wav_files, video_file, srt_file, fcpxml_path)
        else:
            # 수동 임포트 안내
            self._show_manual_import_guide(wav_folder, fcpxml_path, video_file, srt_file)
    
    def _find_video_file(self):
        """출력 폴더에서 영상 파일 찾기"""
        video_extensions = ['.mp4', '.mov', '.mxf', '.avi']
        
        # 출력 폴더에서 찾기
        for f in os.listdir(self.output_folder):
            for ext in video_extensions:
                if f.lower().endswith(ext):
                    return os.path.join(self.output_folder, f)
        
        # 상위 폴더에서도 찾기
        parent_folder = os.path.dirname(self.output_folder)
        if os.path.exists(parent_folder):
            for f in os.listdir(parent_folder):
                for ext in video_extensions:
                    if f.lower().endswith(ext):
                        return os.path.join(parent_folder, f)
        
        return None
    
    def _find_synced_srt(self):
        """_synced.srt 파일 찾기"""
        for f in os.listdir(self.output_folder):
            if f.endswith('_synced.srt'):
                return os.path.join(self.output_folder, f)
        
        # 일반 SRT 파일도 찾기
        for f in os.listdir(self.output_folder):
            if f.endswith('.srt'):
                return os.path.join(self.output_folder, f)
        
        return None
    
    def _get_resolve(self):
        """DaVinci Resolve API 연결 시도"""
        try:
            import sys
            resolve_script_paths = [
                "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
                os.path.expanduser("~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"),
            ]
            
            for path in resolve_script_paths:
                if os.path.exists(path) and path not in sys.path:
                    sys.path.append(path)
            
            import DaVinciResolveScript as dvr
            resolve = dvr.scriptapp("Resolve")
            return resolve
        except Exception as e:
            return None
    
    def _import_to_resolve_full(self, resolve, wav_folder, wav_files, video_file, srt_file, fcpxml_path):
        """DaVinci Resolve에 전체 임포트 + 타임라인 생성"""
        try:
            project_manager = resolve.GetProjectManager()
            project = project_manager.GetCurrentProject()

            if not project:
                QMessageBox.warning(self, "경고", "DaVinci Resolve에서 프로젝트를 먼저 열어주세요.")
                return

            media_pool = project.GetMediaPool()
            root_folder = media_pool.GetRootFolder()
            fps = float(project.GetSetting("timelineFrameRate") or 24)

            debug_log = []

            # === 1. 영상 파일 임포트 ===
            video_clip = None
            if video_file and os.path.exists(video_file):
                media_pool.SetCurrentFolder(root_folder)
                video_clips = media_pool.ImportMedia([video_file])
                if video_clips:
                    video_clip = video_clips[0]
                    debug_log.append(f"영상 임포트 OK: {video_clip.GetName()}")

            # === 2. AD_Audio 폴더에 WAV 임포트 ===
            ad_folder = None
            for subfolder in root_folder.GetSubFolderList():
                if subfolder.GetName() == "AD_Audio":
                    ad_folder = subfolder
                    break
            if not ad_folder:
                ad_folder = media_pool.AddSubFolder(root_folder, "AD_Audio")

            media_pool.SetCurrentFolder(ad_folder)
            wav_paths = [os.path.join(wav_folder, f) for f in sorted(wav_files)]
            wav_clips = media_pool.ImportMedia(wav_paths)
            debug_log.append(f"WAV 임포트: {len(wav_clips) if wav_clips else 0}개")

            # === 3. 타임라인 생성 ===
            timeline = None
            timeline_name = "AD_" + os.path.basename(self.output_folder)

            # 방법 1: 영상 클립으로 타임라인 생성
            if video_clip:
                try:
                    timeline = media_pool.CreateTimelineFromClips(timeline_name, [video_clip])
                    debug_log.append(f"CreateTimelineFromClips: {timeline is not None}")
                except Exception as e:
                    debug_log.append(f"CreateTimelineFromClips 실패: {e}")

            # 방법 2: 빈 타임라인 후 영상 추가
            if not timeline:
                timeline = media_pool.CreateEmptyTimeline(timeline_name)
                debug_log.append(f"CreateEmptyTimeline: {timeline is not None}")

                if timeline and video_clip:
                    project.SetCurrentTimeline(timeline)
                    try:
                        result = media_pool.AppendToTimeline([video_clip])
                        debug_log.append(f"AppendToTimeline(video): {bool(result)}")
                    except Exception as e:
                        debug_log.append(f"AppendToTimeline 실패: {e}")

            if not timeline:
                QMessageBox.warning(self, "경고", f"타임라인 생성 실패\n\n{chr(10).join(debug_log)}")
                return

            project.SetCurrentTimeline(timeline)

            # === 4. AD용 오디오 트랙 추가 ===
            # 기존 오디오 트랙 수 확인
            existing_audio_tracks = timeline.GetTrackCount("audio")
            debug_log.append(f"기존 오디오 트랙: {existing_audio_tracks}개")

            # AD용 오디오 트랙 추가 (A2 또는 그 이상)
            ad_audio_track = existing_audio_tracks + 1
            try:
                track_result = timeline.AddTrack("audio")
                debug_log.append(f"AddTrack(audio): {track_result}")
                if track_result:
                    # 트랙 이름 설정 시도
                    try:
                        timeline.SetTrackName("audio", ad_audio_track, "AD_Audio")
                    except:
                        pass
            except Exception as e:
                debug_log.append(f"AddTrack 실패: {e}")
                ad_audio_track = existing_audio_tracks  # 기존 마지막 트랙 사용

            # === 5. WAV 파일을 AD 오디오 트랙에 배치 ===
            wav_placed = 0
            if wav_clips:
                sorted_files = sorted(wav_files)

                # 파일명-클립 매핑 생성
                clip_map = {}
                for clip in wav_clips:
                    clip_name = clip.GetName()
                    clip_map[clip_name] = clip

                for filename in sorted_files:
                    clip = clip_map.get(filename)
                    if not clip:
                        continue

                    # 파일명에서 타임코드 추출 (00_00_05_12.wav 형식)
                    basename = os.path.splitext(filename)[0]
                    tc_parts = basename.split('_')

                    if len(tc_parts) >= 4:
                        try:
                            h = int(tc_parts[0])
                            m = int(tc_parts[1])
                            s = int(tc_parts[2])
                            f = int(tc_parts[3])
                            record_frame = int((h * 3600 + m * 60 + s) * fps + f)

                            # 클립 duration 가져오기
                            clip_props = clip.GetClipProperty()

                            # 방법 1: trackIndex와 recordFrame으로 배치
                            clip_info = {
                                "mediaPoolItem": clip,
                                "trackIndex": ad_audio_track,
                                "recordFrame": record_frame
                            }
                            result = media_pool.AppendToTimeline([clip_info])

                            if result:
                                wav_placed += 1
                                debug_log.append(f"  배치 OK: {filename} @ frame {record_frame}")
                            else:
                                # 방법 2: 기본 AppendToTimeline 후 이동 시도
                                result2 = media_pool.AppendToTimeline([clip])
                                if result2:
                                    wav_placed += 1
                                    debug_log.append(f"  배치(기본): {filename}")
                        except Exception as e:
                            debug_log.append(f"  배치 실패: {filename} - {e}")

                debug_log.append(f"WAV 배치 결과: {wav_placed}/{len(wav_clips)}개")

            # === 6. 자막(SRT) 파일 임포트 ===
            srt_imported = False
            if srt_file and os.path.exists(srt_file):
                # 방법 1: ImportSubtitleTrack (DaVinci Resolve 18+)
                try:
                    # 먼저 자막 트랙 추가 시도
                    timeline.AddTrack("subtitle")
                except:
                    pass

                try:
                    result = timeline.ImportSubtitleTrack(srt_file)
                    srt_imported = bool(result)
                    debug_log.append(f"ImportSubtitleTrack: {srt_imported}")
                except Exception as e:
                    debug_log.append(f"ImportSubtitleTrack 실패: {e}")

                # 방법 2: Media Pool에 SRT 추가 (폴백)
                if not srt_imported:
                    try:
                        media_pool.SetCurrentFolder(root_folder)
                        srt_clips = media_pool.ImportMedia([srt_file])
                        if srt_clips:
                            debug_log.append("SRT를 Media Pool에 임포트 (수동 배치 필요)")
                    except Exception as e:
                        debug_log.append(f"SRT Media Pool 임포트 실패: {e}")

            # === 7. 결과 ===
            track_v = timeline.GetTrackCount("video")
            track_a = timeline.GetTrackCount("audio")
            track_s = 0
            try:
                track_s = timeline.GetTrackCount("subtitle")
            except:
                pass

            msg = f"✅ 타임라인: {timeline.GetName()}\n"
            msg += f"📊 트랙: V{track_v} + A{track_a}"
            if track_s:
                msg += f" + S{track_s}"
            msg += f"\n\n"
            msg += f"🎬 영상: {'배치됨' if video_clip else '없음'}\n"
            msg += f"🔊 WAV: {wav_placed}/{len(wav_clips) if wav_clips else 0}개 배치\n"
            msg += f"📝 자막: {'임포트됨' if srt_imported else '수동 배치 필요'}\n\n"
            msg += f"[디버그]\n" + "\n".join(debug_log[-10:])  # 마지막 10개만

            QMessageBox.information(self, "DaVinci Resolve 임포트", msg)

        except Exception as e:
            import traceback
            QMessageBox.critical(self, "오류", f"{str(e)}\n\n{traceback.format_exc()}")
            self._show_manual_import_guide(wav_folder, fcpxml_path, video_file, srt_file)
    
    def _place_wav_on_audio_track(self, media_pool, timeline, wav_clips, wav_files, fps):
        """더 이상 사용하지 않음"""
        pass

    
    def _place_wav_on_audio_track(self, media_pool, timeline, wav_clips, wav_files, fps):
        """더 이상 사용하지 않음 - _import_to_resolve_full에 통합됨"""
        pass
    
    def _show_manual_import_guide(self, wav_folder, fcpxml_path, video_file, srt_file):
        """수동 임포트 가이드 표시"""
        guide_text = f"""DaVinci Resolve에서 AD 프로젝트를 설정하는 방법:

📁 출력 파일 위치:
• WAV 폴더: {wav_folder}
• FCPXML: {fcpxml_path if os.path.exists(fcpxml_path) else '(없음)'}
• 영상 파일: {video_file if video_file else '(없음)'}
• 자막 파일: {srt_file if srt_file else '(없음)'}

🎬 빠른 설정 (FCPXML 사용):
1. DaVinci Resolve 실행 → 프로젝트 열기
2. File > Import > Timeline > ad_import.fcpxml
3. WAV 폴더의 파일들이 자동으로 타임라인에 배치됨

🎬 수동 설정:
1. Media Pool에 영상 파일 드래그
2. Media Pool에 WAV 폴더 드래그
3. 영상을 타임라인에 배치
4. WAV 파일들을 타임코드에 맞춰 Audio 트랙에 배치

📝 자막 추가:
1. Edit 페이지 > Effects > Subtitles
2. 또는 File > Import > Subtitle > _synced.srt

💡 팁:
• WAV 파일명에 타임코드가 포함되어 있습니다
• FCPXML 사용 시 자동 배치가 됩니다
• 영상과 AD 오디오의 싱크를 확인하세요
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle("다빈치리졸브 임포트 가이드")
        msg.setText("DaVinci Resolve가 실행 중이 아니거나 API에 접근할 수 없습니다.")
        msg.setDetailedText(guide_text)
        msg.setIcon(QMessageBox.Icon.Information)
        
        btn_open = msg.addButton("폴더 열기", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        if msg.clickedButton() == btn_open:
            import subprocess
            subprocess.run(['open', self.output_folder])
    
    def open_settings(self):
        """설정 다이얼로그"""
        dialog = SettingsDialog(config, self)
        if dialog.exec():
            self.load_config()
            self.srt_batch_tab.refresh_api_status()
            self.single_clip_tab.refresh_api_status()
    
    def show_status(self, message: str):
        """상태바 메시지"""
        self.status_bar.showMessage(message, 5000)
    
    def closeEvent(self, event):
        """창 닫기"""
        config.voice_settings = self.voice_panel.get_settings()
        config.set('output', 'format', self.combo_format.currentData())
        config.set('output', 'frame_rate', self.combo_fps.currentData())
        event.accept()
