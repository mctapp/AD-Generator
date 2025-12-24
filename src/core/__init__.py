# core/__init__.py
from .srt_parser import SRTParser, SRTEntry
from .tts_engine import TTSEngine, TTSOptions
from .overlap_checker import OverlapChecker, OverlapResult
from .export import FCPXMLExporter, EDLExporter
from .srt_generator import SRTGenerator
from .srt_sync import SRTSync, SyncEntry
from .xlsx_exporter import XLSXExporter
from .validation import Validator, ValidationResult

try:
    from .pdf_parser import PDFParser, ScriptEntry
    HAS_PDF = True
except ImportError:
    HAS_PDF = False
    ScriptEntry = None
