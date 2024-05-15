import logging
import configparser
import getpass
import multiprocessing
import threading

logging.basicConfig(
    filename="Logs.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

from modules.application import Application
from modules.update import update_tray

USER_NAME = getpass.getuser()

config = configparser.ConfigParser()
config.read("settings.ini")

enable_price_check_at_start = config.getboolean(
    "DEFAULT", "enable_price_check_at_start"
)





if enable_price_check_at_start:
    threadupdate = threading.Thread(target=update_tray)
    threadupdate.daemon = True
    threadupdate.start()
if __name__ == "__main__":
    if multiprocessing.get_start_method() != 'spawn':
        multiprocessing.set_start_method('spawn')
    app = Application()