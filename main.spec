# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*', 'assets'),
        ('data/*', 'data'),  # Include data folder
    ],
    hiddenimports=[
        'flet_core',
        'flet',
        'login_window',
        'admin_panel', 
        'user.user_panel',
        'TLPanel',
        'utils.path_config',
        'services.approval_service',
        'admin.components.approval_actions',
        'admin.components',
        'services',
        'utils',
        'user',
        'admin',
        'typing',
        'json',
        'os',
        'datetime'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KMTI File Management System',
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
    icon='assets/fms-icon.ico'
)