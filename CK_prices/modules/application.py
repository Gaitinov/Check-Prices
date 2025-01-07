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
from datetime import datetime, timedelta
from modules.record import Record
from modules.record import Recordtop
from modules.record import Recordlink
from modules.update import update_tray
from modules.settings import Settings
from modules.product_info_extractor import extract_product_info
from modules.config import CustomEntry, DBPath, Instruction
from winotify import Notification


config = configparser.ConfigParser()
config.read("settings.ini")

check_price_interval = config.getint("DEFAULT", "check_price_interval")
price_range_for_save_to_db = config.getint("DEFAULT", "price_range_for_save_to_db")
min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


class Application(ct.CTk):
    app_title = "Check Prices"
    tray_price_check_thread = None
    stop_event = None

    logging.info("Logging started")

    def check_auto_close(self):
        if "--auto-close" in sys.argv and "--from-settings" not in sys.argv:
            self.setup_for_tray()

    def __init__(self):
        super().__init__()

        try:
            self.total_items = 0
            self.checked_items = 0
            self.is_in_tray = False

            db_path = DBPath.get_or_init_db_path()

            self.con = sqlite3.connect(db_path)
            self.create_widgets()
            self.title(Application.app_title)
            self.iconbitmap(r"images/icon.ico")

            self.update_idletasks()
            window_width = 1200
            window_height = 400
            position_right = int(self.winfo_screenwidth() / 2 - window_width / 2)
            position_down = int(self.winfo_screenheight() / 2 - window_height / 2)
            self.geometry(
                f"{window_width}x{window_height}+{position_right}+{position_down}"
            )
            self.attributes("-topmost", True)
            self.after_idle(
                self.attributes, "-topmost", False
            )  # Затем возвращаем обычный режим

            self.protocol("WM_DELETE_WINDOW", self.setup_for_tray)
            self.check_auto_close()
            self.mainloop()
        except Exception as e:
            logging.error("Error: %s", e)

    def start_tray_price_check_thread(self):
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

    def setup_for_tray(self):
        logging.info("The application moved to the tray")

        def restore_application_window():
            try:
                print("Thread stopped")
                self.stop_event.set()
                self.deiconify()
                self.icon.stop()
                self.load_data()
                self.lift()  # Поднимаем окно на передний план
                self.focus_force()  # Принудительно устанавливаем фокус на окне
                self.is_in_tray = False
                self.after(0, self.update_activity_indicator)
                logging.info("The application is out of the tray")
            except Exception as e:
                logging.error("Error: %s", e)

        def exit_application(icon, item):
            os._exit(0)

        try:
            if (
                self.tray_price_check_thread is None
                or not self.tray_price_check_thread.is_alive()
            ):
                self.stop_event = threading.Event()
                self.tray_price_check_thread = threading.Thread(
                    target=self.start_tray_price_check_thread
                )
                self.tray_price_check_thread.start()
            self.is_in_tray = True
            self.withdraw()
            image = Image.open("images/icon.ico")
            self.icon = pystray.Icon(
                "name",
                image,
                "Check price",
                menu=pystray.Menu(
                    item("Развернуть", restore_application_window, default=True),
                    item("Выйти", exit_application),
                ),
            )
            self.icon.run()
        except Exception as e:
            logging.error("Error: %s", e)

    def create_widgets(self):

        self.configure(bg="#f0f0f0")

        style = tkinter.ttk.Style()
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            rowheight=25,
        )
        style.configure(
            "Treeview.Heading",
            font=("Helvetica", 10, "bold"),
            background="#f2f2f2",
            foreground="#333333",
        )
        style.map("Treeview", background=[("selected", "#0078D7")])

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
            accelerator="Delete",
            image=self.delete_image,
            compound=tkinter.LEFT,
            command=self.delete_record,
        )
        mainmenu.add_cascade(label="Правка", menu=self.editmenu)

        helpmenu = tkinter.Menu(mainmenu, tearoff=False)
        helpmenu.add_command(label="О программе...", command=self.show_info)
        helpmenu.add_command(label="Инструкция", command=Instruction.open_manual)
        helpmenu.add_command(label="Журнал", command=self.open_logs)
        helpmenu.add_command(label="Открыть папку с БД", command=self.open_folder)
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
        entSearch.bind("<Return>", lambda event: self.load_data())
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
        self.bind_all("<KeyPress-Delete>", lambda evt: self.editmenu.invoke(4))

        self.bind("<Destroy>", self.close_database_connection)

        self.trwPB.bind("<Double-1>", self.on_double_click)

        self.update_button = ct.CTkButton(
            frm, text="Проверить данные", command=self.update
        )
        self.update_button.grid(row=0, column=3, padx=20, pady=5)

        button = ct.CTkButton(frm, text="Товары", command=self.open_products_window)
        button.grid(row=0, column=4, padx=20, pady=5)

        self.activity_indicator = ct.CTkLabel(
            self, text="Проверка цен...", font=("Arial", 12)
        )
        self.activity_indicator.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        self.activity_indicator.grid_remove()

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

    def close_database_connection(self, evt):
        self.con.close()

    def get_last_price(self, id_item, current_time):
        logging.info(
            f"Fetching last price for item id_item={id_item}, current record time={current_time}"
        )

        try:
            cur = self.con.cursor()
            cur.execute(
                "SELECT price, time FROM prices WHERE id_item = ? ORDER BY time DESC",
                (id_item,),
            )
            all_records = cur.fetchall()
            logging.info(f"All records for id_item={id_item}: {all_records}")

            current_time_obj = datetime.strptime(current_time, "%m/%d/%Y %H:%M:%S")
            logging.info(f"Parsed current time: {current_time_obj}")
            last_valid_price = None

            for record in all_records:
                price, record_time = record
                record_time_obj = datetime.strptime(record_time, "%m/%d/%Y %H:%M:%S")
                logging.info(f"Record time: {record_time_obj}, Price: {price}")

                if record_time_obj == current_time_obj:
                    continue

                if record_time_obj < current_time_obj:
                    last_valid_price = price
                    break

            if last_valid_price is not None:
                logging.info(
                    f"Last valid price for id_item={id_item}: {last_valid_price}"
                )
                return last_valid_price
            else:
                logging.warning(
                    f"No previous record found for id_item={id_item} with time < {current_time}"
                )
                return None

        except Exception as e:
            logging.error(f"Error in get_last_price for id_item={id_item}: {e}")
            return None

    def get_price_change_status(self, last_price, current_price):
        try:
            if last_price is not None:
                last_price = float(last_price)
            current_price = float(current_price)
        except ValueError as e:
            return "same"

        if last_price is None:
            return "same"
        if last_price == 0 and current_price > 0:
            return "back_in_stock"
        if last_price > 0 and current_price == 0:
            return "back_in_stock"
        if current_price > last_price:
            return "up"
        elif current_price < last_price:
            return "down"
        return "same"

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

        last_items = {}
        for rec in cur:
            id_record = rec[0]
            id_item = rec[1]
            item = rec[2]
            price = rec[3]
            time = rec[4]
            link = rec[5]
            information = rec[6]
            if id_item not in last_items:
                last_price = self.get_last_price(id_item, time)
                print(f"Last price for id_item={id_item}: {last_price}")
                print(f"Current price for id_item={id_item}: {price}")
                tag = self.get_price_change_status(last_price, price)
                print(f"Tag for id_item={id_item}: {tag}")
                last_items[id_item] = tag
            else:
                tag = "same"

            self.trwPB.insert(
                "",
                "end",
                text=id_record,
                values=(id_item, item, price, time, link, information),
                tags=(tag,),
            )
        cur.close()

        self.trwPB.tag_configure("up", background="lightpink")
        self.trwPB.tag_configure("down", background="palegreen")
        self.trwPB.tag_configure("same", background="white")
        self.trwPB.tag_configure("back_in_stock", background="lightblue")

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
                    title=f"<a href='{value}'>{item_name}</a>",
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
            Application.app_title,
            f"© Check Prices, 2024 г.\n\n" "Сделано Гайтиновым Мухарамом.",
            parent=self,
        )

    def open_products_window(self):
        productswindow = Products(parent=self)
        productswindow.mainloop()

    def open_settings(self):
        settings = Settings()
        settings.mainloop()

    def open_logs(self):
        try:
            os.startfile("Logs.log")
        except Exception as e:
            tkinter.messagebox.showerror(
                "Ошибка", "Не удалось открыть файл журнала", parent=self
            )

    def open_folder(self):
        try:
            os.startfile(os.path.dirname(DBPath.get_or_init_db_path()))
        except Exception as e:
            tkinter.messagebox.showerror(
                "Ошибка", "Не удалось открыть папку с базой данных", parent=self
            )

    def update(self):
        self.update_button.configure(text="Проверка...", state="disabled")
        update_thread = threading.Thread(target=self.update_logic)
        update_thread.start()

    def update_complete_callback(self):
        self.update_button.configure(text="Проверить данные", state="normal")
        self.load_data()

    def update_activity_indicator(self):
        self.activity_indicator.configure(
            text=f"Проверка цен... ({self.checked_items}/{self.total_items})"
        )

    def notifycheck(self):
        try:
            toast = Notification(
                app_id="Check prices",
                title="Проверка цен завершена",
                msg="Откройте приложение",
            )
            toast.show()
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def update_logic(self):
        db_path = DBPath.get_or_init_db_path()
        logging.info("Update from the application: started")

        con = sqlite3.connect(db_path)
        cur = con.cursor()
        link = cur.execute(f"select link from items").fetchall()
        link = [x[0] for x in link]
        link_count = len(link)
        price_interval = 0
        error_messages = []
        self.total_items = len(link)
        self.checked_items = 0
        self.activity_indicator.grid()
        self.after(0, self.update_activity_indicator)

        for i in range(link_count):
            if "flip" in link[i]:
                item, information, price = extract_product_info(link[i])
                if item is None:
                    error_messages.append(f"Не удалось получить данные с {link[i]}.")

            elif "technodom" in link[i]:
                item, information, price = extract_product_info(link[i])
                if item is None:
                    error_messages.append(f"Не удалось получить данные с {link[i]}.")

            elif "kaspi" in link[i]:
                result = extract_product_info(link[i])
                if result is None:
                    error_messages.append(
                        f"Не удалось получить данные с kaspi: {link[i]}."
                    )
                    continue
                if result[0] == "skip":
                    error_messages.append(
                        f" Пропуск. Нет цены на товар Kaspi: {link[i]}."
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
                    error_messages.append(
                        f"Не удалось получить данные с ozon:  {link[i]}."
                    )
                    continue
                else:
                    item, information, price = result

            else:
                error_messages.append(f"Неизвестный магазин: {link[i]}")
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

            self.checked_items += 1
            if not self.is_in_tray:
                self.after(0, self.update_activity_indicator)

        con.commit()

        if self.is_in_tray:
            self.notifycheck()

        if error_messages:
            tkinter.messagebox.showerror(
                "Ошибки во время выполнения", "\n\n".join(error_messages)
            )

        if price_interval < price_range_for_save_to_db:
            tkinter.messagebox.showinfo("Уведомление", "Изменений нет", parent=self)
        else:
            tkinter.messagebox.showinfo("Уведомление", "Цены изменились", parent=self)
        logging.info("Update from the application: finished")
        self.after(0, self.update_complete_callback)
        self.activity_indicator.grid_remove()


class Products(ct.CTkToplevel):
    app_title = "Check Prices"

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
        window_width = 800
        window_height = 300
        self.geometry(
            f"{window_width}x{window_height}+{self.winfo_screenwidth() // 2 - window_width // 2}+{self.winfo_screenheight() // 2 - window_height // 2}"
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
            accelerator="F1",
            image=self.addlink_image,
            compound=tkinter.LEFT,
            command=self.add_product_by_link,
        )
        self.editmenu.add_command(
            label="Изменить",
            accelerator="F2",
            image=self.edit_image,
            compound=tkinter.LEFT,
            command=self.edit_record,
        )
        self.editmenu.add_separator()
        self.editmenu.add_command(
            label="Удалить",
            accelerator="Delete",
            image=self.delete_image,
            compound=tkinter.LEFT,
            command=self.delete_record,
        )
        self.editmenu.add_separator()

        self.editmenu.add_command(
            label="Не обновлялись > месяца",
            image=self.search_image,
            compound=tkinter.LEFT,
            command=self.show_not_updated_items,
        )
        mainmenu.add_cascade(label="Правка", menu=self.editmenu)

        helpmenu = tkinter.Menu(mainmenu, tearoff=False)
        helpmenu.add_command(label="О программе...", command=self.show_info)
        helpmenu.add_command(label="Инструкция", command=Instruction.open_manual)
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
        entSearch.bind("<Return>", lambda event: self.load_data())
        btnSearch = tkinter.ttk.Button(
            frm, image=self.search_image, command=self.load_data
        )
        btnSearch.grid(row=0, column=1, pady=5, padx=(1, 15))

        self.add_button = ct.CTkButton(
            frm, text="Добавить", command=self.add_product_by_link
        )
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
        self.bind_all("<KeyPress-F1>", lambda evt: self.editmenu.invoke(1))
        self.bind_all("<KeyPress-F2>", lambda evt: self.editmenu.invoke(2))
        self.bind_all("<KeyPress-Delete>", lambda evt: self.editmenu.invoke(4))

        self.bind("<Destroy>", self.close_database_connection)

        self.trwPB.bind("<Double-1>", self.on_double_click)

        context_menu = tkinter.Menu(self, tearoff=0)
        context_menu.add_command(label="Добавить", command=self.add_record)
        context_menu.add_command(
            label="Добавить товар по ссылке", command=self.add_product_by_link
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

    def show_not_updated_items(self):
        cur = self.con.cursor()
        one_month_ago = datetime.now() - timedelta(days=30)
        one_month_ago_str = one_month_ago.strftime("%m/%d/%Y %H:%M:%S")

        cur.execute(
            """
            WITH LatestRecords AS (
                SELECT 
                    p1.id_item,
                    p1.item,
                    p1.time as last_update,
                    p1.link
                FROM prices p1
                WHERE p1.time = (
                    SELECT MAX(p2.time)
                    FROM prices p2
                    WHERE p2.item = p1.item
                )
            )
            SELECT 
                id_item,
                item,
                last_update,
                link
            FROM LatestRecords
            WHERE last_update < ?
            ORDER BY last_update DESC
        """,
            (one_month_ago_str,),
        )

        not_updated_items = cur.fetchall()
        cur.close()

        if not not_updated_items:
            tkinter.messagebox.showinfo(
                title="Информация",
                message="Все товары обновлены в течение последнего месяца.",
                parent=self,
            )
            return

        window = tkinter.Toplevel(self)
        window.title("Товары, не обновлявшиеся более месяца")
        window.state("zoomed")

        window.configure(bg="#f0f0f0")

        main_container = tkinter.Frame(window, bg="#f0f0f0")
        main_container.pack(fill=tkinter.BOTH, expand=True, padx=20, pady=20)

        header = tkinter.Label(
            master=main_container,
            text="Товары, не обновлявшиеся более месяца",
            font=("Helvetica", 18, "bold"),
            bg="#f0f0f0",
            fg="#333333",
        )
        header.pack(pady=15)


        table_container = tkinter.Frame(
            main_container,
            bg="white",
            highlightbackground="#ddd",
            highlightthickness=1,
            bd=0,
        )
        table_container.pack(fill=tkinter.BOTH, expand=True, pady=(0, 15))

        frame = tkinter.Frame(table_container)
        frame.pack(fill=tkinter.BOTH, expand=True, padx=2, pady=2)

        y_scrollbar = tkinter.Scrollbar(frame)
        y_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)

        x_scrollbar = tkinter.Scrollbar(frame, orient=tkinter.HORIZONTAL)
        x_scrollbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        tree = tkinter.ttk.Treeview(
            master=frame,
            columns=("ID", "Товар", "Последнее обновление", "Ссылка"),
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
        )

        y_scrollbar.config(command=tree.yview)
        x_scrollbar.config(command=tree.xview)

        tree.heading("ID", text="ID")
        tree.heading("Товар", text="Товар")
        tree.heading("Последнее обновление", text="Последнее обновление")
        tree.heading("Ссылка", text="Ссылка")

        tree.column("ID", width=50, anchor="center")
        tree.column("Товар", width=500, anchor="w")
        tree.column("Последнее обновление", width=200, anchor="center")
        tree.column("Ссылка", width=300, anchor="w")

        tree.tag_configure("oddrow", background="#f9f9f9")
        tree.tag_configure("evenrow", background="white")

        tree.pack(fill=tkinter.BOTH, expand=True)

        for idx, (id_item, item_name, last_update_str, link) in enumerate(
            not_updated_items
        ):
            try:
                item_name = item_name.split("\n")[0].strip()
                tree.insert(
                    "",
                    tkinter.END,
                    values=(id_item, item_name, last_update_str, link),
                    tags=("evenrow" if idx % 2 == 0 else "oddrow",),
                )
            except Exception as e:
                print(f"Ошибка при обработке записи: {e}")
                print(
                    f"Проблемная запись: ID={id_item}, Товар={item_name}, "
                    f"Дата={last_update_str}, Ссылка={link}"
                )

        def open_item_link(event):
            selected_item = tree.selection()
            if selected_item:
                link = tree.item(selected_item[0])["values"][3]
                if link:
                    webbrowser.open(link)
                else:
                    tkinter.messagebox.showinfo(
                        title="Информация",
                        message="Ссылка для этого товара отсутствует.",
                        parent=window,
                    )

        tree.bind("<Double-1>", open_item_link)

        button_container = tkinter.Frame(main_container, bg="#f0f0f0")
        button_container.pack(fill=tkinter.X, pady=(0, 10))

        close_button = tkinter.Button(
            master=button_container,
            text="Закрыть",
            font=("Helvetica", 12),
            command=window.destroy,
            bg="#0078D7",  #
            fg="white",
            activebackground="#006cc1",
            activeforeground="white",
            relief=tkinter.FLAT,
            padx=30,
            pady=8,
            cursor="hand2",
        )
        close_button.pack(pady=10)

    def on_double_click(self, event):
        r = self.trwPB.focus()
        if r:
            selected_item = self.trwPB.selection()[0]
            values = self.trwPB.item(selected_item)
            url = values.get("values")[2]
        webbrowser.open(url)

    def close_database_connection(self, evt):
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
            cur.execute("select * from items order by id_item DESC;")
        for rec in cur:
            self.trwPB.insert("", "end", text=rec[0], values=(rec[1], rec[2], rec[3]))
        cur.close()

    def add_record(self):
        rec = {"id_item": None, "item": "", "time": "", "link": ""}
        Recordtop(parent=self, record=rec)

    def add_product_by_link(self):
        Recordlink(parent=self)

    def configure_activity_indicator(self):
        # Инициализация и настройка индикатора активности
        self.activity_indicator = ct.CTkLabel(self, text="", font=("Arial", 12))
        self.activity_indicator.grid(row=3, column=0, pady=10, padx=10, sticky="ew")
        self.activity_indicator.grid_remove()

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
            Application.app_title,
            "© Check Prices, 2024 г.\n\n" "Сделано Гайтиновым Мухарамом.",
            parent=self,
        )
