import os
from setuptools import setup
import glob

# Добавление флагов компиляции

APP = ['start.pyw']
DATA_FILES = []

# Включение всех файлов из папки images
for file in glob.glob('images/**/*', recursive=True):
    if os.path.isfile(file):
        DATA_FILES.append(('images', [file]))

# Включение всех файлов из папки data
for file in glob.glob('data/**/*', recursive=True):
    if os.path.isfile(file):
        DATA_FILES.append(('data', [file]))

# Добавление остальных необходимых файлов
DATA_FILES.append(('', ['settings.ini']))

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'images/icon.ico',
    'packages': ['rumps', 'customtkinter', 'greenlet', 'playwright', 'pyee', 'plotly', '_plotly_utils'],
    "excludes": ["playwright._impl.__pyinstaller.hook-playwright.sync_api",
                 "playwright._impl.__pyinstaller.hook-playwright.async_api"],
    'plist': {
        'CFBundleName': 'CheckPrices',
        'LSUIElement': True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)