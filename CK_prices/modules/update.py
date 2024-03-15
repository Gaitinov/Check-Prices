import requests
import logging
import configparser
from bs4 import BeautifulSoup as BS
from datetime import datetime
from modules.driver import setup_driver
import sqlite3
import os
import sys
from plyer import notification

config = configparser.ConfigParser()
config.read('settings.ini')

interval = config.getint('DEFAULT', 'price_range_notification')
price_range_notification = interval

def notifyex():
    notification.notify(
        title="Check prices",
        message="Цены изменились",
        app_icon="images/icon.ico",
        timeout=10,
    )

def update():
    # Настройка логирования
    logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logging.info('Update start')
    if getattr(sys, 'frozen', False):
        dir_path = sys._MEIPASS
    else:
        dir_path = os.path.dirname(os.path.abspath(__file__))

    db_dir = os.path.join(dir_path, 'data')

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    db_path = os.path.join(db_dir, 'tab.db')

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    link = cur.execute(f"select link from items").fetchall()
    link = ([x[0] for x in link])
    link_count = len(link)
    changecount = 0
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

        elif "technodom" in link[i]:
            try:
                r = requests.get(link[i])
                html = BS(r.content, "html.parser")
                item = html.find("h1").text
                information = "Для дополнительной информации перейдите на страницу товара"
                try:
                    price = html.find('p', class_='Typography__Heading_H1').text
                    price = price.replace('₸', '')
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
                soup = BS(html, 'html.parser')
            except Exception as e:
                logging.error(f"Произошла ошибка: {e}")

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
            continue

        time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        timeall = cur.execute(f"select time from prices WHERE link = '{link[i]}'").fetchall()
        timeall = ([x[0] for x in timeall])
        record_count = len(timeall)
        if record_count != 0:
            lastrrecordtime = datetime.strptime(timeall[0], "%m/%d/%Y %H:%M:%S")
            for p in range(record_count):
                current_time = datetime.strptime(timeall[p], "%m/%d/%Y %H:%M:%S")
                if lastrrecordtime < current_time:
                    lastrrecordtime = current_time
            lastrrecordtime = lastrrecordtime.strftime(
                "%m/%d/%Y %H:%M:%S")
            lastrecordid = cur.execute(
                f"select id_record from prices WHERE link = '{link[i]}' AND time = '{lastrrecordtime}'").fetchone()[
                0]
            print(f"Last record ID: {lastrecordid}")

            lastprice = cur.execute(f"select price from prices WHERE id_record = '{lastrecordid}'").fetchone()[0]
            print(f"Last price: {lastprice}")

            if lastprice != price:
                print(f"Price change detected: {lastprice} -> {price}")
                id_item = str(cur.execute(f"select id_item from items WHERE link = '{link[i]}'").fetchone()[0])

                cur.execute("insert into prices (id_item, item, price, time, link, information) " +
                            "values (?, ? ,? , ? , ?, ?)",
                            (id_item, item, price, time, link[i], information))
                changecount = 1
                price_interval_by_product = lastprice - price
                # перевод интервала в положительное число
                if price_interval_by_product < 0:
                    price_interval_by_product = price_interval_by_product * -1
                if price_interval_by_product > price_interval:
                    price_interval = price_interval_by_product
                print(f"Price interval: {price_interval}")
                print(f"Price interval by product: {price_interval_by_product}")

                logging.info(f"Price change detected: {lastprice} -> {price}")


        else:
            id_item = str(cur.execute(f"select id_item from items WHERE link = '{link[i]}'").fetchone()[0])

            cur.execute("insert into prices (id_item, item, price, time, link, information) " +
                        "values (?, ? ,? , ? , ?, ?)",
                        (id_item, item, price, time, link[i], information))
    try:
        if changecount > 0 and price_interval > price_range_notification:
            notifyex()
            print("Уведомление")
        con.commit()
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")