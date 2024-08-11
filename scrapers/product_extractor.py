import logging
import re
import time
import random
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ProductExtractor:
    """
    Eine Klasse, um Produktdetails von einer Produktseite zu extrahieren.
    """

    def __init__(self, driver):
        """
        Initialisiert die ProductExtractor-Klasse.

        Parameter:
        driver (WebDriver): Der Selenium WebDriver.
        """
        self.driver = driver
        self.currency_map = {
            '€': 'EUR',
            '$': 'USD',
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR',
            'CHF': 'CHF'  # Hinzufügen von CHF ohne Sonderzeichen
        }

    def clean_text(self, text):
        """
        Bereinigt den gegebenen Text, indem unerwünschte Zeichen entfernt werden.

        Parameter:
        text (str): Der zu bereinigende Text.

        Rückgabe:
        str: Der bereinigte Text.
        """
        text = re.sub(r'\s+', ' ', text)  # Ersetze alle Arten von Leerzeichen durch ein einzelnes Leerzeichen
        text = text.replace('\xa0',
                            ' ').strip()  # Ersetze \xa0 durch ein Leerzeichen und entferne führende/nachfolgende Leerzeichen
        text = re.sub(r'[()]+', '', text)  # Entferne Klammern
        return text

    def random_sleep(self, min_seconds=0.5, max_seconds=1.5):
        """
        Führt eine zufällige Schlafzeit zwischen min_seconds und max_seconds durch.

        Parameter:
        min_seconds (float): Minimale Schlafzeit.
        max_seconds (float): Maximale Schlafzeit.
        """
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)

    def wait_for_element(self, xpath, timeout=10):
        """
        Wartet, bis ein bestimmtes Element erscheint.

        Parameter:
        xpath (str): Der XPath des gesuchten Elements.
        timeout (int): Die maximale Wartezeit für das Element.

        Rückgabe:
        WebElement: Das gefundene Element oder None, wenn das Element nicht gefunden wurde.
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return element
        except Exception:
            return None

    def extract_product_details(self, url):
        """
        Extrahiert die Produktdetails von der angegebenen Produktseite.

        Parameter:
        url (str): Die URL der Produktseite.

        Rückgabe:
        dict: Ein Dictionary mit den extrahierten Produktdetails.
        """
        logging.info(f"Rufe Produktseite auf: {url}")
        self.driver.get(url)

        # Scrollen, um sicherzustellen, dass die Seite vollständig geladen ist
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.random_sleep(1, 2)
        self.driver.execute_script("window.scrollTo(0, 0);")
        self.random_sleep(1, 2)

        # Warten, bis die Seite vollständig geladen ist
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Artikelnummer
        article_number_element = soup.select_one('.mu-product-details-page__article-number')
        article_number = self.clean_text(
            article_number_element.text.replace('Art.Nr.', '')) if article_number_element else 'Unbekannt'
        logging.info(f"Artikelnummer extrahiert: {article_number}")

        # Produktname
        product_name_element = soup.select_one('.mu-product-details-page__product-name')
        product_name = self.clean_text(product_name_element.text) if product_name_element else 'Unbekannt'
        logging.info(f"Produktname extrahiert: {product_name}")

        # Preis und Währung
        price_element = soup.select_one('div.mu-product-price__price-container span.mu-product-price__price')
        promo_price_element = soup.select_one(
            'div.mu-product-price__price-container span.mu-product-price__price--promo')

        if promo_price_element:
            price = self.clean_text(price_element.text) if price_element else 'Unbekannt'
            promo_price = self.clean_text(promo_price_element.text)
            on_promo = True
        else:
            price = self.clean_text(price_element.text) if price_element else 'Unbekannt'
            promo_price = 'N/A'
            on_promo = False

        currency = 'Unbekannt'
        for symbol, curr in self.currency_map.items():
            if symbol in price:
                currency = curr
                price = price.replace(symbol, '').strip()
                break
        logging.info(f"Preis extrahiert: {price} {currency}")
        logging.info(f"Promo Preis extrahiert: {promo_price} {currency}")
        logging.info(f"On Promo: {on_promo}")

        # Marke
        brand_element = soup.select_one('a.mu-product-details-page__brand img')
        brand = self.clean_text(brand_element['alt']) if brand_element else 'Unbekannt'
        logging.info(f"Marke extrahiert: {brand}")

        # Artikelbeschreibung
        description_element = soup.select_one('.mu-product-description__text')
        description = self.clean_text(description_element.text) if description_element else 'Unbekannt'
        logging.info("Artikelbeschreibung extrahiert.")

        # Inhaltsstoffe
        ingredients_element = soup.select_one('td:-soup-contains("Inhaltsstoffe") + td')
        ingredients = self.clean_text(ingredients_element.text) if ingredients_element else 'Unbekannt'
        logging.info("Inhaltsstoffe extrahiert.")

        # Gesamtrating und Gesamtanzahl der Reviews
        rating_button_xpath = '//*[@id="page"]/main/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/button'

        # Versuche, das Element zu finden (maximal 3 Versuche)
        attempts = 0
        rating_button = None
        while attempts < 3 and not rating_button:
            rating_button = self.wait_for_element(rating_button_xpath, 10)
            if not rating_button:
                attempts += 1
                logging.warning(f"Element nicht gefunden (Versuch {attempts}), Seite wird neu geladen...")
                self.driver.refresh()
                self.random_sleep(1, 2)
                logging.info("Seite neu geladen")

        if not rating_button:
            logging.warning("Element nach 3 Versuchen nicht gefunden, fahre ohne Gesamtrating fort.")
            overall_rating = '0'
            total_reviews = '0'
        else:
            overall_rating_xpath = '//*[@id="page"]/main/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/button/div[2]'
            total_reviews_xpath = '//*[@id="page"]/main/div[1]/div/div[1]/div[2]/div[1]/div[3]/div/button/div[3]/div'

            overall_rating_element = self.wait_for_element(overall_rating_xpath, 5)
            total_reviews_element = self.wait_for_element(total_reviews_xpath, 5)

            overall_rating = self.clean_text(overall_rating_element.text) if overall_rating_element else '0'
            total_reviews = self.clean_text(
                total_reviews_element.text.replace('(', '').replace(')', '').strip()) if total_reviews_element else '0'

        logging.info(f"Gesamtrating extrahiert: {overall_rating}")
        logging.info(f"Gesamtanzahl der Reviews extrahiert: {total_reviews}")

        logging.info(f"Produktdetails extrahiert zu -->  {product_name}, {article_number}")
        logging.info("=" * 100 + "\n")

        return {
            'Produkt_URL': url,
            'Artikelnummer': article_number,
            'Produktname': product_name,
            'Preis': price,
            'Promo_Preis': promo_price,
            'on_promo': on_promo,
            'Währung': currency,
            'Marke': brand,
            'Artikelbeschreibung': description,
            'Inhaltsstoffe': ingredients,
            'GesamtRating': overall_rating,
            'Gesamtanzahl_Reviews': total_reviews
        }
