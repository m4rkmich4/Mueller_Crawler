import shutil
import os
import logging
from selenium.webdriver.chrome.options import Options

# Konfiguration des Loggings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Funktion, um das temporäre Verzeichnis plattformunabhängig zu ermitteln
def get_temp_dir():
    if os.name == 'nt':  # Windows
        return os.getenv('TEMP')
    else:  # Unix-ähnliche Systeme (Linux, macOS)
        return '/tmp'

# Konstante für das Cache-Verzeichnis
CACHE_DIR = os.path.join(get_temp_dir(), 'chrome-user-data')

def clear_cache(cache_dir: str = CACHE_DIR):
    """
    Löscht den Chrome-Cache.

    Parameter:
    cache_dir (str): Das Verzeichnis, in dem die Chrome-Benutzerdaten gespeichert sind.
    """
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        logging.info(f"Cache-Verzeichnis {cache_dir} wurde gelöscht.")
    else:
        logging.info(f"Cache-Verzeichnis {cache_dir} existiert nicht. Keine Aktion erforderlich.")

def get_chrome_options() -> Options:
    """
    Erstellt und konfiguriert die Chrome-Optionen.

    Rückgabe:
    Options: Die konfigurierten Chrome-Optionen.
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Headless-Modus
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])

    # Verzeichnis für Benutzerprofildaten
    chrome_options.add_argument(f'--user-data-dir={CACHE_DIR}')

    logging.info("Chrome-Optionen wurden konfiguriert.")
    return chrome_options
