import ctypes
import tkinter
import tkinter.ttk
import logging
import tkinter.messagebox
import customtkinter as ct
import sqlite3
import sys
import requests
import webbrowser
import os
import configparser
import plotly.graph_objects as go
from pystray import MenuItem as item
import pystray
import threading
from PIL import Image
from datetime import datetime
from bs4 import BeautifulSoup as BS
from modules.record import Record
from modules.record import Recordtop
from modules.record import Recordlink
from modules.kaspidriver import setup_driver_kaspi
from modules.ozondriver import setup_driver_ozon
from modules.update import update
from modules.settings import Settings


config = configparser.ConfigParser()
config.read("settings.ini")

check_price_interval = config.getint("DEFAULT", "check_price_interval")
price_range_for_save_to_db = config.getint("DEFAULT", "price_range_for_save_to_db")
min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


class Application(tkinter.Tk):
    app_title = "Учёт цен"
    schprocess = None
    stop_event = None

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

    def __init__(self):
        super().__init__()

        # Настройка логирования
        logging.basicConfig(
            filename="app.log",
            filemode="w",
            format="%(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        logging.info("Логирование началось самый старт")

        try:
            if getattr(sys, "frozen", False):
                dir_path = sys._MEIPASS
            else:
                dir_path = os.path.dirname(os.path.abspath(__file__))

            db_dir = os.path.join(dir_path, "data")

            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            db_path = os.path.join(db_dir, "tab.db")

            self.countter = 0
            self.con = sqlite3.connect(db_path)
            self.create_widgets()
            self.title(Application.app_title)
            self.iconbitmap(r"images/icon.ico")

            # Добавляем эти строки для центрирования окна и вывода его поверх других
            self.update_idletasks()  # Обновление состояния окна
            window_width = self.winfo_reqwidth()
            window_height = self.winfo_reqheight()
            position_right = int(self.winfo_screenwidth() / 2 - window_width / 2)
            position_down = int(self.winfo_screenheight() / 2 - window_height / 2)
            self.geometry(
                f"{window_width}x{window_height}+{position_right}+{position_down}"
            )
            self.attributes("-topmost", True)  # Поверх всех окон
            self.after_idle(
                self.attributes, "-topmost", False
            )  # Затем возвращаем обычный режим

            self.protocol("WM_DELETE_WINDOW", self.exitstray)
            self.mainloop()
            logging.info("Логирование началось init")  # Запись по умолчанию
        except Exception as e:
            logging.error("Произошла ошибка: %s", e)

    def sch(self):
        try:
            logging.info("Запущен поток")
            print("Запущен поток")
            threadupdate = None
            while not self.stop_event.is_set():
                self.stop_event.wait(check_price_interval)
                if self.stop_event.is_set():
                    logging.info("Поток break")
                    print("Поток break")
                    break

                if threadupdate is None or not threadupdate.is_alive():
                    threadupdate = threading.Thread(target=update)
                    threadupdate.daemon = True
                    threadupdate.start()

            logging.info("Логирование началось (поток)")  # Запись по умолчанию
        except Exception as e:
            logging.error("Произошла ошибка: %s", e)

    def exitstray(self):
        logging.info("Логирование началось: свернуто")

        def action():
            try:
                logging.info("Поток остановлен")
                print("Поток остановлен")
                self.stop_event.set()
                self.deiconify()
                self.icon.stop()
                self.load_data()
                self.lift()  # Поднимаем окно на передний план
                self.focus_force()  # Принудительно устанавливаем фокус на окне
                logging.info("Логирование началось разворачивание")
            except Exception as e:
                logging.error("Произошла ошибка: %s", e)

        def exitall(icon, item):
            os._exit(0)

        try:
            if self.schprocess is None or not self.schprocess.is_alive():
                self.stop_event = threading.Event()
                self.schprocess = threading.Thread(target=self.sch)
                self.schprocess.start()
            logging.info("Логирование началось tray основа")
            self.withdraw()
            image = Image.open("images/icon.ico")
            self.icon = pystray.Icon(
                "name",
                image,
                "Check price",
                menu=pystray.Menu(item("Развернуть", action), item("Выйти", exitall)),
            )
            self.icon.run()
        except Exception as e:
            logging.error("Произошла ошибка: %s", e)

    def create_widgets(self):
        self.add_image = tkinter.PhotoImage(file=r"images/add.gif")
        self.edit_image = tkinter.PhotoImage(file=r"images/edit.gif")
        self.graph_image = tkinter.PhotoImage(file=r"images/graph.png")
        self.delete_image = tkinter.PhotoImage(file=r"images/delete.gif")
        self.search_image = tkinter.PhotoImage(file=r"images/search.gif")
        mainmenu = tkinter.Menu(self)
        self["menu"] = mainmenu

        self.editmenu = tkinter.Menu(mainmenu, tearoff=False)
        self.editmenu.add_command(
            label="Добавить",
            accelerator="Ins",
            image=self.add_image,
            compound=tkinter.LEFT,
            command=self.add_record,
        )
        self.editmenu.add_command(
            label="Изменить",
            accelerator="F2",
            image=self.edit_image,
            compound=tkinter.LEFT,
            command=self.edit_record,
        )
        self.editmenu.add_command(
            label="Создать график",
            accelerator="F5",
            image=self.graph_image,
            compound=tkinter.LEFT,
            command=self.create_graph,
        )
        self.editmenu.add_separator()
        self.editmenu.add_command(
            label="Удалить",
            accelerator="F8",
            image=self.delete_image,
            compound=tkinter.LEFT,
            command=self.delete_record,
        )
        mainmenu.add_cascade(label="Правка", menu=self.editmenu)

        helpmenu = tkinter.Menu(mainmenu, tearoff=False)
        helpmenu.add_command(label="О программе...", command=self.show_info)
        mainmenu.add_cascade(label="Справка", menu=helpmenu)
        mainmenu.add_command(label="Настройки", command=self.open_settings)

        self.search = tkinter.StringVar()
        self.search.set("")

        frm = tkinter.ttk.Frame(self)
        entSearch = ct.CTkEntry(frm, textvariable=self.search)
        entSearch.grid(row=0, column=0, sticky="we")
        btnSearch = tkinter.ttk.Button(
            frm, image=self.search_image, command=self.load_data
        )
        btnSearch.grid(row=0, column=1)
        frm.grid_columnconfigure(0, weight=1)
        frm.grid(row=0, column=0, columnspan=2, sticky="we")

        self.trwPB = tkinter.ttk.Treeview(
            self,
            columns=("id_item", "item", "price", "time", "link", "information"),
            displaycolumns="#all",
            show="headings",
        )
        self.trwPB.column("id_item", minwidth=100)
        self.trwPB.column("item", minwidth=100)
        self.trwPB.column("price", minwidth=100)
        self.trwPB.column("time", minwidth=100)
        self.trwPB.column("link", minwidth=100)
        self.trwPB.column("information", minwidth=100)

        self.trwPB.heading("id_item", text="id_item")
        self.trwPB.heading("item", text="Товар")
        self.trwPB.heading("price", text="Цена")
        self.trwPB.heading("time", text="Время")
        self.trwPB.heading("link", text="Ссылка")
        self.trwPB.heading("information", text="Информация")

        self.trwPB.grid(row=1, column=0, sticky="wnes")
        hs = tkinter.ttk.Scrollbar(
            self, orient=tkinter.HORIZONTAL, command=self.trwPB.xview
        )
        hs.grid(row=2, column=0, sticky="we")
        vs = tkinter.ttk.Scrollbar(self, command=self.trwPB.yview)
        vs.grid(row=1, column=1, sticky="ns")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        sgp = tkinter.ttk.Sizegrip(self)
        sgp.grid(row=2, column=1, sticky="ns")

        self.bind_all("<KeyPress-Insert>", lambda evt: self.editmenu.invoke(0))
        self.bind_all("<KeyPress-F2>", lambda evt: self.editmenu.invoke(1))
        self.bind_all("<KeyPress-F5>", lambda evt: self.editmenu.invoke(2))
        self.bind_all("<KeyPress-F8>", lambda evt: self.editmenu.invoke(4))

        self.bind("<Destroy>", self.cleanup)

        self.trwPB.bind("<Double-1>", self.on_double_click)

        entSearch.bind("<Control-KeyPress>", self.keys)

        self.update_button = ct.CTkButton(
            frm, text="Проверить данные", command=self.update
        )
        self.update_button.grid(row=0, column=3, padx=20, pady=5)

        button = ct.CTkButton(frm, text="Товары", command=self.newwindow)
        button.grid(row=0, column=4, padx=20, pady=5)

        context_menu = tkinter.Menu(self, tearoff=0)
        context_menu.add_command(label="Создать график", command=self.create_graph)
        context_menu.add_command(label="Добавить", command=self.add_record)
        context_menu.add_command(label="Изменить", command=self.edit_record)
        context_menu.add_command(label="Удалить", command=self.delete_record)

        def show_context_menu(event):
            row_id = self.trwPB.identify_row(event.y)
            self.trwPB.selection_set(row_id)
            context_menu.post(event.x_root, event.y_root)

        self.trwPB.bind("<Button-3>", show_context_menu)

        self.load_data()

    def on_double_click(self, event):
        r = self.trwPB.focus()
        if r:
            cur = self.con.cursor()
            selected_item = self.trwPB.selection()[0]
            values = self.trwPB.item(selected_item)
            url = values.get("values")[4]
        webbrowser.open(url)

    def cleanup(self, evt):
        self.con.close()

    def load_data(self):
        self.trwPB.delete(*self.trwPB.get_children())
        cur = self.con.cursor()
        s = self.search.get()
        if s:
            cur.execute(
                "SELECT * FROM prices WHERE id_item LIKE ? ORDER BY id_record DESC;",
                (s + "%",),
            )
        else:
            cur.execute("SELECT * FROM prices ORDER BY id_record DESC;")
        for rec in cur:
            self.trwPB.insert(
                "",
                "end",
                text=rec[0],
                values=(rec[1], rec[2], rec[3], rec[4], rec[5], rec[6]),
            )
        cur.close()

    def add_record(self):
        rec = {
            "id_record": None,
            "id_item": "",
            "item": "",
            "price": "",
            "time": "",
            "link": "",
            "information": "",
        }
        Record(parent=self, record=rec)

    def edit_record(self):
        r = self.trwPB.focus()
        if r:
            rec = {
                "id_record": self.trwPB.item(r, option="text"),
                "id_item": self.trwPB.set(r, column="id_item"),
                "item": self.trwPB.set(r, column="item"),
                "price": self.trwPB.set(r, column="price"),
                "time": self.trwPB.set(r, column="time"),
                "link": self.trwPB.set(r, column="link"),
                "information": self.trwPB.set(r, column="information"),
            }
            Record(parent=self, record=rec)

    def create_graph(self):
        r = self.trwPB.focus()
        if r:
            cur = self.con.cursor()
            selected_item = self.trwPB.selection()[0]
            values = self.trwPB.item(selected_item)
            value = values.get("values")[4]
            prices = cur.execute(
                f"select price from prices WHERE link = '{value}'"
            ).fetchall()
            prices = [x[0] for x in prices]
            timeall = cur.execute(
                f"select time from prices WHERE link = '{value}'"
            ).fetchall()
            timeall = [x[0] for x in timeall]

            if len(prices) < 2:
                tkinter.messagebox.showerror(
                    "Ошибка",
                    "Для создания графика требуется как минимум две записи",
                    parent=self,
                )
            else:
                fig = go.Figure(
                    data=go.Scatter(
                        x=timeall, y=prices, mode="lines+markers", name="Цены"
                    )
                )
                fig.update_layout(
                    title="График изменения цен на товар",
                    xaxis_title="Время",
                    yaxis_title="Цена",
                )
                fig.write_html("graph.html")  # Сохраняем график в HTML-файл
                webbrowser.open(
                    "file://" + os.path.realpath("graph.html")
                )  # Открываем HTML-файл в браузере

            self.con.commit()

    def delete_record(self):
        r = self.trwPB.focus()
        if r and tkinter.messagebox.askyesno(
            Application.app_title,
            "Удалить запись?",
            default=tkinter.messagebox.NO,
            parent=self,
        ):
            id_row = self.trwPB.item(r, option="text")
            cur = self.con.cursor()
            try:
                cur.execute("delete from prices where id_record=?", (id_row,))
            except sqlite3.DatabaseError as err:
                tkinter.messagebox.showerror(
                    Application.app_title,
                    "При удалении записи возникла ошибка: " + str(err),
                    parent=self,
                )
            else:
                self.con.commit()
                self.load_data()

    def show_info(self):
        tkinter.messagebox.showinfo(
            Application.app_title, "© Учёт цен, 2022 г.", parent=self
        )

    def newwindow(self):
        apps = Products(parent=self)
        apps.mainloop()

    def open_settings(self):
        settings = Settings()
        settings.mainloop()

    def update(self):
        self.update_button.configure(text="Проверка...", state="disabled")
        update_thread = threading.Thread(target=self.update_logic)
        update_thread.start()

    def update_complete_callback(self):
        self.update_button.configure(text="Проверить данные", state="normal")
        self.load_data()

    def update_logic(self):
        if getattr(sys, "frozen", False):
            dir_path = sys._MEIPASS
        else:
            dir_path = os.path.dirname(os.path.abspath(__file__))

        db_dir = os.path.join(dir_path, "data")

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        db_path = os.path.join(db_dir, "tab.db")

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        link = cur.execute(f"select link from items").fetchall()
        link = [x[0] for x in link]
        link_count = len(link)
        price_interval = 0

        for i in range(link_count):
            if "flip" in link[i]:
                r = requests.get(link[i])
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

            elif "technodom" in link[i]:
                try:
                    r = requests.get(link[i])
                    html = BS(r.content, "html.parser")
                    item = html.find("h1").text
                    information = (
                        "Для дополнительной информации перейдите на страницу товара"
                    )
                    try:
                        price = html.find("p", class_="Typography__Heading_H1").text
                        price = price.replace("₸", "")
                        price = int(price)
                    except:
                        price = 0
                        information = "Товара нет в наличии"
                except:
                    item = "Снят с продажи"
                    price = 0

            elif "kaspi" in link[i]:
                try:
                    html = setup_driver_kaspi(link[i])
                    if html is None:
                        logging.error(
                            "Не удалось получить данные с kaspi, переход к следующей записи"
                        )
                        continue
                    soup = BS(html, "html.parser")
                except Exception as e:
                    logging.error(f"Произошла ошибка: {e}")

                try:
                    item = soup.find("h1", class_="item__heading").text.strip()
                except:
                    item = "Информации нет"
                try:
                    sellers_rows = soup.find_all("tr")
                    for seller_row in sellers_rows:
                        reviews_link = seller_row.find("a", class_="rating-count")
                        if reviews_link:
                            reviews_text = reviews_link.text.strip()
                            reviews_count = int(
                                "".join(filter(str.isdigit, reviews_text))
                            )

                            if reviews_count >= min_reviews_count:
                                price_text = seller_row.find(
                                    "div", class_="sellers-table__price-cell-text"
                                ).text.strip()
                                price = int("".join(filter(str.isdigit, price_text)))
                                break
                    else:
                        logging.warning(
                            f"Не найдено предложений с количеством отзывов больше {min_reviews_count}"
                        )
                        continue
                except Exception as e:
                    logging.error(f"Произошла ошибка при поиске цены: {e}")
                    price = None
                    item = "Товара нет в наличии"
                try:
                    description = soup.find("div", class_="item__description-text")
                    description_items = description.find_all("li")
                    information = " / ".join(
                        item.get_text().strip() for item in description_items
                    )
                except:
                    information = "Информации нет"

            elif "ozon" in link[i]:
                html = setup_driver_ozon(link[i])
                if html is None:
                    logging.error(
                        "Не удалось получить данные с ozon, переход к следующей записи"
                    )
                    continue
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
                    "Ошибка", f"Неизвестный магазин: {link[i]}"
                )
                continue

            time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
            timeall = cur.execute(
                f"select time from prices WHERE link = '{link[i]}'"
            ).fetchall()
            timeall = [x[0] for x in timeall]

            record_count = len(timeall)
            if record_count != 0:
                lastrrecordtime = datetime.strptime(timeall[0], "%m/%d/%Y %H:%M:%S")
                for p in range(record_count):
                    current_time = datetime.strptime(timeall[p], "%m/%d/%Y %H:%M:%S")
                    if lastrrecordtime < current_time:
                        lastrrecordtime = current_time
                lastrrecordtime = lastrrecordtime.strftime("%m/%d/%Y %H:%M:%S")
                lastrecordid = cur.execute(
                    f"select id_record from prices WHERE link = '{link[i]}' AND time = '{lastrrecordtime}'"
                ).fetchone()[0]
                print(f"Last record ID: {lastrecordid}")

                lastprice = cur.execute(
                    f"select price from prices WHERE id_record = '{lastrecordid}'"
                ).fetchone()[0]
                print(f"Last price: {lastprice}")

                if lastprice != price:
                    print(f"Price change detected: {lastprice} -> {price}")
                    id_item = str(
                        cur.execute(
                            f"select id_item from items WHERE link = '{link[i]}'"
                        ).fetchone()[0]
                    )
                    price_interval_by_product = lastprice - price
                    print(f"Price interval by product: {price_interval_by_product}")
                    if price_interval_by_product < 0:
                        price_interval_by_product = price_interval_by_product * -1
                    if price_interval_by_product > price_interval:
                        price_interval = price_interval_by_product
                    if price_range_for_save_to_db < price_interval_by_product:
                        cur.execute(
                            "insert into prices (id_item, item, price, time, link, information) "
                            + "values (?, ? ,? , ? , ?, ?)",
                            (id_item, item, price, time, link[i], information),
                        )

            else:
                id_item = str(
                    cur.execute(
                        f"select id_item from items WHERE link = '{link[i]}'"
                    ).fetchone()[0]
                )

                cur.execute(
                    "insert into prices (id_item, item, price, time, link, information) "
                    + "values (?, ? ,? , ? , ?, ?)",
                    (id_item, item, price, time, link[i], information),
                )
        if price_interval < price_range_for_save_to_db:
            tkinter.messagebox.showinfo("Уведомление", "Изменений нет", parent=self)
        else:
            tkinter.messagebox.showinfo("Уведомление", "Цены изменились", parent=self)
        con.commit()
        self.after(0, self.update_complete_callback)


