# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Administrator\\Documents\\Nikita\\Nikita.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['subprocess', 'cherrypy', 'urllib', 'threading', 'requests', 're', 'time', 'operator', 'json', 'psutil', 'shlex', 'platform', 'socket', 'sqlite3', 'src.parser', 'src.reader', 'src.dictionaries', 'src.messenger', 'src.globals', 'src.tools', 'src.solr', 'src.sender', 'src.redis_manager', 'src.state_manager', 'src.parser_state', 'src.cherry'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'cryptography', 'lib2to3', 'win32com'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nikita',
)
