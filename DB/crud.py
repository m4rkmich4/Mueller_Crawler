# DB/crud.py
from sqlalchemy.orm import Session
from datetime import date, time
from . import models


def create_product(db: Session, product_data: dict, session_date: date, session_time: time):
    """
    Fügt ein neues Produkt zur Datenbank hinzu.
    :param db: Die Datenbank-Session
    :param product_data: Ein Dictionary mit den Produktdaten
    :param session_date: Datum der Crawling-Session
    :param session_time: Uhrzeit der Crawling-Session
    :return: Das hinzugefügte Produkt
    """
    db_product = models.Product(
        product_url=product_data["Produkt_URL"],
        artikelnummer=product_data["Artikelnummer"],
        produktname=product_data["Produktname"],
        preis=product_data["Preis"],
        promo_preis=product_data["Promo_Preis"],
        on_promo=product_data["on_promo"],
        waehrung=product_data["Währung"],
        marke=product_data["Marke"],
        artikelbeschreibung=product_data["Artikelbeschreibung"],
        inhaltsstoffe=product_data["Inhaltsstoffe"],
        gesamtrating=product_data["GesamtRating"],
        gesamtanzahl_reviews=product_data["Gesamtanzahl_Reviews"],
        produkt_id=product_data["Produkt_ID"],
        session_date=session_date,
        session_time=session_time
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def create_review(db: Session, review_data: dict, session_date: date, session_time: time):
    """
    Fügt eine neue Bewertung zur Datenbank hinzu.
    :param db: Die Datenbank-Session
    :param review_data: Ein Dictionary mit den Bewertungsdaten
    :param session_date: Datum der Crawling-Session
    :param session_time: Uhrzeit der Crawling-Session
    :return: Die hinzugefügte Bewertung
    """
    db_review = models.Review(
        reviewer=review_data["Reviewer"],
        review=review_data["Review"],
        rating=review_data["Rating"],
        date=review_data["Date"],
        author_location=review_data["Author_Location"],
        review_count=review_data["Review_Count"],
        review_votes=review_data["Review_Votes"],
        gender=review_data["Gender"],
        age=review_data["Age"],
        review_id=review_data["Review_ID"],
        produkt_id=review_data["Produkt_ID"],
        session_date=session_date,
        session_time=session_time
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
