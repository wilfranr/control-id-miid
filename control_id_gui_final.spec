# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import sys
from pathlib import Path

# Rutas
proj_dir = Path(__file__).parent
assets_dir = proj_dir / 'assets'
images_dir = assets_dir / 'images'

a = Analysis(
    ['control_id_gui_final.py'],
    pathex=[str(proj_dir)],
    binaries=[],
    datas=[
        (str(images_dir / 'logo.png'), 'assets/images'),
        # Incluir config.py si existe en la raíz al momento del build
        (str(proj_dir / 'config.py'), '.' ) if (proj_dir / 'config.py').exists() else (),
    ],
    hiddenimports=[],
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
    name='ControlIdGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(images_dir / 'logo.ico') if (images_dir / 'logo.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ControlIdGUI'
)
