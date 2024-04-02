import configparser
import tkinter
import threading
import sqlite3
from datetime import datetime
import customtkinter as ct
from modules.validators import Validators
from modules.product_info_extractor import extract_product_info
from modules.config import CustomEntry, DBPath

config = configparser.ConfigParser()
config.read("settings.ini")

min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


class Record(ct.CTkToplevel):
    def __init__(self, parent=None, record={}):
        super().__init__()
        self.parent = parent
        self.create_widgets(record)
        self.title("Изменение записи" if record["id_record"] else "Добавление записи")
        self.resizable(False, False)
        self.transient(parent)
        self.focus_set()
        self.grab_set()

    def create_widgets(self, record):
        self.entry_menu = CustomEntry(self)

        grid_params = {"padx": 10, "pady": 6}

        self.id_record = record["id_record"]
        self.id_item = ct.StringVar()
        self.id_item.set(record["id_item"])
        self.item = ct.StringVar()
        self.item.set(record["item"])
        self.price = ct.StringVar()
        self.price.set(record["price"])
        self.time = ct.StringVar()
        self.time.set(record["time"])
        self.link = ct.StringVar()
        self.link.set(record["link"])
        self.information = ct.StringVar()
        self.information.set(record["information"])

        frame = ct.CTkFrame(self, corner_radius=10, bg_color="#f0f0f0")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.id_item = ct.StringVar(value=record.get("id_item", ""))
        lblid_item = ct.CTkLabel(frame, text="ID товара")
        lblid_item.grid(row=0, column=0, **grid_params)
        self.entid_item = ct.CTkEntry(frame, textvariable=self.id_item, width=600)
        self.entid_item.grid(row=0, column=1, sticky="we", **grid_params)

        self.item = ct.StringVar(value=record.get("item", ""))
        lblitem = ct.CTkLabel(frame, text="Товар")
        lblitem.grid(row=1, column=0, **grid_params)
        self.entitem = ct.CTkEntry(frame, textvariable=self.item, width=600)
        self.entitem.grid(row=1, column=1, sticky="we", **grid_params)

        self.price = ct.StringVar(value=record.get("price", ""))
        lblprice = ct.CTkLabel(frame, text="Цена")
        lblprice.grid(row=2, column=0, **grid_params)
        self.entprice = ct.CTkEntry(frame, textvariable=self.price, width=600)
        self.entprice.grid(row=2, column=1, sticky="we", **grid_params)

        self.time = ct.StringVar(value=record.get("time", ""))
        lbltime = ct.CTkLabel(frame, text="Время")
        lbltime.grid(row=3, column=0, **grid_params)
        self.enttime = ct.CTkEntry(frame, textvariable=self.time, width=600)
        self.enttime.grid(row=3, column=1, sticky="we", **grid_params)

        self.link = ct.StringVar(value=record.get("link", ""))
        lbllink = ct.CTkLabel(frame, text="Ссылка")
        lbllink.grid(row=4, column=0, **grid_params)
        self.entlink = ct.CTkEntry(frame, textvariable=self.link, width=600)
        self.entlink.grid(row=4, column=1, sticky="we", **grid_params)

        self.information = ct.StringVar(value=record.get("information", ""))
        lblinformation = ct.CTkLabel(frame, text="Информация")
        lblinformation.grid(row=5, column=0, **grid_params)
        self.entinformation = ct.CTkEntry(
            frame, textvariable=self.information, width=400
        )
        self.entinformation.grid(row=5, column=1, sticky="we", **grid_params)

        for entry in [
            self.entid_item,
            self.entitem,
            self.entprice,
            self.enttime,
            self.entlink,
            self.entinformation,
        ]:
            entry.bind(
                "<Button-3>",
                lambda event, widget=entry: self.entry_menu.show(event, widget),
            )
            entry.bind("<Control-KeyPress>", lambda event: self.entry_menu.keys(event))

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=6, column=0, sticky="e", **grid_params)
        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=6, column=1, sticky="e", **grid_params)

        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.bind("<Map>", self.place)

    def place(self, evt):
        self.update_idletasks()

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)

        self.geometry(f"+{x}+{y}")

    def validation(self):
        if not Validators.validate_id(self.id_item.get()):
            return
        if not Validators.validate_item(self.item.get()):
            return
        if not Validators.validate_price(self.price.get()):
            return
        if not Validators.validate_time(self.time.get()):
            return
        if not Validators.validate_url(self.link.get()):
            return
        return True

    def save_record(self):

        if not self.validation():
            return

        cur = self.parent.con.cursor()
        try:
            if self.id_record:
                cur.execute(
                    "update prices set id_item=?, item=?, price=?, time=?, link=?, information=? where id_record=?",
                    (
                        self.id_item.get().strip(),
                        self.item.get(),
                        self.price.get().strip(),
                        self.time.get().strip(),
                        self.link.get(),
                        self.information.get(),
                        self.id_record,
                    ),
                )
            else:
                cur.execute(
                    "insert into prices (id_item, item, price, time, link, information) "
                    + "values (?, ? ,? , ? , ?, ?)",
                    (
                        self.id_item.get().strip(),
                        self.item.get(),
                        self.price.get().strip(),
                        self.time.get().strip(),
                        self.link.get(),
                        self.information.get(),
                    ),
                )
        except sqlite3.DatabaseError as err:
            ct.messagebox.showerror(
                self.parent.app_title,
                "При сохранении записи возникла ошибка: " + str(err),
                parent=self,
            )
        else:
            self.parent.con.commit()
            self.parent.load_data()
            self.destroy()


