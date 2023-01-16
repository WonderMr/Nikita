# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['Nikita.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['subprocess', 'clickhouse_driver', 'cherrypy', 'urllib', 'threading', 'requests', 're', 'time', 'operator', 'json', 'psutil', 'subprocess', 'shlex', 'platform', 'socket', 'sqlite3', 'src.parser', 'src.reader', 'win32timezone', 'src.dictionaries', 'src.messenger'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'cryptography', 'lib2to3', 'win32com', 'gevent', 'matplotlib', 'matplotlib.backend', '__PyInstaller_hooks_0_pandas_io_formats_style'],
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
    name='Nikita',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='Nikita',
)
