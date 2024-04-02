import logging
import configparser
import requests
from bs4 import BeautifulSoup as BS
from modules.kaspidriver import setup_driver_kaspi
from modules.ozondriver import setup_driver_ozon

config = configparser.ConfigParser()
config.read("settings.ini")

min_reviews_count = config.getint("DEFAULT", "min_reviews_count")


def extract_product_info(url):
    if "flip" in url:
        return extract_info_flip(url)
    elif "technodom" in url:
        return extract_info_technodom(url)
    elif "kaspi" in url:
        return extract_info_kaspi(url)
    elif "ozon" in url:
        return extract_info_ozon(url)
    else:
        return None, "Магазин не поддерживается", 0


def extract_info_flip(url):
    if "flip" not in url:
        return None, "Ссылка не содержит 'flip'", 0

    try:
        response = requests.get(url)
        html = BS(response.content, "html.parser")

        item = html.find("h1").text if html.find("h1") else "Имя продукта не найдено"

        try:
            information = html.find("span", itemprop="description").text
        except:
            information = "Информации нет"

        try:
            meta_tag = html.find("meta", {"itemprop": "price"})
            price = int(meta_tag["content"])
        except:
            try:
                price_text = html.find("span", class_="text_att").text
                price = int(price_text.replace("₸", "").strip())
            except:
                price = 0
                information = "Товара нет в наличии"

        return item, information, price
    except Exception as e:
        return None, f"Ошибка при запросе: {str(e)}", 0


def extract_info_technodom(url):
    if "technodom" not in url:
        return None, "Ссылка не содержит 'technodom'", 0
    try:
        r = requests.get(url)
        html = BS(r.content, "html.parser")
        item = html.find("h1").text
        information = "Для дополнительной информации перейдите на страницу товара"
        try:
            price_text = html.find(
                "p",
                class_="Typography ProductPricesVariantB_accented__n2rtH Typography__Heading Typography__Heading_H1",
            ).text
            price_text = price_text.replace("\xa0", "").replace("₸", "").strip()
            price = int(price_text.replace(" ", ""))
        except:
            price = 0
            information = "Товара нет в наличии"
        return item, information, price
    except:
        item = "Снят с продажи"
        price = 0
        information = "Для дополнительной информации перейдите на страницу товара"
        return item, information, price


def extract_info_kaspi(url):
    try:
        html = setup_driver_kaspi(url)
        if html is None:
            logging.error(
                "Не удалось получить данные с kaspi, переход к следующей записи"
            )
            return None
        soup = BS(html, "html.parser")
    except Exception as e:
        logging.error("Error: %s", e)

    try:
        item = soup.find("h1", class_="item__heading").text.strip()
    except:
        item = "Информации нет"
    try:
        description = soup.find("div", class_="item__description-text")
        description_items = description.find_all("li")
        information = " / ".join(item.get_text().strip() for item in description_items)
    except:
        information = "Информации нет"
    try:
        sellers_rows = soup.find_all("tr")
        for seller_row in sellers_rows:
            reviews_link = seller_row.find("a", class_="rating-count")
            if reviews_link:
                reviews_text = reviews_link.text.strip()
                reviews_count = int("".join(filter(str.isdigit, reviews_text)))

                if reviews_count >= min_reviews_count:
                    price_text = seller_row.find(
                        "div", class_="sellers-table__price-cell-text"
                    ).text.strip()
                    price = int("".join(filter(str.isdigit, price_text)))
                    break
        else:
            price_text = soup.find("div", class_="item__price-once").text.strip()
            price = int("".join(filter(str.isdigit, price_text)))

            if price is None:
                logging.warning(f"No price was found for the product at Kaspi")
                return "skip", None
            else:
                logging.warning(
                    f"There is no suitable store with enough reviews on Kaspi"
                )
                return "second_check", item, information, price
    except Exception as e:
        logging.error(
            f"There was an error when searching for the price of an item on Kaspi:{url}: {e}"
        )
        price = None
        item = "Товара нет в наличии"
    return item, information, price


def extract_info_ozon(url):
    try:
        html = setup_driver_ozon(url)
        if html == "webOutOfStock":
            return "webOutOfStock"

        if html is None:
            logging.error("Failed to retrieve data from ozon, skip to next entry")
            return None
        soup = BS(html, "html.parser")
    except Exception as e:
        logging.error(f"Error: {e}")
    try:
        item = soup.find(attrs={"data-widget": "webProductHeading"})
        item = item.get_text().strip()
    except:
        item = "Информации нет"
    try:
        price_block = soup.find(attrs={"data-widget": "webSale"})
        price_text = price_block.get_text().strip()
        price_text = price_text.split("₸")[0]
        price = int("".join(filter(str.isdigit, price_text)))
    except:
        price = 0
        item = "Товара нет в наличии"
    try:
        description_block = soup.select_one('div[data-widget="webDescription"]')
        information = description_block.get_text().strip()
    except:
        information = "Информации нет"
    return item, information, price
