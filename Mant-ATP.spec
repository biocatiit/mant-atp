# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mant-ATP
Cross-platform GUI application for XLSX data fitting
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all necessary data files and submodules
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'matplotlib.backends.backend_qtagg',
    'numpy',
    'pandas',
    'lmfit',
    'openpyxl',
]

# Add lmfit submodules (it has many internal imports)
hiddenimports += collect_submodules('lmfit')

# Collect data files needed by packages
datas = []
datas += collect_data_files('lmfit')

a = Analysis(
    ['fit_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific settings
if sys.platform == 'darwin':
    # macOS: Create .app bundle
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Mant-ATP',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # No terminal window
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
        name='Mant-ATP',
    )
    app = BUNDLE(
        coll,
        name='Mant-ATP.app',
        icon=None,  # Add icon path here if available
        bundle_identifier='com.mantatp.fitter',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'Mant-ATP',
            'NSHighResolutionCapable': True,
        },
    )
elif sys.platform == 'win32':
    # Windows: Create single .exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Mant-ATP',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # No console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,  # Add icon path here if available
    )
else:
    # Linux: Create single executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Mant-ATP',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
