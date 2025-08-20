# -*- mode: python ; coding: utf-8 -*-


import os

def collect_data_dirs():
    datas = [('assets/*', 'assets'),
             ('data/*', 'data')]
    base = os.path.abspath('data')
    for sub in ['logs']:
        full = os.path.join(base, sub)
        if os.path.exists(full):
            datas.append((full, f'data/{sub}'))
    return datas

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=collect_data_dirs(),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
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
    icon='assets/fms-icon.ico',
)
