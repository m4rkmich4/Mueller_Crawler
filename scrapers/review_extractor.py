import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class ReviewExtractor:
    """
    Eine Klasse, um Produktbewertungen von einer Produktseite zu extrahieren.
    """

    def __init__(self, driver):
        """
        Initialisiert die ReviewExtractor-Klasse.

        Parameter:
        driver (WebDriver): Der Selenium WebDriver.
        """
        self.driver = driver

    def extrahiere_reviews_von_seite(self, html):
        """
        Extrahiert alle Bewertungen von einer einzelnen Seite.

        Parameter:
        html (str): Der HTML-Quelltext der Seite.

        Rückgabe:
        list: Eine Liste von Dictionaries mit den extrahierten Bewertungen.
        """
        soup = BeautifulSoup(html, 'html.parser')
        reviews = []
        review_elements = soup.select('ol.bv-content-list > li.bv-content-item')
        for element in review_elements:
            reviewer_element = element.select_one('.bv-author')
            review_text_element = element.select_one('.bv-content-summary-body-text')
            review_rating_element = element.select_one('.bv-rating-stars-container > abbr')
            review_date_element = element.select_one('.bv-content-datetime .bv-content-datetime-stamp')

            author_location_element = element.select_one('.bv-author-location span')
            review_count_element = element.select_one('.bv-author-userstats-reviews .bv-author-userstats-value')
            review_votes_element = element.select_one('.bv-author-userstats-votes .bv-author-userstats-value')

            # Suche nach Geschlecht und Alter in der Liste
            user_info_elements = element.select('.bv-author-userinfo .bv-author-userinfo-value')

            if reviewer_element and review_text_element and review_rating_element and review_date_element:
                reviewer = reviewer_element.get_text(strip=True)
                review_text = review_text_element.get_text(strip=True)
                review_rating = int(
                    review_rating_element['title'].split()[0])  # Extrahiere den Titel und konvertiere zu int
                review_date = review_date_element.get_text(strip=True)

                author_location = author_location_element.get_text(
                    strip=True) if author_location_element else 'Unbekannt'
                review_count = int(review_count_element.get_text(strip=True)) if review_count_element else 0
                review_votes = int(review_votes_element.get_text(strip=True)) if review_votes_element else 0

                # Extrahiere Geschlecht und Alter
                author_gender = user_info_elements[0].get_text(strip=True) if len(
                    user_info_elements) > 0 else 'Unbekannt'
                author_age = user_info_elements[1].get_text(strip=True) if len(user_info_elements) > 1 else 'Unbekannt'

                reviews.append({
                    'Reviewer': reviewer,
                    'Review': review_text,
                    'Rating': review_rating,
                    'Date': review_date,
                    'Author_Location': author_location,
                    'Review_Count': review_count,
                    'Review_Votes': review_votes,
                    'Gender': author_gender,
                    'Age': author_age
                })
            else:
                logging.warning("Ein Rezensionselement konnte nicht vollständig extrahiert werden.")
        return reviews

    def check_for_reviews(self):
        """
        Überprüft, ob das Review-Container-Element vorhanden ist.

        Rückgabe:
        bool: True, wenn das Element gefunden wird, sonst False.
        """
        try:
            reviews_container = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, 'BVRRContainer'))
            )
            logging.info("Review-Element gefunden. Extraktion kann beginnen.")
            return True
        except TimeoutException:
            logging.warning("Review-Element nicht gefunden.")
            return False

    def extract_reviews(self, url, artikelnummer, produktname,
                        max_reviews=300):  # Erhöhen Sie die maximale Anzahl der Reviews auf 300

        reviews = []
        self.driver.get(url)
        logging.info(f"Extrahiere Reviews: {url}")

        # Überprüfen, ob das Review-Element vorhanden ist, und gegebenenfalls die Seite neu laden (bis zu 5 Versuche)
        for attempt in range(1, 6):
            if self.check_for_reviews():
                break
            else:
                logging.warning(f"Versuch {attempt} - Seite wird neu geladen.")
                self.driver.refresh()
                time.sleep(random.randint(1, 6))  # Wartezeit nach dem Neuladen der Seite
                if attempt == 5:
                    logging.info("Keine Reviews nach 5 Neuladeversuchen gefunden. Beenden der Extraktion.")
                    return reviews

        # Scrollen, um sicherzustellen, dass die Seite vollständig geladen ist
        for _ in range(2):  # Reduzierte Anzahl der Scrollvorgänge
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(self.driver, 1).until(lambda d: d.execute_script("return document.readyState") == "complete")
            self.driver.execute_script("window.scrollTo(0, 0);")
            WebDriverWait(self.driver, 1).until(lambda d: d.execute_script("return document.readyState") == "complete")

        # Warten, bis die Seite vollständig geladen ist
        WebDriverWait(self.driver, 20).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # Erste Extraktion durchführen
        time.sleep(2)  # Warten, um sicherzustellen, dass die Seite vollständig geladen ist
        html = self.driver.page_source
        extracted_reviews = self.extrahiere_reviews_von_seite(html)
        reviews.extend(extracted_reviews)
        logging.info(f"{len(extracted_reviews)} neue Reviews extrahiert, insgesamt {len(reviews)} Reviews.")

        # Überprüfen der Anzahl der extrahierten Reviews
        if len(extracted_reviews) < 8:
            logging.info("Weniger als 8 Reviews extrahiert, Beenden der Extraktion.")
            logging.info(f"Insgesamt {len(reviews)} Reviews extrahiert.")
            logging.info("=" * 100 + "\n")
            return reviews

        # Normale Überprüfung des "Weiter"-Buttons und Fortsetzung der Extraktion
        while len(reviews) < max_reviews:
            try:
                next_button = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="BVRRContainer"]/div/div/div/div/div[3]/div/ul/li[2]/a'))
                )
                if 'bv-content-pagination-buttons-item-disabled' in next_button.get_attribute('class') or len(
                        reviews) >= max_reviews:
                    logging.info(
                        "Weiter-Button ist deaktiviert oder maximale Anzahl an Reviews erreicht, Beenden der Extraktion.")
                    break
                else:
                    # Scrollen, um sicherzustellen, dass der "Weiter"-Button sichtbar ist
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    # Klick mithilfe von JavaScript ausführen
                    self.driver.execute_script("arguments[0].click();", next_button)
                    # Warten, bis die neue Seite geladen ist
                    WebDriverWait(self.driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    time.sleep(2)  # Warten, um sicherzustellen, dass die Seite vollständig geladen ist

                    # Extrahiere Reviews der nächsten Seite
                    html = self.driver.page_source
                    extracted_reviews = self.extrahiere_reviews_von_seite(html)
                    reviews.extend(extracted_reviews)
                    logging.info(f"{len(extracted_reviews)} neue Reviews extrahiert, insgesamt {len(reviews)} Reviews.")
            except Exception as e:
                logging.info("Kein 'Weiter'-Button gefunden, Beenden der Extraktion.")
                break

        logging.info(f"Insgesamt {len(reviews)} Reviews extrahiert.")
        logging.info("=" * 100 + "\n")
        return reviews
