# ui/settings_dialog.py
# API 키 및 앱 설정 다이얼로그

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFormLayout,
    QMessageBox, QTabWidget, QWidget, QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from .styles import COLORS


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        self.setWindowTitle("설정")
        self.setMinimumWidth(450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 탭 위젯
        tabs = QTabWidget()
        
        # API 설정 탭
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        api_group = QGroupBox("NAVER Cloud Platform API")
        api_form = QFormLayout(api_group)
        
        self.edit_client_id = QLineEdit()
        self.edit_client_id.setPlaceholderText("Client ID를 입력하세요")
        api_form.addRow("Client ID:", self.edit_client_id)
        
        self.edit_client_secret = QLineEdit()
        self.edit_client_secret.setPlaceholderText("Client Secret을 입력하세요")
        self.edit_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("Client Secret:", self.edit_client_secret)
        
        # 비밀번호 보기 체크
        show_secret_row = QHBoxLayout()
        self.btn_show_secret = QPushButton("표시")
        self.btn_show_secret.setCheckable(True)
        self.btn_show_secret.toggled.connect(self.toggle_secret_visibility)
        self.btn_show_secret.setFixedWidth(60)
        show_secret_row.addStretch()
        show_secret_row.addWidget(self.btn_show_secret)
        api_form.addRow("", show_secret_row)
        
        # 연결 테스트 버튼
        self.btn_test = QPushButton("연결 테스트")
        self.btn_test.clicked.connect(self.test_connection)
        api_form.addRow("", self.btn_test)
        
        api_layout.addWidget(api_group)
        
        # API 발급 안내
        info_label = QLabel(
            '<a href="https://www.ncloud.com/product/aiService/clovaVoice">'
            'NAVER Cloud Platform에서 API 키 발급받기</a>'
        )
        info_label.setOpenExternalLinks(True)
        info_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 10px;")
        api_layout.addWidget(info_label)
        
        api_layout.addStretch()
        tabs.addTab(api_tab, "API 설정")
        
        # 출력 설정 탭
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)
        
        output_group = QGroupBox("출력 설정")
        output_form = QFormLayout(output_group)
        
        self.combo_format = QComboBox()
        self.combo_format.addItem("FCPXML (권장)", "fcpxml")
        self.combo_format.addItem("EDL", "edl")
        output_form.addRow("출력 형식:", self.combo_format)
        
        self.combo_fps = QComboBox()
        self.combo_fps.addItem("24 fps", 24)
        self.combo_fps.addItem("23.976 fps", 23.976)
        self.combo_fps.addItem("25 fps", 25)
        self.combo_fps.addItem("29.97 fps", 29.97)
        self.combo_fps.addItem("30 fps", 30)
        output_form.addRow("프레임레이트:", self.combo_fps)
        
        output_layout.addWidget(output_group)
        
        # 고급 설정
        advanced_group = QGroupBox("고급 설정")
        advanced_form = QFormLayout(advanced_group)
        
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0.1, 2.0)
        self.spin_delay.setSingleStep(0.1)
        self.spin_delay.setValue(0.3)
        self.spin_delay.setSuffix(" 초")
        advanced_form.addRow("API 호출 간격:", self.spin_delay)
        
        output_layout.addWidget(advanced_group)
        output_layout.addStretch()
        
        tabs.addTab(output_tab, "출력 설정")
        
        layout.addWidget(tabs)
        
        # 버튼
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("저장")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
    
    def toggle_secret_visibility(self, checked):
        """시크릿 키 표시/숨김"""
        if checked:
            self.edit_client_secret.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_show_secret.setText("숨김")
        else:
            self.edit_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_show_secret.setText("표시")
    
    def load_settings(self):
        """설정 로드"""
        self.edit_client_id.setText(self.config.client_id)
        self.edit_client_secret.setText(self.config.client_secret)
        
        # 출력 형식
        output_format = self.config.get('output', 'format') or 'fcpxml'
        index = self.combo_format.findData(output_format)
        if index >= 0:
            self.combo_format.setCurrentIndex(index)
        
        # 프레임레이트
        fps = self.config.get('output', 'frame_rate') or 24
        index = self.combo_fps.findData(fps)
        if index >= 0:
            self.combo_fps.setCurrentIndex(index)
        
        # API 딜레이
        delay = self.config.get('app', 'api_delay') or 0.3
        self.spin_delay.setValue(delay)
    
    def save_settings(self):
        """설정 저장"""
        self.config.client_id = self.edit_client_id.text().strip()
        self.config.client_secret = self.edit_client_secret.text().strip()
        
        self.config.set('output', 'format', self.combo_format.currentData())
        self.config.set('output', 'frame_rate', self.combo_fps.currentData())
        self.config.set('app', 'api_delay', self.spin_delay.value())
        
        self.accept()
    
    def test_connection(self):
        """API 연결 테스트"""
        client_id = self.edit_client_id.text().strip()
        client_secret = self.edit_client_secret.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "경고", "Client ID와 Client Secret을 입력하세요.")
            return
        
        # TTS 엔진으로 테스트
        from ..core.tts_engine import TTSEngine
        engine = TTSEngine(client_id, client_secret)
        
        self.btn_test.setEnabled(False)
        self.btn_test.setText("테스트 중...")
        
        # 실제로는 비동기로 해야 하지만 간단히 동기 처리
        success, message = engine.test_connection()
        
        self.btn_test.setEnabled(True)
        self.btn_test.setText("연결 테스트")
        
        if success:
            QMessageBox.information(self, "성공", f"✓ {message}\n\nAPI 연결이 정상입니다.")
        else:
            QMessageBox.critical(self, "실패", f"✗ {message}\n\nAPI 키를 확인하세요.")
