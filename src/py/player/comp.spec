# your_script.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

block_cipher = None

# PySide6 관련 리소스 수집
pyside6_binaries = collect_data_files("PySide6", include_py_files=True)
pyside6_plugins = collect_data_files("PySide6.QtPlugins")
pyside6_modules = collect_submodules("PySide6")

# VLC 관련 파일
vlc_root = r"C:\Program Files\VideoLAN\VLC"
vlc_binaries = [
    (os.path.join(vlc_root, "libvlc.dll"), "."),
    (os.path.join(vlc_root, "libvlccore.dll"), "."),
]
vlc_plugins = [(os.path.join(vlc_root, "plugins"), "plugins")]

a = Analysis(
    ['player.py'],
    pathex=['.'],
    binaries=vlc_binaries + pyside6_binaries,
    datas=vlc_plugins + pyside6_plugins,
    hiddenimports=pyside6_modules,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='video',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False  # GUI 앱일 경우 False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='video'
)
