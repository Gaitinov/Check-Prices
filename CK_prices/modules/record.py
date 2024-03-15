import customtkinter as ct
import tkinter
import sqlite3
import requests
from bs4 import BeautifulSoup as BS
from datetime import datetime
import time
from modules.driver import setup_driver

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
        grid_params = {"padx": 4, "pady": 4}

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

        lblid_item = ct.CTkLabel(self, text="id_item")
        lblid_item.grid(row=0, column=0, **grid_params)
        self.entid_item = ct.CTkEntry(self, textvariable=self.id_item)
        self.entid_item.grid(row=0, column=1, sticky="w", **grid_params)

        lblitem = ct.CTkLabel(self, text="Товар")
        lblitem.grid(row=1, column=0, **grid_params)
        self.entitem = ct.CTkEntry(self, textvariable=self.item)
        self.entitem.grid(row=1, column=1, sticky="w", **grid_params)

        lblprice = ct.CTkLabel(self, text="Цена")
        lblprice.grid(row=2, column=0, **grid_params)
        self.entprice = ct.CTkEntry(self, textvariable=self.price)
        self.entprice.grid(row=2, column=1, sticky="w", **grid_params)

        lbltime = ct.CTkLabel(self, text="Время")
        lbltime.grid(row=3, column=0, **grid_params)
        self.enttime = ct.CTkEntry(self, textvariable=self.time)
        self.enttime.grid(row=3, column=1, sticky="w", **grid_params)

        lbllink = ct.CTkLabel(self, text="Ссылка")
        lbllink.grid(row=4, column=0, **grid_params)
        self.entlink = ct.CTkEntry(self, textvariable=self.link)
        self.entlink.grid(row=4, column=1, sticky="w", **grid_params)

        lblinformation = ct.CTkLabel(self, text="Информация")
        lblinformation.grid(row=5, column=0, **grid_params)
        self.entinformation = ct.CTkEntry(self, textvariable=self.information)
        self.entinformation.grid(row=5, column=1, sticky="w", **grid_params)

        self.btnOK = ct.CTkButton(self, text="ОК", command=self.save_record)
        self.btnOK.grid(row=6, column=0, sticky="e", **grid_params)

        self.btnCancel = ct.CTkButton(self, text="Отмена",
                                      command=self.destroy)
        self.btnCancel.grid(row=6, column=1, sticky="e", **grid_params)

        self.bind_all("<Alt-KeyPress-b>", lambda evt: self.entFIO.focus_set())
        self.bind_all("<Alt-KeyPress-y>", lambda evt: self.entBirth.focus_set())
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
        cur = self.parent.con.cursor()
        try:
            if self.id_record:
                cur.execute(
                    "update prices set id_item=?, item=?, price=?, time=?, link=?, information=? where id_record=?",
                    (self.id_item.get(), self.item.get(), self.price.get(), self.time.get(), self.link.get(),
                     self.information.get(), self.id_record))
            else:
                cur.execute("insert into prices (id_item, item, price, time, link, information) " + \
                            "values (?, ? ,? , ? , ?, ?)",
                            (self.id_item.get(), self.item.get(), self.price.get(), self.time.get(), self.link.get(),
                             self.information.get()))
        except sqlite3.DatabaseError as err:
            ct.messagebox.showerror(self.parent.app_title,
                                    "При сохранении записи возникла ошибка: " + str(err),
                                    parent=self)
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
        grid_params = {"padx": 4, "pady": 4}

        self.id_item = record["id_item"]
        self.item = ct.StringVar()
        self.item.set(record["item"])
        self.time = ct.StringVar()
        self.time.set(record["time"])
        self.link = ct.StringVar()
        self.link.set(record["link"])

        lblitem = ct.CTkLabel(self, text="Товар")
        lblitem.grid(row=0, column=0, **grid_params)
        self.entitem = ct.CTkEntry(self, textvariable=self.item)
        self.entitem.grid(row=0, column=1, sticky="w", **grid_params)

        lbltime = ct.CTkLabel(self, text="Время")
        lbltime.grid(row=1, column=0, **grid_params)
        self.enttime = ct.CTkEntry(self, textvariable=self.time)
        self.enttime.grid(row=1, column=1, sticky="w", **grid_params)

        lbllink = ct.CTkLabel(self, text="Ссылка")
        lbllink.grid(row=2, column=0, **grid_params)
        self.entlink = ct.CTkEntry(self, textvariable=self.link)
        self.entlink.grid(row=2, column=1, sticky="w", **grid_params)

        self.btnOK = ct.CTkButton(self, text="ОК", command=self.save_record)
        self.btnOK.grid(row=5, column=0, sticky="e", **grid_params)

        self.btnCancel = ct.CTkButton(self, text="Отмена",
                                      command=self.destroy)
        self.btnCancel.grid(row=5, column=1, sticky="e", **grid_params)

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
        cur = self.parent.con.cursor()
        if "flip" in self.link.get():
            r = requests.get(self.link.get())
            html = BS(r.content, "html.parser")
            try:
                information = html.find("span", itemprop="description").text
            except:
                information = "Информации нет"
            try:
                meta_tag = html.find('meta', {'itemprop': 'price'})
                price = int(meta_tag['content'])
            except:
                try:
                    price = html.find("span", class_="text_att").text
                    price = price.replace('₸', '')  # remove space and "₸" symbol
                    price = int(price)
                except:
                    price = 0
                    information = "Товара нет в наличии"

        elif "technodom" in self.link.get():
            r = requests.get(self.link.get())
            html = BS(r.content, "html.parser")
            information = "Для дополнительной информации перейдите на страницу товара"
            try:
                price = html.find('p', class_='Typography__Heading_H1').text
                price = price.replace('₸', '')  # remove space and "₸" symbol
                price = int(price)
                print(price)
            except:
                price = 0
                information = "Товара нет в наличии"


        elif "kaspi" in self.link.get():
            from modules.driver import setup_driver
            driver = setup_driver()
            driver.get(self.link.get())
            time.sleep(5)
            html = driver.page_source
            driver.quit()
            soup = BS(html, 'html.parser')

            try:
                price_text = soup.find('div', class_='item__price-once').text.strip()
                price = int(''.join(filter(str.isdigit, price_text)))
            except:
                price = 0
                self.item = "Товара нет в наличии"

            try:
                description = soup.find('div', class_='item__description-text')
                description_items = description.find_all('li')
                information = ' / '.join(item.get_text().strip() for item in description_items)
            except:
                information = "Информации нет"


        else:
            tkinter.messagebox.showerror("Ошибка", f"Неизвестный магазин: {self.link.get()}")
            return
        try:
            if self.id_item:
                cur.execute("update items set item=?, time=?, link=? where id_item=?",
                            (self.item.get(), self.time.get(), self.link.get(), self.id_item))
            else:
                cur.execute("insert into items (item, time, link) " + \
                            "values (?, ? ,? )",
                            (self.item.get(), self.time.get(), self.link.get()))

                id_item = str(cur.execute(f"select id_item from items WHERE time = '{self.time.get()}'").fetchone()[0])

                cur.execute("insert into prices (id_item, item, price, time, link, information) " + \
                            "values (?, ? ,? , ? , ?, ?)",
                            (id_item, self.item.get(), price, self.time.get(), self.link.get(), information))

        except sqlite3.DatabaseError as err:
            ct.messagebox.showerror(self.parent.app_title,
                                    "При сохранении записи возникла ошибка: " + str(err),
                                    parent=self)
        else:
            self.parent.con.commit()
            self.parent.load_data()
            self.destroy()


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
        grid_params = {"padx": 4, "pady": 4}

        self.link = ct.StringVar()
        self.link.set("")

        lbllink = ct.CTkLabel(self, text="Ссылка")
        lbllink.grid(row=0, column=0, **grid_params)
        self.entlink = ct.CTkEntry(self, textvariable=self.link)
        self.entlink.grid(row=0, column=1, sticky="w", **grid_params)

        self.btnOK = ct.CTkButton(self, text="ОК", command=self.save_record)
        self.btnOK.grid(row=1, column=0, sticky="e", **grid_params)

        self.btnCancel = ct.CTkButton(self, text="Отмена",
                                      command=self.destroy)
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
        if "flip" in self.link.get():
            r = requests.get(self.link.get())
            html = BS(r.content, "html.parser")
            item = html.find("h1").text
            try:
                information = html.find("span", itemprop="description").text
            except:
                information = "Информации нет"
            try:
                meta_tag = html.find('meta', {'itemprop': 'price'})
                price = int(meta_tag['content'])
            except:
                try:
                    price = html.find("span", class_="text_att").text
                    price = price.replace('₸', '')  # remove space and "₸" symbol
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
                price = html.find('p', class_='Typography__Heading_H1').text
                price = price.replace('₸', '')  # remove space and "₸" symbol
                price = int(price)
            except:
                price = 0
                information = "Товара нет в наличии"

        elif "kaspi" in self.link.get():
            html = setup_driver(self.link.get())

            soup = BS(html, 'html.parser')
            try:
                item = soup.find('h1', class_='item__heading').text.strip()
            except:
                item = "Информации нет"
            try:
                price_text = soup.find('div', class_='item__price-once').text.strip()
                price = int(''.join(filter(str.isdigit, price_text)))
            except:
                price = 0
                item = "Товара нет в наличии"
            try:
                description = soup.find('div', class_='item__description-text')
                description_items = description.find_all('li')
                information = ' / '.join(item.get_text().strip() for item in description_items)
            except:
                information = "Информации нет"
        else:
            tkinter.messagebox.showerror("Ошибка", f"Неизвестный магазин: {self.link.get()}")
            return

        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        cur = self.parent.con.cursor()
        try:
            cur.execute("insert into items (item, time, link) " +
                        "values (?, ? , ? )",
                        (item, now, self.link.get()))
            id_item = str(cur.execute(f"select id_item from items WHERE time = '{now}'").fetchone()[0])

            cur.execute("insert into prices (id_item, item, price, time, link, information) " +
                        "values (?, ? ,? , ? , ?, ?)",
                        (id_item, item, price, now, self.link.get(), information))

        except sqlite3.DatabaseError as err:
            ct.messagebox.showerror(self.parent.app_title,
                                    "При сохранении записи возникла ошибка: " + str(err),
                                    parent=self)
        else:
            self.parent.con.commit()
            self.parent.load_data()
            self.destroy()
