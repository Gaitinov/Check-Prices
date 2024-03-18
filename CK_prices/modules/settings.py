import tkinter
import tkinter.ttk
import tkinter.messagebox
import customtkinter as ct
import configparser
import os
import sys


class Settings(tkinter.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_ui()
        self.load_current_value()

    def init_ui(self):
        self.title("Настройки")
        self.geometry(
            f"800x600+{self.winfo_screenwidth() // 2 - 800 // 2}+{self.winfo_screenheight() // 2 - 600 // 2}")
        self.configure(bg='#f0f0f0')

        # Использование корректного аргумента для задания шрифта
        self.label = ct.CTkLabel(self, text="Введите новое значение интервала проверки цен (в секундах) в трее:")
        self.label.pack(pady=10)

        self.entry = ct.CTkEntry(self, width=200, corner_radius=10)
        self.entry.pack(pady=5)

        self.label_price_range = ct.CTkLabel(self, text="Введите диапазон цен для уведомлений:")
        self.label_price_range.pack(pady=10)

        self.entry_price_range_notification = ct.CTkEntry(self, width=200, corner_radius=10)
        self.entry_price_range_notification.pack(pady=5)

        self.label_price_range_save_db = ct.CTkLabel(self, text="Введите диапазон цен для сохранения в базу данных:")
        self.label_price_range_save_db.pack(pady=10)

        self.entry_price_range_save_db = ct.CTkEntry(self, width=200, corner_radius=10)
        self.entry_price_range_save_db.pack(pady=5)

        self.button = ct.CTkButton(self, text="Сохранить", command=self.save_value)
        self.button.pack(pady=10)

        self.grab_set()


    def load_current_value(self):
        config = configparser.ConfigParser()
        config.read('settings.ini')
        current_value = config.get('DEFAULT', 'CHECK_PRICE_INTERVAL', fallback='Введите значение')

        current_price_range_notification = config.get('DEFAULT', 'PRICE_RANGE_NOTIFICATION', fallback='Введите значение')
        current_price_range_save_db = config.get('DEFAULT', 'PRICE_RANGE_FOR_SAVE_TO_DB', fallback='Введите значение')
        self.entry_price_range_notification.insert(0, current_price_range_notification)
        self.entry_price_range_save_db.insert(0, current_price_range_save_db)
        self.entry.insert(0, current_value)

    def save_value(self):
        value = self.entry.get()
        price_range_notification = self.entry_price_range_notification.get()
        price_range_save_db = self.entry_price_range_save_db.get()
        config = configparser.ConfigParser()
        config.read('settings.ini')

        try:
            price_range_save = int(price_range_save_db)
            if price_range_save < 0:
                raise ValueError("Введите корректный диапазон цен для сохранения")
            config.set('DEFAULT', 'PRICE_RANGE_FOR_SAVE_TO_DB', str(price_range_save))  # Сохранение как строки
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка", str(e))
            return

        try:
            value_int = int(value)
            if value_int <= 59 or value_int > 100000:
                raise ValueError(
                    "Введите корректное положительное число, не равное нулю, не меньше 60 и не больше 100000")
            config.set('DEFAULT', 'CHECK_PRICE_INTERVAL', value)
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка", str(e))
            return

        try:
            price_range_notification = int(price_range_notification)
            if price_range_notification < price_range_save:
                raise ValueError(
                    "Введите корректный диапазон цен для уведомлений, который больше или равен диапазону цен для сохранения")
            config.set('DEFAULT', 'PRICE_RANGE_NOTIFICATION', str(price_range_notification))
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка", str(e))
            return

        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

        os.execv(sys.executable, ['python'] + sys.argv)
        self.destroy()



