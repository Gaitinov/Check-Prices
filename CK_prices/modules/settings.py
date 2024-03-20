import tkinter
import ctypes
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

    def is_ru_lang_keyboard(self):
        user32 = ctypes.windll.LoadLibrary("user32.dll")
        return hex(user32.GetKeyboardLayout(0)) == "0x4190419"

    def keys(self, event):
        if self.is_ru_lang_keyboard():
            if event.keycode == 86:  # 'V' in Russian layout
                event.widget.event_generate("<<Paste>>")
            elif event.keycode == 67:  # 'C' in Russian layout
                event.widget.event_generate("<<Copy>>")
            elif event.keycode == 88:  # 'X' in Russian layout
                event.widget.event_generate("<<Cut>>")
            elif event.keycode == 65535:  # Delete key
                event.widget.event_generate("<<Clear>>")
            elif event.keycode == 65:  # 'A' in Russian layout
                event.widget.event_generate("<<SelectAll>>")

    def init_ui(self):
        self.title("Настройки")
        self.geometry(
            f"800x450+{self.winfo_screenwidth() // 2 - 800 // 2}+{self.winfo_screenheight() // 2 - 450 // 2}"
        )
        self.configure(bg="#f0f0f0")

        frame = ct.CTkFrame(self, corner_radius=10)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.label = ct.CTkLabel(
            frame,
            text="Введите новое значение интервала проверки цен (в секундах):",
            anchor="w",
        )
        self.label.pack(pady=10, padx=10, fill="x")

        self.entry = ct.CTkEntry(frame, width=400, corner_radius=5)
        self.entry.pack(pady=5, padx=10, fill="x")

        self.label_price_range = ct.CTkLabel(
            frame, text="Введите диапазон цен для уведомлений:", anchor="w"
        )
        self.label_price_range.pack(pady=10, padx=10, fill="x")

        self.entry_price_range_notification = ct.CTkEntry(
            frame, width=400, corner_radius=5
        )
        self.entry_price_range_notification.pack(pady=5, padx=10, fill="x")

        self.label_price_range_save_db = ct.CTkLabel(
            frame, text="Введите диапазон цен для сохранения в базу данных:", anchor="w"
        )
        self.label_price_range_save_db.pack(pady=10, padx=10, fill="x")

        self.entry_price_range_save_db = ct.CTkEntry(frame, width=400, corner_radius=5)
        self.entry_price_range_save_db.pack(pady=5, padx=10, fill="x")

        self.label_min_reviews_count = ct.CTkLabel(
            frame,
            text="Введите минимальное количество отзывов у магазина Kaspi при проверке цен:",
            anchor="w",
        )
        self.label_min_reviews_count.pack(pady=10, padx=10, fill="x")

        self.entry_min_reviews_count = ct.CTkEntry(frame, width=400, corner_radius=5)
        self.entry_min_reviews_count.pack(pady=5, padx=10, fill="x")

        self.button = ct.CTkButton(frame, text="Сохранить", command=self.save_value)
        self.button.pack(pady=10, padx=10)

        self.entry.bind("<Control-KeyPress>", self.keys)
        self.entry_price_range_notification.bind("<Control-KeyPress>", self.keys)
        self.entry_price_range_save_db.bind("<Control-KeyPress>", self.keys)
        self.entry_min_reviews_count.bind("<Control-KeyPress>", self.keys)

        self.grab_set()

    def load_current_value(self):
        config = configparser.ConfigParser()
        config.read("settings.ini")
        current_value = config.get(
            "DEFAULT", "CHECK_PRICE_INTERVAL", fallback="Введите значение"
        )

        current_price_range_notification = config.get(
            "DEFAULT", "PRICE_RANGE_NOTIFICATION", fallback="Введите значение"
        )
        current_price_range_save_db = config.get(
            "DEFAULT", "PRICE_RANGE_FOR_SAVE_TO_DB", fallback="Введите значение"
        )
        current_min_reviews_count = config.get(
            "DEFAULT", "MIN_REVIEWS_COUNT", fallback="Введите значение"
        )
        self.entry_min_reviews_count.insert(0, current_min_reviews_count)
        self.entry_price_range_notification.insert(0, current_price_range_notification)
        self.entry_price_range_save_db.insert(0, current_price_range_save_db)
        self.entry.insert(0, current_value)

    def save_value(self):
        value = self.entry.get()
        price_range_notification = self.entry_price_range_notification.get()
        price_range_save_db = self.entry_price_range_save_db.get()
        config = configparser.ConfigParser()
        config.read("settings.ini")

        try:
            price_range_save = int(price_range_save_db)
            if price_range_save < 0:
                raise ValueError("Введите корректный диапазон цен для сохранения")
            config.set(
                "DEFAULT", "PRICE_RANGE_FOR_SAVE_TO_DB", str(price_range_save)
            )  # Сохранение как строки
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка диапазона цен для сохранения", str(e))
            return

        try:
            value_int = int(value)
            if value_int <= 59 or value_int > 100000:
                raise ValueError(
                    "Введите корректное положительное число, не равное нулю, не меньше 60 и не больше 100000"
                )
            config.set("DEFAULT", "CHECK_PRICE_INTERVAL", value)
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка интервала проверки цен в фоне", str(e))
            return

        try:
            price_range_notification = int(price_range_notification)
            if price_range_notification < price_range_save:
                raise ValueError(
                    "Введите корректный диапазон цен для уведомлений, который больше или равен диапазону цен для сохранения"
                )
            config.set(
                "DEFAULT", "PRICE_RANGE_NOTIFICATION", str(price_range_notification)
            )
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка диапазона цен для уведомлений", str(e))
            return

        try:
            min_reviews_count = int(self.entry_min_reviews_count.get())
            if min_reviews_count < 0:
                raise ValueError("Введите корректное количество отзывов")
            config.set("DEFAULT", "MIN_REVIEWS_COUNT", str(min_reviews_count))
        except ValueError as e:
            tkinter.messagebox.showerror("Ошибка в количестве отзывов", str(e))
            return

        with open("settings.ini", "w") as configfile:
            config.write(configfile)

        os.execv(sys.executable, ["python"] + sys.argv)
        self.destroy()
