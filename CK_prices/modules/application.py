import tkinter
import tkinter.ttk
import logging
import tkinter.messagebox
import customtkinter as ct
import sqlite3
import sys
import webbrowser
import os
import configparser
import plotly.graph_objects as go
from pystray import MenuItem as item
import pystray
import threading
from PIL import Image
from datetime import datetime
from modules.record import Record
from modules.record import Recordtop
from modules.record import Recordlink
from modules.update import update_tray
from modules.settings import Settings
from modules.product_info_extractor import extract_product_info
from modules.config import CustomEntry, DBPath


config = configparser.ConfigParser()
config.read("settings.ini")

check_price_interval = config.getint("DEFAULT", "check_price_interval")
price_range_for_save_to_db = config.getint("DEFAULT", "price_range_for_save_to_db")
min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


class Application(ct.CTk):
    app_title = "Учёт цен"
    schprocess = None
    stop_event = None

    logging.info("Logging started")

    def check_auto_close(self):
        if "--auto-close" in sys.argv and "--from-settings" not in sys.argv:
            self.exitstray()

    def __init__(self):
        super().__init__()

        try:
            db_path = DBPath.get_or_init_db_path()

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
            self.check_auto_close()
            self.mainloop()
        except Exception as e:
            logging.error("Error: %s", e)

    def sch(self):
        try:
            print("Thread started")
            threadupdate = None
            while not self.stop_event.is_set():
                self.stop_event.wait(check_price_interval)
                if self.stop_event.is_set():
                    logging.info("The thread is broken")
                    print("Thread is broken")
                    break

                if threadupdate is None or not threadupdate.is_alive():
                    threadupdate = threading.Thread(target=update_tray)
                    threadupdate.daemon = True
                    threadupdate.start()
                    logging.info("Thread started")

        except Exception as e:
            logging.error("Error: %s", e)

    def exitstray(self):
        logging.info("The application moved to the tray")

        def action():
            try:
                print("Поток остановлен")
                self.stop_event.set()
                self.deiconify()
                self.icon.stop()
                self.load_data()
                self.lift()  # Поднимаем окно на передний план
                self.focus_force()  # Принудительно устанавливаем фокус на окне
                logging.info("The application is out of the tray")
            except Exception as e:
                logging.error("Error: %s", e)

        def exitall(icon, item):
            os._exit(0)

        try:
            if self.schprocess is None or not self.schprocess.is_alive():
                self.stop_event = threading.Event()
                self.schprocess = threading.Thread(target=self.sch)
                self.schprocess.start()
            self.withdraw()
            image = Image.open("images/icon.ico")
            self.icon = pystray.Icon(
                "name",
                image,
                "Check price",
                menu=pystray.Menu(
                    item("Развернуть", action, default=True), item("Выйти", exitall)
                ),
            )
            self.icon.run()
        except Exception as e:
            logging.error("Error: %s", e)

    def create_widgets(self):
        self.add_image = tkinter.PhotoImage(file=r"images/add.gif")
        self.edit_image = tkinter.PhotoImage(file=r"images/edit.gif")
        self.graph_image = tkinter.PhotoImage(file=r"images/graph.png")
        self.delete_image = tkinter.PhotoImage(file=r"images/delete.gif")
        self.search_image = tkinter.PhotoImage(file=r"images/search.gif")

        self.entry_menu = CustomEntry(self)

        mainmenu = tkinter.Menu(self)
        self.config(menu=mainmenu)

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

        frm = ct.CTkFrame(self)
        entSearch = ct.CTkEntry(frm, textvariable=self.search)
        entSearch.bind(
            "<Button-3>",
            lambda event, widget=entSearch: self.entry_menu.show(event, widget),
        )
        entSearch.bind("<Control-KeyPress>", lambda event: self.entry_menu.keys(event))
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
            if row_id:
                self.trwPB.selection_set(row_id)
                self.trwPB.focus(row_id)
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
        search_str = self.search.get()
        if search_str:
            cur.execute(
                """
                    SELECT * FROM prices
                    WHERE id_item LIKE ?
                       OR item LIKE ?
                       OR price LIKE ?
                       OR time LIKE ?
                       OR link LIKE ?
                       OR information LIKE ?
                    ORDER BY id_record DESC;
                    """,
                (
                    f"%{search_str}%",
                    f"%{search_str}%",
                    f"%{search_str}%",
                    f"%{search_str}%",
                    f"%{search_str}%",
                    f"%{search_str}%",
                ),
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
            item_name = cur.execute(
                f"select item from items WHERE link = '{value}'"
            ).fetchone()[0]
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
                    title=f"График изменения цен на товар: {item_name}",
                    xaxis_title="Время",
                    yaxis_title="Цена",
                )
                fig.write_html("graph.html")
                webbrowser.open("file://" + os.path.realpath("graph.html"))

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
        db_path = DBPath.get_or_init_db_path()

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        link = cur.execute(f"select link from items").fetchall()
        link = [x[0] for x in link]
        link_count = len(link)
        price_interval = 0

        for i in range(link_count):
            if "flip" in link[i]:
                item, information, price = extract_product_info(link[i])

            elif "technodom" in link[i]:
                item, information, price = extract_product_info(link[i])

            elif "kaspi" in link[i]:
                result = extract_product_info(link[i])
                if result is None:
                    tkinter.messagebox.showerror(
                        title="Ошибка загрузки данных",
                        message="Не удалось получить данные с kaspi.",
                    )
                    continue
                if result[0] == "skip":
                    tkinter.messagebox.showerror(
                        title="Недостаточно отзывов",
                        message=f"Нет цены на товар Kaspi: {link[i]}. Пропуск.",
                        parent=self,
                    )
                if result[0] == "second_check":
                    logging.warning(
                        f"Повторная проверка цен для товара Kaspi: {link[i]}. Пропуск."
                    )
                    continue
                item, information, price = result

            elif "ozon" in link[i]:
                result = extract_product_info(link[i])
                if result is None:
                    tkinter.messagebox.showerror(
                        title="Ошибка загрузки данных",
                        message="Не удалось получить данные с ozon.",
                    )
                    continue
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


