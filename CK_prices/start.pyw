import os
import getpass
from modules.application import Application

# Получение имени текущего пользователя
USER_NAME = getpass.getuser()

def add_to_startup():
    # Путь к текущему исполняемому файлу
    file_path = os.path.realpath(__file__)
    # Обрезаем последний сегмент пути (имя файла) и '_internal' папку
    base_path = os.path.dirname(os.path.dirname(file_path))
    # Добавляем имя файла, которое мы ожидаем для исполняемого файла
    exe_name = 'CheckPrices.exe'
    exe_path = os.path.join(base_path, exe_name)

    # Путь к папке автозагрузки для текущего пользователя
    bat_path = rf'C:\Users\{USER_NAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'

    # Создание BAT-файла для запуска приложения
    with open(os.path.join(bat_path, "CheckPrices.bat"), "w+") as bat_file:
        bat_file.write(f'cd /d "{base_path}"\n')  # Изменяем директорию на директорию с exe-файлом
        bat_file.write(f'start "" "{exe_path}"')  # Запускаем exe-файл

# Вызов функции для добавления приложения в автозагрузку
add_to_startup()

# Создание экземпляра вашего приложения
app = Application()