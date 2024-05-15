import ctypes
import tkinter
import os
import sys
import logging


class CustomEntry:
    def __init__(self, parent):
        self.menu = tkinter.Menu(parent, tearoff=False)
        self.menu.add_command(
            label="Вырезать",
            command=lambda: parent.focus_get().event_generate("<<Cut>>"),
        )
        self.menu.add_command(
            label="Копировать",
            command=lambda: parent.focus_get().event_generate("<<Copy>>"),
        )
        self.menu.add_command(
            label="Вставить",
            command=lambda: parent.focus_get().event_generate("<<Paste>>"),
        )
        self.menu.add_command(
            label="Выделить всё",
            command=lambda: parent.focus_get().event_generate("<<SelectAll>>"),
        )

    def show(self, event, widget):
        self.focused_widget = widget
        self.focused_widget.focus_set()
        self.focused_widget.icursor("end")
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

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


class DBPath:
    _db_path = None

    @classmethod
    def get_or_init_db_path(cls):
        if cls._db_path is None:
            if getattr(sys, "frozen", False):
                dir_path = sys._MEIPASS
            else:
                dir_path = os.path.dirname(os.path.abspath(__file__))

            db_dir = os.path.join(dir_path, "data")

            if not os.path.exists(db_dir):
                os.makedirs(db_dir)

            cls._db_path = os.path.join(db_dir, "tab.db")

        return cls._db_path


class Instruction:
    @staticmethod
    def open_manual():
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            manual_path = os.path.join(script_dir, "../instruction.pdf")
            os.startfile(manual_path)
        except Exception as e:
            logging.error("Error: %s", e)