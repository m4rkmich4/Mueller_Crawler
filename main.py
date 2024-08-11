# main.py
import os
import json
import logging
from datetime import datetime, date, time
from scrapers.web_crawler import WebCrawler
from scrapers.link_extractor import LinkExtractor
from scrapers.product_extractor import ProductExtractor
from scrapers.review_extractor import ReviewExtractor
from sqlalchemy.orm import Session
from DB.database import SessionLocal, engine
from DB import crud, models
from DB.utils import clean_product_data, clean_review_data

# TESTMODE-Schalter, für normalbetrieb auf False lassen !!!
TESTMODE = False 
NUMBER_OF_PRODUCTS = 7

# Timestamp für Log-Dateinamen und Ordner
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
session_datetime = datetime.now()
session_date = session_datetime.date()
session_time = session_datetime.time()
session_dir = os.path.join("Output", f"Crawler_Session_{timestamp}")
os.makedirs(session_dir, exist_ok=True)

# Logging-Konfiguration
log_filename = os.path.join(session_dir, f'crawler_log_{timestamp}.txt')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Entferne alle vorhandenen Handler
if logger.hasHandlers():
    logger.handlers.clear()

# File handler for logging to a file
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Stream handler for logging to console
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)

# Funktion zum Protokollieren des Startens und Endens einer Funktion
def log_function_call(func):
    def wrapper(*args, **kwargs):
        logging.info(f"Starting {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"Finished {func.__name__}")
        return result
    return wrapper

# URL der Produktseite
url = "https://www.mueller.de/parfuemerie/duefte-fuer-ihn/duefte/"

@log_function_call
def main():
    # Erstellen Sie die Datenbanktabellen (falls sie nicht bereits existieren)
    logging.info("Erstelle Datenbanktabellen...")
    models.Base.metadata.create_all(bind=engine)
    logging.info("Datenbanktabellen erstellt.")

    # Instanz der WebCrawler-Klasse erstellen und Seite abrufen
    crawler = WebCrawler(url)
    crawler.fetch_page_source()
    
    # Instanz der LinkExtractor-Klasse erstellen und alle Produktlinks extrahieren
    link_extractor = LinkExtractor(crawler.driver, url)
    all_product_links = link_extractor.extract_product_links()

    # Instanz der ProductExtractor-Klasse erstellen
    product_extractor = ProductExtractor(crawler.driver)

    # Produktdetails extrahieren
    product_data = []
    review_product_data = []

    # Anzahl der zu besuchenden Produktseiten basierend auf TESTMODE
    num_products_to_visit = NUMBER_OF_PRODUCTS if TESTMODE else len(all_product_links)

    # Verarbeiten der Produktlinks
    product_id = 1
    for link in all_product_links[:num_products_to_visit]:
        try:
            logging.info(f"Verarbeite Produkt-ID: {product_id}")
            product_details = product_extractor.extract_product_details(link)
            product_details['Produkt_ID'] = product_id

            # Struktur für JSON-Datei vorbereiten
            product_data.append(clean_product_data(product_details))

            # Überprüfen, ob das Produkt ein Rating größer als 0 hat
            if float(product_details.get('GesamtRating', 0)) > 0:
                review_product_data.append(product_details)

            product_id += 1

        except Exception as e:
            logging.error(f"Fehler beim Verarbeiten des Links {link}: {e}")

    crawler.close()

    # Produktdaten in JSON-Datei speichern
    product_json_filename = os.path.join(session_dir, f'produkte_{timestamp}.json')
    save_clean_json(product_json_filename, product_data)
    logging.info(f"Produktdaten wurden in '{product_json_filename}' gespeichert.")

    # ----------------------------
    # Schritt 2: Reviews extrahieren
    # ----------------------------

    # Logging-Konfiguration für Review-Crawler
    crawler = WebCrawler(url)
    crawler.fetch_page_source()

    # Instanz des ReviewExtractor erstellen
    review_extractor = ReviewExtractor(crawler.driver)

    # Reviews extrahieren
    reviews_data = []

    review_id = 1

    for product in review_product_data:
        try:
            product_id = product['Produkt_ID']
            product_url = product['Produkt_URL']
            logging.info(f"Extrahiere Reviews für Produkt-ID: {product_id}")

            # Extrahiere Reviews für das Produkt
            product_reviews = review_extractor.extract_reviews(product_url, product['Artikelnummer'], product['Produktname'])

            # Füge die Produkt_ID und eine eindeutige Review_ID zu jedem Review hinzu
            for review in product_reviews:
                review['Review_ID'] = review_id
                review['Produkt_ID'] = product_id
                reviews_data.append(clean_review_data(review))
                review_id += 1

        except Exception as e:
            logging.error(f"Fehler beim Extrahieren der Reviews für Produkt {product['Produkt_URL']}: {e}")

    crawler.close()

    # Review-Daten in JSON-Datei speichern
    review_json_filename = os.path.join(session_dir, f'reviews_{timestamp}.json')
    save_clean_json(review_json_filename, reviews_data)
    logging.info(f"Review-Daten wurden in '{review_json_filename}' gespeichert.")

    # ----------------------------
    # Schritt 3: Daten in die Datenbank einfügen
    # ----------------------------
    insert_data_into_db(session_date, session_time)

def save_clean_json(file_path, data):
    """
    Speichert die JSON-Daten in einer Datei und entfernt ungewöhnliche Zeilenabschlusszeichen.
    :param file_path: Pfad zur JSON-Datei
    :param data: Daten, die gespeichert werden sollen
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    # Entferne ungewöhnliche Zeilenabschlusszeichen
    json_str = json_str.replace('\u2028', '').replace('\u2029', '')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_str)

def insert_data_into_db(session_date, session_time):
    def load_json(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def get_json_files(directory):
        """
        Gibt die JSON-Dateien in einem Verzeichnis zurück, außer .txt-Dateien
        :param directory: Das Verzeichnis, das durchsucht werden soll
        :return: Eine Liste der JSON-Dateien
        """
        return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.json')]

    def get_all_json_files(root_directory):
        """
        Gibt alle JSON-Dateien in allen Unterverzeichnissen eines Root-Verzeichnisses zurück
        :param root_directory: Das Root-Verzeichnis
        :return: Eine Liste der JSON-Dateien
        """
        all_json_files = []
        for subdir in os.listdir(root_directory):
            full_subdir_path = os.path.join(root_directory, subdir)
            if os.path.isdir(full_subdir_path):
                all_json_files.extend(get_json_files(full_subdir_path))
        return all_json_files

    # Alle JSON-Dateien im Output-Verzeichnis und dessen Unterverzeichnissen laden
    json_files = get_all_json_files('./Output')

    try:
        # DB-Session erstellen
        logging.info("Erstelle Datenbank-Sitzung...")
        db: Session = SessionLocal()
        logging.info("Datenbank-Sitzung erfolgreich erstellt.")

        # JSON-Dateien durchgehen und Daten zur Datenbank hinzufügen
        for json_file in json_files:
            data = load_json(json_file)
            if 'produkte' in json_file:
                for product in data:
                    crud.create_product(db, clean_product_data(product), session_date, session_time)
            elif 'reviews' in json_file:
                for review in data:
                    crud.create_review(db, clean_review_data(review), session_date, session_time)

    except Exception as e:
        logging.error(f"Fehler bei der Datenbank-Operation: {e}")
    finally:
        db.close()
        logging.info("Datenbank-Sitzung geschlossen.")

if __name__ == "__main__":
    main()
