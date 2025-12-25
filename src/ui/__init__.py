# ui/__init__.py
from .main_window import MainWindow
from .settings_dialog import SettingsDialog
from .styles import MAIN_STYLE, COLORS, get_button_style
from .widgets import DropZone, VoicePanel, SRTTable, TimecodeInput, ClipHistoryTable
from .tabs import SRTBatchTab, SingleClipTab, ScriptConverterTab, SRTSyncTab
from .effects import (
    apply_shadow, apply_card_shadow, apply_button_shadow,
    apply_glow_effect, apply_green_glow, apply_purple_glow
)
