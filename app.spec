# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('customtkinter')
# Для Playwright часто требуется collect_all, чтобы подтянуть драйверы браузеров
from PyInstaller.utils.hooks import collect_all
tmp_ret = collect_all('playwright')
datas += tmp_ret[0]; binaries = tmp_ret[1]; hiddenimports = tmp_ret[2]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['selenium'], # Явно исключаем селениум
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
    name='Profi Parser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # <--- ВАЖНО: Отключаем сжатие UPX, чтобы антивирус не блокировал менеджер драйверов
    upx_exclude=['selenium-manager.exe'], # На всякий случай дублируем исключение для бинарника
    console=False,          # GUI режим без всплывающего окна cmd
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
