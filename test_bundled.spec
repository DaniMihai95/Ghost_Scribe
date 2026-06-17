# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect OpenVINO dynamic libraries
openvino_binaries = collect_dynamic_libs('openvino')
genai_binaries = collect_dynamic_libs('openvino_genai')
all_binaries = openvino_binaries + genai_binaries

a = Analysis(
    ['test_bundled.py'],
    pathex=[],
    binaries=all_binaries,
    datas=[],
    hiddenimports=[
        'openvino',
        'openvino.runtime',
        'openvino_genai',
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
    name='test_bundled',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # CONSOLE ENABLED for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='test_bundled',
)