class Products(tkinter.Toplevel):
    app_title = "Учёт цен"

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

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.active_operations = 0
        self.configure_activity_indicator()
        if getattr(sys, "frozen", False):
            dir_path = sys._MEIPASS
        else:
            dir_path = os.path.dirname(os.path.abspath(__file__))

        db_dir = os.path.join(dir_path, "data")

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        db_path = os.path.join(db_dir, "tab.db")

        self.con = sqlite3.connect(db_path)
        self.create_widgets()
        self.center_window()
        self.title(Application.app_title)
        self.iconbitmap(r"images/icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.update_application_window)
        self.mainloop()

    def update_application_window(self):
        self.destroy()
        self.parent.load_data()

    def center_window(self):
        self.update_idletasks()  # Обновляем информацию о размерах окна

        # Получаем ширину и высоту окна
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # Получаем ширину и высоту экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Вычисляем координаты для центрирования окна
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)

        # Устанавливаем новые координаты окна
        self.geometry(f"+{x}+{y}")

    def create_widgets(self):
        self.add_image = tkinter.PhotoImage(file=r"images/add.gif")
        self.addlink_image = tkinter.PhotoImage(file=r"images/addlink.png")
        self.edit_image = tkinter.PhotoImage(file=r"images/edit.gif")
        self.delete_image = tkinter.PhotoImage(file=r"images/delete.gif")
        self.search_image = tkinter.PhotoImage(file=r"images/search.gif")
        mainmenu = tkinter.Menu(self)
        self["menu"] = mainmenu

        self.editmenu = tkinter.Menu(mainmenu, tearoff=False)
        self.editmenu.add_command(
            label="Добавить",
            accelerator="Ins",
            image=self.add_image,
            compound=tkinter.LEFT,
            command=self.add_record,
        )
        self.editmenu.add_command(
            label="Добавить товар по ссылке",
            accelerator="F2",
            image=self.addlink_image,
            compound=tkinter.LEFT,
            command=self.add_link,
        )
        self.editmenu.add_command(
            label="Изменить",
            accelerator="F5",
            image=self.edit_image,
            compound=tkinter.LEFT,
            command=self.edit_record,
        )
        self.editmenu.add_separator()
        self.editmenu.add_command(
            label="Удалить",
            accelerator="F8",
            image=self.delete_image,
            compound=tkinter.LEFT,
            command=self.delete_record,
        )
        mainmenu.add_cascade(label="Правка", menu=self.editmenu)

        helpmenu = tkinter.Menu(mainmenu, tearoff=False)
        helpmenu.add_command(label="О программе...", command=self.show_info)
        mainmenu.add_cascade(label="Справка", menu=helpmenu)

        self.search = tkinter.StringVar()
        self.search.set("")

        self.activity_indicator = ct.CTkLabel(
            self, text="Добавление данных...", font=("Arial", 12)
        )
        self.activity_indicator.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        self.activity_indicator.grid_remove()  # Скрыть по умолчанию

        frm = tkinter.ttk.Frame(self)
        entSearch = ct.CTkEntry(frm, textvariable=self.search)
        entSearch.grid(row=0, column=0, sticky="we")
        btnSearch = tkinter.ttk.Button(
            frm, image=self.search_image, command=self.load_data
        )
        btnSearch.grid(row=0, column=1, pady=5, padx=(1, 15))
        frm.grid_columnconfigure(0, weight=1)
        frm.grid(row=0, column=0, columnspan=2, sticky="we")

        self.trwPB = tkinter.ttk.Treeview(
            self,
            columns=("item", "time", "link"),
            displaycolumns="#all",
            show="headings",
        )
        self.trwPB.column("item", minwidth=100)
        self.trwPB.column("time", minwidth=100)
        self.trwPB.column("link", minwidth=100)

        self.trwPB.heading("item", text="Товар")
        self.trwPB.heading("time", text="Время")
        self.trwPB.heading("link", text="Ссылка")

        self.trwPB.grid(row=1, column=0, sticky="wnes")
        hs = tkinter.ttk.Scrollbar(
            self, orient=tkinter.HORIZONTAL, command=self.trwPB.xview
        )
        hs.grid(row=2, column=0, sticky="we")
        vs = tkinter.ttk.Scrollbar(self, command=self.trwPB.yview)
        vs.grid(row=1, column=1, sticky="ns")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        sgp = tkinter.ttk.Sizegrip(self)
        sgp.grid(row=2, column=1, sticky="ns")

        self.bind_all("<KeyPress-Insert>", lambda evt: self.editmenu.invoke(0))
        self.bind_all("<KeyPress-F2>", lambda evt: self.editmenu.invoke(1))
        self.bind_all("<KeyPress-F5>", lambda evt: self.editmenu.invoke(2))
        self.bind_all("<KeyPress-F8>", lambda evt: self.editmenu.invoke(4))

        self.bind("<Destroy>", self.cleanup)

        self.trwPB.bind("<Double-1>", self.on_double_click)

        entSearch.bind("<Control-KeyPress>", self.keys)

        context_menu = tkinter.Menu(self, tearoff=0)
        context_menu.add_command(label="Добавить", command=self.add_record)
        context_menu.add_command(
            label="Добавить товар по ссылке", command=self.add_link
        )
        context_menu.add_command(label="Изменить", command=self.edit_record)
        context_menu.add_command(label="Удалить", command=self.delete_record)

        def show_context_menu(event):
            row_id = self.trwPB.identify_row(event.y)
            self.trwPB.selection_set(row_id)
            context_menu.post(event.x_root, event.y_root)

        self.trwPB.bind("<Button-3>", show_context_menu)

        self.load_data()

        self.grab_set()

    def on_double_click(self, event):
        r = self.trwPB.focus()
        if r:
            cur = self.con.cursor()
            selected_item = self.trwPB.selection()[0]
            values = self.trwPB.item(selected_item)
            url = values.get("values")[2]
        webbrowser.open(url)

    def cleanup(self, evt):
        self.con.close()

    def load_data(self):
        self.trwPB.delete(*self.trwPB.get_children())
        cur = self.con.cursor()
        s = self.search.get()
        if s:
            cur.execute(
                "select * from items where item like ? order by id_item;", (s + "%",)
            )
        else:
            cur.execute("select * from items order by id_item;")
        for rec in cur:
            self.trwPB.insert("", "end", text=rec[0], values=(rec[1], rec[2], rec[3]))
        cur.close()

    def add_record(self):
        rec = {"id_item": None, "item": "", "time": "", "link": ""}
        Recordtop(parent=self, record=rec)

    def add_link(self):
        Recordlink(parent=self)

    def configure_activity_indicator(self):
        # Инициализация и настройка индикатора активности
        self.activity_indicator = ct.CTkLabel(self, text="", font=("Arial", 12))
        self.activity_indicator.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        self.activity_indicator.grid_remove()  # Скрыть по умолчанию

    def update_activity_indicator(self):
        if self.active_operations > 0:
            self.activity_indicator.configure(
                text=f"Добавление данных... ({self.active_operations})"
            )
        else:
            self.activity_indicator.configure(text="")

    def show_activity(self):
        self.active_operations += 1
        self.update_activity_indicator()
        if self.active_operations == 1:
            self.activity_indicator.grid()

    def hide_activity(self):
        if self.active_operations > 0:
            self.active_operations -= 1
            self.update_activity_indicator()
            if self.active_operations == 0:
                self.activity_indicator.grid_remove()

    def edit_record(self):
        r = self.trwPB.focus()
        if r:
            rec = {
                "id_item": self.trwPB.item(r, option="text"),
                "item": self.trwPB.set(r, column="item"),
                "time": self.trwPB.set(r, column="time"),
                "link": self.trwPB.set(r, column="link"),
            }
            Recordtop(parent=self, record=rec)

    def delete_record(self):
        r = self.trwPB.focus()
        if r:
            id_row = self.trwPB.item(r, option="text")
            if tkinter.messagebox.askyesno(
                Application.app_title,
                "Удалить запись товара?",
                default=tkinter.messagebox.NO,
                parent=self,
            ):
                if tkinter.messagebox.askyesno(
                    Application.app_title,
                    "Удалить историю цен товара?",
                    default=tkinter.messagebox.NO,
                    parent=self,
                ):
                    cur = self.con.cursor()
                    try:
                        cur.execute("delete from items where id_item=?", (id_row,))
                        cur.execute("delete from prices where id_item=?", (id_row,))
                    except sqlite3.DatabaseError as err:
                        tkinter.messagebox.showerror(
                            Application.app_title,
                            "При удалении записи возникла ошибка: " + str(err),
                            parent=self,
                        )
                    else:
                        self.con.commit()
                        self.load_data()
                else:
                    cur = self.con.cursor()
                    try:
                        cur.execute("delete from items where id_item=?", (id_row,))
                    except sqlite3.DatabaseError as err:
                        tkinter.messagebox.showerror(
                            Application.app_title,
                            "При удалении записи возникла ошибка: " + str(err),
                            parent=self,
                        )
                    else:
                        self.con.commit()
                        self.load_data()

    def show_info(self):
        tkinter.messagebox.showinfo(
            Application.app_title, "© Учёт цен, 2022 г.", parent=self
        )
