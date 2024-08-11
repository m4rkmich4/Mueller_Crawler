import time
import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from chromedriver_py import binary_path
from scrapers.browser_settings import get_chrome_options, clear_cache

# Konfiguration des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class WebCrawler:
    """
    Eine Klasse, die einen Web-Crawler für das Extrahieren von Webseiten-Inhalten darstellt.
    """

    def __init__(self, url: str):
        """
        Initialisiert die WebCrawler-Klasse.

        Parameter:
        url (str): Die URL der zu besuchenden Webseite.
        """
        self.url = url

        # Verbindung zur URL prüfen
        self.headers = self.get_request_headers()
        self.check_url_connection()

        # Cache löschen bevor der Browser gestartet wird
        clear_cache()

        # Browser-Optionen festlegen
        chrome_options = get_chrome_options()

        # Chrome-Dienst starten
        self.svc = Service(executable_path=binary_path)

        # WebDriver initialisieren
        self.driver = webdriver.Chrome(service=self.svc, options=chrome_options)

        # Die angegebene URL laden
        self.driver.get(self.url)
        logging.info(f"WebDriver gestartet und URL {url} geladen.")

    def get_request_headers(self):
        """
        Holt die Headers der Anfrage.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9',
            'Referer': 'https://google.com',
        }
        return headers

    def check_url_connection(self):
        """
        Überprüft die Verbindung zur URL und gibt entsprechende Statusmeldungen aus.
        """
        try:
            # SSL-Überprüfung deaktivieren
            response = requests.get(self.url, headers=self.headers, verify=False)
            if response.status_code == 200:
                logging.info(f"Verbindung zur URL {self.url} erfolgreich, Statuscode: {response.status_code}")
            elif 400 <= response.status_code < 500:
                logging.error(
                    f"Client-Fehler bei der Verbindung zur URL {self.url}, Statuscode: {response.status_code}")
                raise Exception(
                    f"Client-Fehler: Kann nicht auf URL {self.url} zugreifen, Statuscode: {response.status_code}")
            elif 500 <= response.status_code < 600:
                logging.error(
                    f"Server-Fehler bei der Verbindung zur URL {self.url}, Statuscode: {response.status_code}")
                raise Exception(
                    f"Server-Fehler: Kann nicht auf URL {self.url} zugreifen, Statuscode: {response.status_code}")
        except requests.exceptions.SSLError as e:
            logging.error(f"SSL-Fehler bei der Verbindung zur URL {self.url}: {e}")
            raise
        except Exception as e:
            logging.error(f"Ein Fehler ist bei der Verbindung zur URL {self.url} aufgetreten: {e}")
            raise

    def accept_cookies(self):
        """
        Akzeptiert Cookies auf der Webseite, falls vorhanden.
        """
        try:
            logging.info("Versuche, das Cookie-Banner zu akzeptieren...")
            # Warten, bis das Cookie-Banner geladen ist
            wait = WebDriverWait(self.driver, 15)
            shadow_host = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div#usercentrics-root')))

            # Zugriff auf das Shadow DOM
            shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', shadow_host)

            # Warten, bis der Akzeptieren-Button klickbar ist
            accept_button = WebDriverWait(shadow_root, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="uc-accept-all-button"]'))
            )

            # Akzeptieren-Button klicken
            accept_button.click()
            logging.info("Cookies wurden akzeptiert.")
        except Exception as e:
            # Fehlerbehandlung, falls etwas schiefgeht
            logging.error(f"Ein Fehler ist beim Klicken auf den Cookie-Button aufgetreten: {e}")

    def fetch_page_source(self) -> str:
        """
        Ruft den Seitenquelltext der aktuellen Seite ab.

        Rückgabe:
        str: Der HTML-Seitenquelltext.
        """
        logging.info("Cookies werden akzeptiert, falls vorhanden.")
        # Cookies akzeptieren, falls das Banner vorhanden ist
        self.accept_cookies()

        # Warten, bis die Seite vollständig geladen ist
        logging.info("Warte, bis die Seite vollständig geladen ist...")
        time.sleep(5)

        # Seitenquelltext abrufen
        page_source = self.driver.page_source
        logging.info("Seitenquelltext abgerufen.")
        logging.info("=" * 100 + "\n\n")
        return page_source

    def close(self):
        """
        Schließt den WebDriver und beendet die Browser-Sitzung.
        """
        # WebDriver schließen
        self.driver.quit()
        logging.info("WebDriver geschlossen und Browser-Sitzung beendet.")
