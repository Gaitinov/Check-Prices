import tkinter
import tkinter.ttk
import tkinter.messagebox
import customtkinter as ct
import sqlite3
import webbrowser
from datetime import datetime, timedelta
from modules.record import Recordtop
from modules.record import Recordlink
from modules.config import CustomEntry, DBPath, Instruction


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
        self.title(self.app_title)
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
                self.app_title,
                "Удалить запись товара?",
                default=tkinter.messagebox.NO,
                parent=self,
            ):
                if tkinter.messagebox.askyesno(
                    self.app_title,
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
                            self.app_title,
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
                            self.app_title,
                            "При удалении записи возникла ошибка: " + str(err),
                            parent=self,
                        )
                    else:
                        self.con.commit()
                        self.load_data()

    def show_info(self):
        tkinter.messagebox.showinfo(
            self.app_title.app_title,
            "© Check Prices, 2024 г.\n\n" "Сделано Гайтиновым Мухарамом.",
            parent=self,
        )
