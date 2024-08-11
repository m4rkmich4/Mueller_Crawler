import logging
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import time
import random

# Konfiguration des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LinkExtractor:
    """
    Eine Klasse, um Produktlinks von einer Webseite zu extrahieren.
    """

    def __init__(self, driver, base_url):
        """
        Initialisiert die LinkExtractor-Klasse.

        Parameter:
        driver (WebDriver): Der Selenium WebDriver.
        base_url (str): Die Basis-URL der Webseite, die durchsucht werden soll.
        """
        self.driver = driver
        self.base_url = base_url

    def extract_product_links(self):
        """
        Extrahiert alle Produktlinks von der Webseite, einschließlich aller Seiten.

        Rückgabe:
        list: Eine Liste von Produktlinks.
        """
        all_links = []  # Liste zur Speicherung aller gefundenen Links
        page_number = 1  # Startseite

        while True:
            logging.info(f"Extrahiere Links von Seite {page_number}...")

            # Abrufen des Seitenquelltexts
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Finden aller Produktkacheln
            product_tiles = soup.find_all('a', class_='mu-product-tile mu-product-list__item')
            links = [tile['href'] for tile in product_tiles if 'href' in tile.attrs]
            all_links.extend(links)  # Hinzufügen der gefundenen Links zur Gesamtliste

            # Überprüfen, ob eine nächste Seite vorhanden ist und ob der Button klickbar ist
            next_button = self.driver.find_elements(By.CSS_SELECTOR, 'button.mu-pagination__navigation--next')
            if next_button and 'disabled' not in next_button[0].get_attribute('class'):
                # Zur nächsten Seite navigieren
                page_number += 1
                next_url = self.base_url if page_number == 1 else f"{self.base_url}?p={page_number}"
                logging.info(f"Weiter zu Seite {page_number}: {next_url}...")
                self.driver.get(next_url)
                time.sleep(random.randint(3, 5))  # Warte, bis die nächste Seite geladen ist
            else:
                logging.info("Keine weiteren Seiten.")
                break
        logging.info(f"Es wurden {len(all_links)} Produkte extrahiert ")
        logging.info("=" * 100 + "\n\n")
        return all_links
