# player.spec - PyInstaller 빌드 스크립트 (player.py 기반, PySide6 전체 및 VLC DLL 포함)

from PyInstaller.utils.hooks import collect_submodules
import glob
import os

# VLC dll 경로 (예시: 시스템에 따라 경로 조정 필요)
vlc_dll_dir = r'C:/Program Files/VideoLAN/VLC'  # 또는 실제 dll 경로
# VLC 필수 DLL 및 plugins 폴더만 포함
vlc_binaries = [
    (os.path.join(vlc_dll_dir, 'libvlc.dll'), '.'),
    (os.path.join(vlc_dll_dir, 'libvlccore.dll'), '.'),
]
vlc_plugins = [
    (os.path.join(vlc_dll_dir, 'plugins'), 'plugins'),
]

# PySide6 전체 모듈 및 plugin 포함
pyside6_plugins = [
    (os.path.join(os.path.dirname(__import__('PySide6').__file__), 'plugins'), 'PySide6/plugins'),
]

# 필요한 PySide6 모듈만 포함
pyside6_modules = [
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtSvg',
    'PySide6.QtSvgWidgets',
]

a = Analysis([
    'player.py',
],
    pathex=[],
    binaries=vlc_binaries,
    datas=[
        (r'./icon.ico', '.'),
        (r'./icon.png', '.'),
    ] + pyside6_plugins + vlc_plugins,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='player',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
    onefile=True,
)