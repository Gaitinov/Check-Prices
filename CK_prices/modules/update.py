import logging
import configparser
from datetime import datetime
from modules.product_info_extractor import extract_product_info
import sqlite3
from winotify import Notification
from modules.config import DBPath

config = configparser.ConfigParser()
config.read("settings.ini")

price_range_notification = config.getint("DEFAULT", "price_range_notification")
check_price_interval = config.getint("DEFAULT", "check_price_interval")
price_range_for_save_to_db = config.getint("DEFAULT", "price_range_for_save_to_db")
min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


def notifyex():
    try:
        toast = Notification(
            app_id="Check prices", title="Откройте приложение", msg="Цены изменились"
        )
        toast.show()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def update_tray():
    logging.info("Update start")

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
                continue
            if result[0] == "skip":
                logging.warning(
                    f"There is no price for the product Kaspi:{link[i]}. Skip."
                )
                continue
            if result[0] == "second_check":
                logging.warning(f"Data not updated. Skip: {link[i]}")
                continue

            item, information, price = result

        elif "ozon" in link[i]:
            result = extract_product_info(link[i])
            if result is None:
                continue
            elif result == "webOutOfStock":
                item, information, price = "Товара нет в наличии", "Информации нет", 0
            else:
                item, information, price = result
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
        logging.error(f"Error: {e}")
