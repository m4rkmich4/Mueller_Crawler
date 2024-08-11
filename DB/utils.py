# DB/utils.py
def clean_product_data(product_data: dict) -> dict:
    """
    Bereinigt die Produktdaten:
    - Wandelt 'GesamtRating' in float um.
    - Wandelt 'Gesamtanzahl_Reviews' in int um.
    - Entfernt Währungszeichen und ersetzt Komma durch Punkt im 'Preis' und 'Promo_Preis', falls nicht 'N/A'.
    - Setzt Felder auf None, wenn 'unbekannt' in der JSON steht.
    
    :param product_data: Das ursprüngliche Produktdaten-Dictionary
    :return: Das bereinigte Produktdaten-Dictionary
    """
    def clean_price(price) -> float:
        if isinstance(price, str) and price not in ("N/A", "unbekannt", None):
            clean_price = price.replace("€", "").replace(",", ".").strip()
            return float(clean_price)
        elif isinstance(price, (int, float)):
            return float(price)
        else:
            return None

    def clean_field(value: str) -> str:
        return value if value not in ("unbekannt", None) else None

    product_data["GesamtRating"] = float(product_data["GesamtRating"]) if product_data["GesamtRating"] not in ("unbekannt", None) else None
    product_data["Gesamtanzahl_Reviews"] = int(product_data["Gesamtanzahl_Reviews"]) if product_data["Gesamtanzahl_Reviews"] not in ("unbekannt", None) else None
    product_data["Preis"] = clean_price(product_data["Preis"])
    product_data["Promo_Preis"] = clean_price(product_data["Promo_Preis"])

    product_data["Produkt_URL"] = clean_field(product_data["Produkt_URL"])
    product_data["Artikelnummer"] = clean_field(product_data["Artikelnummer"])
    product_data["Produktname"] = clean_field(product_data["Produktname"])
    product_data["Währung"] = clean_field(product_data["Währung"])
    product_data["Marke"] = clean_field(product_data["Marke"])
    product_data["Artikelbeschreibung"] = clean_field(product_data["Artikelbeschreibung"])
    product_data["Inhaltsstoffe"] = clean_field(product_data["Inhaltsstoffe"])

    return product_data

def clean_review_data(review_data: dict) -> dict:
    """
    Bereinigt die Bewertungsdaten:
    - Setzt Felder auf None, wenn 'unbekannt' in der JSON steht.
    - Wandelt 'Rating', 'Review_Count' und 'Review_Votes' in int um.
    
    :param review_data: Das ursprüngliche Bewertungsdaten-Dictionary
    :return: Das bereinigte Bewertungsdaten-Dictionary
    """
    def clean_field(value: str) -> str:
        return value if value not in ("unbekannt", None) else None

    review_data["Rating"] = int(review_data["Rating"]) if review_data["Rating"] not in ("unbekannt", None) else None
    review_data["Review_Count"] = int(review_data["Review_Count"]) if review_data["Review_Count"] not in ("unbekannt", None) else None
    review_data["Review_Votes"] = int(review_data["Review_Votes"]) if review_data["Review_Votes"] not in ("unbekannt", None) else None

    review_data["Reviewer"] = clean_field(review_data["Reviewer"])
    review_data["Review"] = clean_field(review_data["Review"])
    review_data["Date"] = clean_field(review_data["Date"])
    review_data["Author_Location"] = clean_field(review_data["Author_Location"])
    review_data["Gender"] = clean_field(review_data["Gender"])
    review_data["Age"] = clean_field(review_data["Age"])

    return review_data
