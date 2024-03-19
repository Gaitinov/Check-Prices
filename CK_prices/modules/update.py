import requests
import logging
import configparser
from bs4 import BeautifulSoup as BS
from datetime import datetime
from modules.driver import setup_driver
from modules.ozondriver import setup_driver_ozon
import sqlite3
import os
import sys
from winotify import Notification

config = configparser.ConfigParser()
config.read("settings.ini")

interval = config.getint("DEFAULT", "price_range_notification")
price_range_notification = interval
interval = config.getint("DEFAULT", "price_range_for_save_to_db")
price_range_for_save_to_db = interval


def notifyex():
    try:
        toast = Notification(
            app_id="Check prices", title="Откройте приложение", msg="Цены изменились"
        )
        toast.show()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def update():
    # Настройка логирования
    logging.basicConfig(
        filename="app.log",
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    logging.info("Update start")
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
                html = setup_driver(link[i])
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
        elif "ozon" in link[i]:
            try:
                html = setup_driver_ozon(link[i])
                if html is None:
                    logging.error(
                        "Не удалось получить данные с ozon, переход к следующей записи"
                    )
                    continue
                soup = BS(html, "html.parser")
            except Exception as e:
                logging.error(f"Произошла ошибка: {e}")
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

                print(f"Price interval: {price_interval}")
                print(f"Price interval by product: {price_interval_by_product}")
                print(f"Price range for save to db: {price_range_for_save_to_db}")

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
    try:
        if price_interval > price_range_notification:
            notifyex()
            print("Уведомление")
        con.commit()
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
