# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['usonicapp.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('constants.py', '.'),
        ('calc_stat.py', '.'),
        ('config.py', '.'),
        ('database.py', '.'),
        ('models.py', '.'),
        ('plottab.py', '.'),
        ('serialport.py', '.'),
        ('widgets.py', '.'),
        ('qbstyles/styles/', './qbstyles/styles/'),
        ('forms/', './forms/'),
        ('icons/', './icons/'),
        ('img/', './img/'),
        ('settings.toml', '.'),

    ],
    hiddenimports=[
        'playhouse',
        'playhouse.shortcuts',
        'matplotlib',
        'qbstyles',
        'PyQt5.QtSerialPort',
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core._multiarray_tests',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg'
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
    name='usonicapp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name='usonicapp',
)
