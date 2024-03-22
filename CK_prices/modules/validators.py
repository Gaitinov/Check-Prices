from urllib.parse import urlparse
import tkinter.messagebox
import re
import datetime


class Validators:
    @staticmethod
    def is_known_store(url):
        known_stores = ["flip", "technodom", "kaspi", "ozon"]
        return any(store in url for store in known_stores)

    @staticmethod
    def is_valid_link(link):
        try:
            result = urlparse(link)
            return all([result.scheme, result.netloc])
        except:
            return False

    @staticmethod
    def validate_url(link):

        if not link:
            tkinter.messagebox.showerror(
                "Ошибка", "Поле `Ссылка` не должно быть пустым."
            )
            return False

        if not Validators.is_valid_link(link):
            tkinter.messagebox.showerror("Ошибка", "Недопустимый URL в поле `Ссылка`.")
            return False

        if not Validators.is_known_store(link):
            tkinter.messagebox.showerror("Ошибка", f"Неизвестный магазин: {link}")
            return False

        return True

    def validate_item(item):
        if not item:
            tkinter.messagebox.showerror(
                "Ошибка", "Поле `Товар` не должно быть пустым."
            )
            return False

        return True

    def validate_time(time):
        time = time.strip()

        if not time:
            tkinter.messagebox.showerror(
                "Ошибка", "Поле `Время` не должно быть пустым."
            )
            return False

        if not re.match(
            "^(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])/([0-9]{4}) ([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$",
            time,
        ):
            tkinter.messagebox.showerror(
                "Ошибка", "Время должно быть в формате MM/DD/YYYY HH:MM:SS."
            )
            return False

        try:
            # Validate time format and actual feasibility of the date/time
            datetime.datetime.strptime(time, "%m/%d/%Y %H:%M:%S")
        except ValueError:
            tkinter.messagebox.showerror(
                "Ошибка", "Время должно быть в формате MM/DD/YYYY HH:MM:SS и быть действительной датой."
            )
            return False

        return True

    def validate_price(price):
        price = price.strip()

        if not price:
            tkinter.messagebox.showerror("Ошибка", "Поле `Цена` не должно быть пустым.")
            return False

        if not re.match("^\d+(\.\d{1,2})?$", price):
            tkinter.messagebox.showerror("Ошибка", "Цена должна быть числом.")
            return False

        if not float(price) > -1:
            tkinter.messagebox.showerror("Ошибка", "Цена должна быть больше 0.")
            return False

        return True

    def validate_id(id):
        id = id.strip()

        if not id:
            tkinter.messagebox.showerror("Ошибка", "Поле `ID` не должно быть пустым.")
            return False

        if not re.match("^\d+$", id):
            tkinter.messagebox.showerror("Ошибка", "ID должен быть числом.")
            return False

        return True