class Recordtop(ct.CTkToplevel):
    def __init__(self, parent=None, record={}):
        super().__init__()
        self.parent = parent
        self.create_widgets(record)
        self.title("Изменение записи" if record["id_item"] else "Добавление записи")
        self.resizable(False, False)
        self.transient(parent)
        self.focus_set()
        self.grab_set()

    def create_widgets(self, record):
        self.entry_menu = CustomEntry(self)

        grid_params = {"padx": 10, "pady": 6}

        self.id_item = record["id_item"]
        self.item = ct.StringVar()
        self.item.set(record["item"])
        self.time = ct.StringVar()
        self.time.set(record["time"])
        self.link = ct.StringVar()
        self.link.set(record["link"])

        frame = ct.CTkFrame(self, corner_radius=10, bg_color="#f0f0f0")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.id_item = record.get("id_item", "")
        self.item = ct.StringVar(value=record.get("item", ""))
        lblitem = ct.CTkLabel(frame, text="Товар")
        lblitem.grid(row=0, column=0, **grid_params)
        self.entitem = ct.CTkEntry(frame, textvariable=self.item, width=600)
        self.entitem.grid(row=0, column=1, sticky="we", **grid_params)

        self.time = ct.StringVar(value=record.get("time", ""))
        lbltime = ct.CTkLabel(frame, text="Время")
        lbltime.grid(row=1, column=0, **grid_params)
        self.enttime = ct.CTkEntry(frame, textvariable=self.time, width=600)
        self.enttime.grid(row=1, column=1, sticky="we", **grid_params)

        self.link = ct.StringVar(value=record.get("link", ""))
        lbllink = ct.CTkLabel(frame, text="Ссылка")
        lbllink.grid(row=2, column=0, **grid_params)
        self.entlink = ct.CTkEntry(frame, textvariable=self.link, width=600)
        self.entlink.grid(row=2, column=1, sticky="we", **grid_params)

        for entry in [self.entitem, self.enttime, self.entlink]:
            entry.bind(
                "<Button-3>",
                lambda event, widget=entry: self.entry_menu.show(event, widget),
            )
            entry.bind("<Control-KeyPress>", lambda event: self.entry_menu.keys(event))

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=3, column=0, sticky="e", **grid_params)
        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=3, column=1, sticky="e", **grid_params)

        self.bind_all("<Alt-KeyPress-b>", lambda evt: self.entitem.focus_set())
        self.bind_all("<Alt-KeyPress-y>", lambda evt: self.enttime.focus_set())
        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.bind("<Map>", self.place)

    def place(self, evt):
        self.update_idletasks()

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)

        self.geometry(f"+{x}+{y}")

    def validation(self):
        if not Validators.validate_item(self.item.get()):
            return
        if not Validators.validate_url(self.link.get()):
            return
        if not Validators.validate_time(self.time.get()):
            return
        return True

    def save_record(self):

        if not self.validation():
            return

        self.parent.show_activity()
        save_thread = threading.Thread(target=self.save_record_logic)
        save_thread.start()
        self.destroy()

    def save_record_logic(self):
        db_path = DBPath.get_or_init_db_path()

        if not self.id_item:
            if "flip" in self.link.get():
                item, information, price = extract_product_info(self.link.get())

            elif "technodom" in self.link.get():
                item, information, price = extract_product_info(self.link.get())

            elif "kaspi" in self.link.get():
                result = extract_product_info(self.link.get())
                if result is None:
                    tkinter.messagebox.showerror(
                        title="Ошибка загрузки данных",
                        message="Не удалось получить данные с kaspi.",
                    )
                    self.parent.after(0, self.parent.hide_activity)
                    return
                if result[0] == "skip":
                    tkinter.messagebox.showerror(
                        title="Товара нет в наличии",
                        message=f"Не найдена цена на товар.",
                    )
                    self.parent.grab_set()
                    self.parent.after(0, self.parent.hide_activity)
                    return
                if result[0] == "second_check":
                    tkinter.messagebox.showerror(
                        title="Недостаточно отзывов",
                        message=f"Не найдено предложений с количеством отзывов больше {min_reviews_count}. Товар добавлен с минимальной ценой.",
                    )
                    self.parent.grab_set()
                    item, information, price = result[1], result[2], result[3]

                if result[0] != "second_check":
                    item, information, price = result

            elif "ozon" in self.link.get():
                result = extract_product_info(self.link.get())
                if result is None:
                    tkinter.messagebox.showerror(
                        title="Ошибка загрузки данных",
                        message="Не удалось получить данные с ozon.",
                    )
                    self.parent.after(0, self.parent.hide_activity)
                    return

                elif result == "webOutOfStock":
                    item, information, price = (
                        "Товара нет в наличии",
                        "Информации нет",
                        0,
                    )
                else:
                    item, information, price = result

            else:
                tkinter.messagebox.showerror(
                    "Ошибка", f"Неизвестный магазин: {self.link.get()}"
                )
                return
        try:
            # Получаем доступ к базе данных в отдельном потоке
            with sqlite3.connect(db_path) as con:
                cur = con.cursor()
                if self.id_item:
                    cur.execute(
                        "update items set item=?, time=?, link=? where id_item=?",
                        (
                            self.item.get(),
                            self.time.get().strip(),
                            self.link.get(),
                            self.id_item,
                        ),
                    )
                else:
                    cur.execute(
                        "insert into items (item, time, link) " + "values (?, ? ,? )",
                        (self.item.get(), self.time.get().strip(), self.link.get()),
                    )
                    id_item = str(cur.lastrowid)
                    cur.execute(
                        "insert into prices (id_item, item, price, time, link, information) "
                        + "values (?, ? ,? , ? , ?, ?)",
                        (
                            id_item,
                            self.item.get(),
                            price,
                            self.time.get().strip(),
                            self.link.get(),
                            information,
                        ),
                    )
        except sqlite3.DatabaseError as err:
            # Ошибка обновления UI должна выполняться в основном потоке
            self.parent.after(
                0,
                lambda: ct.messagebox.showerror(
                    self.parent.app_title,
                    "При сохранении записи возникла ошибка: " + str(err),
                ),
            )
        else:
            # Подтверждение изменений и обновление данных в UI в основном потоке
            self.parent.after(0, self.parent.load_data)
        finally:
            # Скрытие индикатора активности вне зависимости от результата операции
            self.parent.after(0, self.parent.hide_activity)


