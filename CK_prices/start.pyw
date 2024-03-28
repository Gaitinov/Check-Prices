import configparser
import ctypes
import subprocess
import os
import getpass
import threading

from modules.application import Application
from modules.update import update_tray

USER_NAME = getpass.getuser()

config = configparser.ConfigParser()
config.read("settings.ini")

enable_price_check_at_start = config.getboolean(
    "DEFAULT", "enable_price_check_at_start"
)


def is_already_running(exe_name):
    current_pid = os.getpid()

    call_result = subprocess.check_output(
        f'tasklist /fi "IMAGENAME eq {exe_name}"', shell=True
    ).decode("cp866")

    for line in call_result.splitlines():
        if exe_name in line and str(current_pid) not in line:
            return True
    return False


def show_message(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)


def add_to_startup():
    file_path = os.path.realpath(__file__)
    base_path = os.path.dirname(os.path.dirname(file_path))
    exe_name = "CheckPrices.exe"

    if is_already_running(exe_name):
        show_message("Ошибка запуска", f"Программа CheckPrices уже запущена")
        return

    exe_path = os.path.join(base_path, exe_name)
    bat_path = rf"C:\Users\{USER_NAME}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"

    with open(os.path.join(bat_path, "CheckPrices.bat"), "w+") as bat_file:
        bat_file.write(f'cd /d "{base_path}"\n')
        bat_file.write(f'start "" "{exe_path}" --auto-close')


add_to_startup()

if not is_already_running("CheckPrices.exe"):
    if enable_price_check_at_start:
        threadupdate = threading.Thread(target=update_tray)
        threadupdate.daemon = True
        threadupdate.start()
    app = Application()
