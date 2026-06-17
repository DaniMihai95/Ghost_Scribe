# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect OpenVINO dynamic libraries
openvino_binaries = collect_dynamic_libs('openvino')
genai_binaries = collect_dynamic_libs('openvino_genai')
tokenizers_binaries = collect_dynamic_libs('openvino_tokenizers')

# Combine binaries
all_binaries = openvino_binaries + genai_binaries + tokenizers_binaries

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=[],
    hiddenimports=[
        'pystray._win32', 
        'PIL._tkinter_finder', 
        'keyboard._winkeyboard',
        'openvino',
        'openvino.runtime',
        'openvino.runtime.opset13',
        'openvino_genai',
        'openvino_tokenizers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GhostScribe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ghost_scribe.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='GhostScribe',
)