class Recordlink(ct.CTkToplevel):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.create_widgets()
        self.title("Добавление товара")
        self.resizable(False, False)
        self.transient(parent)
        self.focus_set()
        self.grab_set()

    def create_widgets(self):
        self.entry_menu = CustomEntry(self)

        grid_params = {"padx": 10, "pady": 6}

        frame = ct.CTkFrame(self, corner_radius=10, bg_color="#f0f0f0")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.link = ct.StringVar()
        self.link.set("")

        lbllink = ct.CTkLabel(frame, text="Ссылка")
        lbllink.grid(row=0, column=0, **grid_params)
        self.entlink = ct.CTkEntry(frame, textvariable=self.link, width=600)
        self.entlink.grid(row=0, column=1, sticky="we", **grid_params)

        self.entlink.bind(
            "<Button-3>",
            lambda event, widget=self.entlink: self.entry_menu.show(event, widget),
        )
        self.entlink.bind(
            "<Control-KeyPress>", lambda event: self.entry_menu.keys(event)
        )

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=1, column=0, sticky="e", **grid_params)

        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=1, column=1, sticky="e", **grid_params)

        self.bind_all("<Alt-KeyPress-b>", lambda evt: self.entitem.focus_set())
        self.bind_all("<Alt-KeyPress-y>", lambda evt: self.enttime.focus_set())
        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.bind("<Map>", self.place)

    def place(self, evt):
        self.update_idletasks()

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)

        self.geometry(f"+{x}+{y}")

    def save_record(self):

        if not Validators.validate_url(self.link.get()):
            return

        self.parent.show_activity()
        save_thread = threading.Thread(target=self.save_record_logic)
        save_thread.start()
        self.destroy()

    def save_record_logic(self):
        db_path = DBPath.get_or_init_db_path()

        if "flip" in self.link.get():
            item, information, price = extract_product_info(self.link.get())

        elif "technodom" in self.link.get():
            item, information, price = extract_product_info(self.link.get())

        elif "kaspi" in self.link.get():
            result = extract_product_info(self.link.get())
            if result is None:
                tkinter.messagebox.showerror(
                    title="Ошибка загрузки данных",
                    message="Не удалось получить данные с kaspi.",
                )
                self.parent.after(0, self.parent.hide_activity)
                return
            if result[0] == "skip":
                tkinter.messagebox.showerror(
                    title="Товара нет в наличии",
                    message=f"Не найдена цена на товар.",
                )
                self.parent.grab_set()
                self.parent.after(0, self.parent.hide_activity)
                return
            if result[0] == "second_check":
                tkinter.messagebox.showerror(
                    title="Недостаточно отзывов",
                    message=f"Не найдено предложений с количеством отзывов больше {min_reviews_count}. Товар добавлен с минимальной ценой.",
                )
                self.parent.grab_set()
                item, information, price = result[1], result[2], result[3]

            if result[0] != "second_check":
                item, information, price = result

        elif "ozon" in self.link.get():
            result = extract_product_info(self.link.get())
            if result is None:
                tkinter.messagebox.showerror(
                    title="Ошибка загрузки данных",
                    message="Не удалось получить данные с ozon.",
                )
                self.parent.after(0, self.parent.hide_activity)
                return
            elif result == "webOutOfStock":
                item, information, price = "Товара нет в наличии", "Информации нет", 0
            else:
                item, information, price = result
        else:
            tkinter.messagebox.showerror(
                "Ошибка", f"Неизвестный магазин: {self.link.get()}"
            )
            return

        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        try:
            with sqlite3.connect(db_path) as con:
                cur = con.cursor()
                cur.execute(
                    "insert into items (item, time, link) " + "values (?, ? , ? )",
                    (item, now, self.link.get()),
                )
                id_item = str(
                    cur.execute(
                        f"select id_item from items WHERE time = '{now}'"
                    ).fetchone()[0]
                )

                cur.execute(
                    "insert into prices (id_item, item, price, time, link, information) "
                    + "values (?, ? ,? , ? , ?, ?)",
                    (id_item, item, price, now, self.link.get(), information),
                )

        except sqlite3.DatabaseError as err:
            # Для обновления интерфейса из фонового потока используйте self.after
            self.after(
                0,
                lambda: ct.messagebox.showerror(
                    self.parent.app_title,
                    "При сохранении записи возникла ошибка: " + str(err),
                    parent=self,
                ),
            )
        else:
            self.after(0, self.parent.load_data)
        self.parent.after(0, self.parent.hide_activity)
