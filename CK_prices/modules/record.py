import ctypes
import os
import sys
import customtkinter as ct
import tkinter
import threading
import sqlite3
import requests
from bs4 import BeautifulSoup as BS
from datetime import datetime
from modules.kaspidriver import setup_driver_kaspi
from modules.ozondriver import setup_driver_ozon


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

    def create_widgets(self, record):
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

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=6, column=0, sticky="e", **grid_params)
        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=6, column=1, sticky="e", **grid_params)

        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.entid_item.bind("<Control-KeyPress>", self.keys)
        self.entitem.bind("<Control-KeyPress>", self.keys)
        self.entprice.bind("<Control-KeyPress>", self.keys)
        self.enttime.bind("<Control-KeyPress>", self.keys)
        self.entlink.bind("<Control-KeyPress>", self.keys)
        self.entinformation.bind("<Control-KeyPress>", self.keys)

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
        cur = self.parent.con.cursor()
        try:
            if self.id_record:
                cur.execute(
                    "update prices set id_item=?, item=?, price=?, time=?, link=?, information=? where id_record=?",
                    (
                        self.id_item.get(),
                        self.item.get(),
                        self.price.get(),
                        self.time.get(),
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
                        self.id_item.get(),
                        self.item.get(),
                        self.price.get(),
                        self.time.get(),
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

    def create_widgets(self, record):
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

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=3, column=0, sticky="e", **grid_params)
        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=3, column=1, sticky="e", **grid_params)

        self.bind_all("<Alt-KeyPress-b>", lambda evt: self.entitem.focus_set())
        self.bind_all("<Alt-KeyPress-y>", lambda evt: self.enttime.focus_set())
        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.entitem.bind("<Control-KeyPress>", self.keys)
        self.enttime.bind("<Control-KeyPress>", self.keys)
        self.entlink.bind("<Control-KeyPress>", self.keys)

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
        self.parent.show_activity()
        save_thread = threading.Thread(target=self.save_record_logic)
        save_thread.start()
        self.destroy()

    def save_record_logic(self):
        if getattr(sys, "frozen", False):
            dir_path = sys._MEIPASS
        else:
            dir_path = os.path.dirname(os.path.abspath(__file__))

        db_dir = os.path.join(dir_path, "data")

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        db_path = os.path.join(db_dir, "tab.db")
        if not self.id_item:
            if "flip" in self.link.get():
                r = requests.get(self.link.get())
                html = BS(r.content, "html.parser")
                try:
                    information = html.find("span", itemprop="description").text
                except:
                    information = "Информации нет"
                try:
                    meta_tag = html.find("meta", {"itemprop": "price"})
                    price = int(meta_tag["content"])
                except:
                    try:
                        price = html.find("span", class_="text_att").text
                        price = price.replace("₸", "")  # remove space and "₸" symbol
                        price = int(price)
                    except:
                        price = 0
                        information = "Товара нет в наличии"

            elif "technodom" in self.link.get():
                r = requests.get(self.link.get())
                html = BS(r.content, "html.parser")
                information = (
                    "Для дополнительной информации перейдите на страницу товара"
                )
                try:
                    price = html.find("p", class_="Typography__Heading_H1").text
                    price = price.replace("₸", "")  # remove space and "₸" symbol
                    price = int(price)
                    print(price)
                except:
                    price = 0
                    information = "Товара нет в наличии"

            elif "kaspi" in self.link.get():
                html = setup_driver_kaspi(self.link.get())

                soup = BS(html, "html.parser")

                try:
                    price_text = soup.find(
                        "div", class_="item__price-once"
                    ).text.strip()
                    price = int("".join(filter(str.isdigit, price_text)))
                except:
                    price = 0
                    self.item = "Товара нет в наличии"

                try:
                    description = soup.find("div", class_="item__description-text")
                    description_items = description.find_all("li")
                    information = " / ".join(
                        item.get_text().strip() for item in description_items
                    )
                except:
                    information = "Информации нет"

            elif "ozon" in self.link.get():
                html = setup_driver_ozon(self.link.get())

                soup = BS(html, "html.parser")
                try:
                    price_block = soup.find("div", class_="lo2")
                    price_text = price_block.get_text().strip()
                    price_text = price_text.split("₸")[0]
                    price = int("".join(filter(str.isdigit, price_text)))
                except:
                    price = 0
                    self.item = "Товара нет в наличии"
                try:
                    description_block = soup.find("div", class_="RA-a1")
                    information = description_block.get_text().strip()
                except:
                    information = "Информации нет"

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
                            self.time.get(),
                            self.link.get(),
                            self.id_item,
                        ),
                    )
                else:
                    cur.execute(
                        "insert into items (item, time, link) " + "values (?, ? ,? )",
                        (self.item.get(), self.time.get(), self.link.get()),
                    )
                    id_item = str(cur.lastrowid)
                    cur.execute(
                        "insert into prices (id_item, item, price, time, link, information) "
                        + "values (?, ? ,? , ? , ?, ?)",
                        (
                            id_item,
                            self.item.get(),
                            price,
                            self.time.get(),
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

    def create_widgets(self):
        grid_params = {"padx": 10, "pady": 6}

        frame = ct.CTkFrame(self, corner_radius=10, bg_color="#f0f0f0")
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        self.link = ct.StringVar()
        self.link.set("")

        lbllink = ct.CTkLabel(frame, text="Ссылка")
        lbllink.grid(row=0, column=0, **grid_params)
        self.entlink = ct.CTkEntry(frame, textvariable=self.link, width=600)
        self.entlink.grid(row=0, column=1, sticky="we", **grid_params)

        self.btnOK = ct.CTkButton(frame, text="ОК", command=self.save_record)
        self.btnOK.grid(row=1, column=0, sticky="e", **grid_params)

        self.btnCancel = ct.CTkButton(frame, text="Отмена", command=self.destroy)
        self.btnCancel.grid(row=1, column=1, sticky="e", **grid_params)

        self.bind_all("<Alt-KeyPress-b>", lambda evt: self.entitem.focus_set())
        self.bind_all("<Alt-KeyPress-y>", lambda evt: self.enttime.focus_set())
        self.bind_all("<KeyPress-Return>", lambda evt: self.btnOK.invoke())
        self.bind_all("<KeyPress-Escape>", lambda evt: self.btnCancel.invoke())

        self.entlink.bind("<Control-KeyPress>", self.keys)

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
        self.parent.show_activity()
        save_thread = threading.Thread(target=self.save_record_logic)
        save_thread.start()
        self.destroy()

    def save_record_logic(self):
        if getattr(sys, "frozen", False):
            dir_path = sys._MEIPASS
        else:
            dir_path = os.path.dirname(os.path.abspath(__file__))

        db_dir = os.path.join(dir_path, "data")

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        db_path = os.path.join(db_dir, "tab.db")
        if "flip" in self.link.get():
            r = requests.get(self.link.get())
            html = BS(r.content, "html.parser")
            item = html.find("h1").text
            try:
                information = html.find("span", itemprop="description").text
            except:
                information = "Информации нет"
            try:
                meta_tag = html.find("meta", {"itemprop": "price"})
                price = int(meta_tag["content"])
            except:
                try:
                    price = html.find("span", class_="text_att").text
                    price = price.replace("₸", "")  # remove space and "₸" symbol
                    price = int(price)
                except:
                    price = 0
                    information = "Товара нет в наличии"

        elif "technodom" in self.link.get():
            r = requests.get(self.link.get())
            html = BS(r.content, "html.parser")
            item = html.find("h1").text
            information = "Для дополнительной информации перейдите на страницу товара"
            try:
                price = html.find("p", class_="Typography__Heading_H1").text
                price = price.replace("₸", "")  # remove space and "₸" symbol
                price = int(price)
            except:
                price = 0
                information = "Товара нет в наличии"

        elif "kaspi" in self.link.get():
            html = setup_driver_kaspi(self.link.get())

            soup = BS(html, "html.parser")
            try:
                item = soup.find("h1", class_="item__heading").text.strip()
            except:
                item = "Информации нет"
            try:
                price_text = soup.find("div", class_="item__price-once").text.strip()
                price = int("".join(filter(str.isdigit, price_text)))
            except:
                price = 0
                item = "Товара нет в наличии"
            try:
                description = soup.find("div", class_="item__description-text")
                description_items = description.find_all("li")
                information = " / ".join(
                    item.get_text().strip() for item in description_items
                )
            except:
                information = "Информации нет"

        elif "ozon" in self.link.get():
            html = setup_driver_ozon(self.link.get())

            soup = BS(html, "html.parser")
            try:
                item = soup.find(attrs={"data-widget": "webProductHeading"})
                item = item.get_text().strip()
            except:
                item = "Информации нет"
            try:
                price_block = soup.find("div", class_="lo2")
                price_text = price_block.get_text().strip()
                price_text = price_text.split("₸")[0]
                price = int("".join(filter(str.isdigit, price_text)))
            except:
                price = 0
                item = "Товара нет в наличии"
            try:
                description_block = soup.find("div", class_="RA-a1")
                information = description_block.get_text().strip()
            except:
                information = "Информации нет"
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
