import tkinter
import tkinter.ttk
import tkinter.messagebox
import configparser
import os
import sys
import sqlite3
import customtkinter as ct
from modules.config import CustomEntry, DBPath


class Settings(ct.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_price_check_var = ct.StringVar(value="off")
        self.init_ui()
        self.load_current_value()

    def reload_aplication(self):
        new_args = sys.argv[:]
        if "--auto-close" in new_args:
            new_args.append("--from-settings")
        os.execv(sys.executable, [sys.executable] + new_args)

    def delete_all_data_from_db(self):
        response = tkinter.messagebox.askyesno(
            "Подтверждение удаления",
            "Вы уверены, что хотите безвозвратно удалить все данные из базы данных? Это действие нельзя отменить.",
        )
        if response:
            try:
                db_path = DBPath.get_or_init_db_path()

                con = sqlite3.connect(db_path)
                cur = con.cursor()
                cur.execute("DELETE FROM prices")
                cur.execute("DELETE FROM items")
                con.commit()
                tkinter.messagebox.showinfo(
                    "Успех", "Все данные были успешно удалены из базы данных."
                )
            except Exception as e:
                tkinter.messagebox.showerror(
                    "Ошибка", f"Произошла ошибка при удалении данных: {e}"
                )
            finally:
                con.close()
                self.reload_aplication()

    def init_ui(self):
        self.title("Настройки")
        window_width = 800
        window_height = 530
        self.geometry(
            f"{window_width}x{window_height}+{self.winfo_screenwidth() // 2 - window_width // 2}+{self.winfo_screenheight() // 2 - window_height // 2}"
        )
        self.configure(bg="#f0f0f0")

        self.entry_menu = CustomEntry(self)

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

        self.checkbutton_enable_price_check_at_start = ct.CTkCheckBox(
            frame,
            text="Включить проверку цен при запуске программы",
            variable=self.enable_price_check_var,
            onvalue="on",
            offvalue="off",
        )

        self.checkbutton_enable_price_check_at_start.pack(pady=10, padx=10, fill="x")

        self.delete_data_button = ct.CTkButton(
            frame,
            text="⚠ Удалить все данные из базы данных",
            command=self.delete_all_data_from_db,
            fg_color="red",
        )
        self.delete_data_button.pack(pady=10, padx=10)

        self.button = ct.CTkButton(frame, text="Сохранить", command=self.save_value)
        self.button.pack(pady=10, padx=10)

        for entry in (
            self.entry,
            self.entry_price_range_notification,
            self.entry_price_range_save_db,
            self.entry_min_reviews_count,
        ):
            entry.bind(
                "<Button-3>",
                lambda event, widget=entry: self.entry_menu.show(event, widget),
            )
            entry.bind("<Control-KeyPress>", lambda event: self.entry_menu.keys(event))

        self.resizable(False, False)
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
        # Assuming other setting load logic is correct...
        enable_price_check_at_start = config.get(
            "DEFAULT", "enable_price_check_at_start", fallback="off"
        )

        self.entry_min_reviews_count.insert(0, current_min_reviews_count)
        self.entry_price_range_notification.insert(0, current_price_range_notification)
        self.entry_price_range_save_db.insert(0, current_price_range_save_db)
        self.entry.insert(0, current_value)
        self.enable_price_check_var.set(
            "on" if enable_price_check_at_start == "1" else "off"
        )

    def save_value(self):
        response = tkinter.messagebox.askyesno(
            "Подтверждение сохранения",
            "Программа будет перезапущена для применения изменений. Продолжить?",
        )
        if response:
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
                tkinter.messagebox.showerror(
                    "Ошибка диапазона цен для сохранения", str(e)
                )
                return

            try:
                value_int = int(value)
                if value_int <= 59 or value_int > 100000:
                    raise ValueError(
                        "Введите корректное положительное число, не равное нулю, не меньше 60 и не больше 100000"
                    )
                config.set("DEFAULT", "CHECK_PRICE_INTERVAL", value)
            except ValueError as e:
                tkinter.messagebox.showerror(
                    "Ошибка интервала проверки цен в фоне", str(e)
                )
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
                tkinter.messagebox.showerror(
                    "Ошибка диапазона цен для уведомлений", str(e)
                )
                return

            try:
                min_reviews_count = int(self.entry_min_reviews_count.get())
                if min_reviews_count < 0:
                    raise ValueError("Введите корректное количество отзывов")
                config.set("DEFAULT", "MIN_REVIEWS_COUNT", str(min_reviews_count))
            except ValueError as e:
                tkinter.messagebox.showerror("Ошибка в количестве отзывов", str(e))
                return

            try:
                enable_price_check_at_start_value = (
                    "1" if self.enable_price_check_var.get() == "on" else "0"
                )
                config.set(
                    "DEFAULT",
                    "enable_price_check_at_start",
                    enable_price_check_at_start_value,
                )
            except ValueError as e:
                tkinter.messagebox.showerror(
                    "Ошибка включения проверки цен при запуске программы", str(e)
                )
                return

            with open("settings.ini", "w") as configfile:
                config.write(configfile)

            self.reload_aplication()

            self.destroy()
