# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['C:/Users/Shorek/Desktop/Project 17/Check Prices/start.pyw'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/Shorek/Desktop/pythonProject1/Lib/site-packages/_plotly_utils', '_plotly_utils/'), ('C:/Users/Shorek/Desktop/pythonProject1/Lib/site-packages/edgedriver_autoinstaller', 'edgedriver_autoinstaller/'), ('C:/Users/Shorek/Desktop/pythonProject1/Lib/site-packages/plotly', 'plotly/'), ('C:/Users/Shorek/AppData/Local/Programs/Python/Python311/Lib/site-packages/customtkinter', 'customtkinter/'), ('C:/Users/Shorek/Desktop/Project 17/Check Prices/images', 'images/'), ('C:/Users/Shorek/Desktop/Project 17/Check Prices/modules/data', 'data/')],
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
    name='Check prices',
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
    icon=['C:\\Users\\Shorek\\Desktop\\Project 17\\Check Prices\\images\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Check prices',
)
