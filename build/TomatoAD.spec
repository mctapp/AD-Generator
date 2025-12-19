# -*- mode: python ; coding: utf-8 -*-
# TomatoAD.spec
# PyInstaller 빌드 설정

import sys
from pathlib import Path

block_cipher = None

# 프로젝트 경로
project_path = Path(SPECPATH).parent

a = Analysis(
    [str(project_path / 'src' / 'main.py')],
    pathex=[str(project_path)],
    binaries=[],
    datas=[
        (str(project_path / 'src' / 'resources' / 'voices.json'), 'src/resources'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TomatoAD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TomatoAD',
)

app = BUNDLE(
    coll,
    name='TOMATO AD Voice Generator.app',
    icon=None,  # 아이콘 파일이 있으면 'src/resources/icon.icns'
    bundle_identifier='kr.mct.tomatoad',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'SRT Subtitle',
                'CFBundleTypeExtensions': ['srt'],
                'CFBundleTypeRole': 'Viewer',
            }
        ],
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
    },
)