class Products(ct.CTkToplevel):
    app_title = "Учёт цен"

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.active_operations = 0
        self.configure_activity_indicator()
        db_path = DBPath.get_or_init_db_path()

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
        self.geometry(
            f"800x300+{self.winfo_screenwidth() // 2 - 800 // 2}+{self.winfo_screenheight() // 2 - 300 // 2}"
        )

    def create_widgets(self):
        self.add_image = tkinter.PhotoImage(file=r"images/add.gif")
        self.addlink_image = tkinter.PhotoImage(file=r"images/addlink.png")
        self.edit_image = tkinter.PhotoImage(file=r"images/edit.gif")
        self.delete_image = tkinter.PhotoImage(file=r"images/delete.gif")
        self.search_image = tkinter.PhotoImage(file=r"images/search.gif")

        self.entry_menu = CustomEntry(self)

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

        frm = ct.CTkFrame(self)
        entSearch = ct.CTkEntry(frm, textvariable=self.search)
        entSearch.bind(
            "<Button-3>",
            lambda event, widget=entSearch: self.entry_menu.show(event, widget),
        )
        entSearch.bind("<Control-KeyPress>", lambda event: self.entry_menu.keys(event))
        entSearch.grid(row=0, column=0, sticky="we")
        btnSearch = tkinter.ttk.Button(
            frm, image=self.search_image, command=self.load_data
        )
        btnSearch.grid(row=0, column=1, pady=5, padx=(1, 15))

        self.add_button = ct.CTkButton(frm, text="Добавить", command=self.add_link)
        self.add_button.grid(row=0, column=4, padx=20, pady=5)

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

        context_menu = tkinter.Menu(self, tearoff=0)
        context_menu.add_command(label="Добавить", command=self.add_record)
        context_menu.add_command(
            label="Добавить товар по ссылке", command=self.add_link
        )
        context_menu.add_command(label="Изменить", command=self.edit_record)
        context_menu.add_command(label="Удалить", command=self.delete_record)

        def show_context_menu(event):
            row_id = self.trwPB.identify_row(event.y)
            if row_id:
                self.trwPB.selection_set(row_id)
                self.trwPB.focus(row_id)
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
        search_str = self.search.get()
        if search_str:
            cur.execute(
                "select * from items where item like ? or time like ? or link like ?",
                (f"%{search_str}%", f"%{search_str}%", f"%{search_str}%"),
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
