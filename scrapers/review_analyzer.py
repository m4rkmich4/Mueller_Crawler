import os
import pandas as pd
import spacy
from tqdm import tqdm
from collections import Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from DB.models import Product, Review

class ReviewAnalyzer:
    """
    Eine Klasse zur Analyse von Kundenbewertungen, die in einer Datenbank gespeichert sind.

    Attribute
    ----------
    db_path : str
        Pfad zur SQLite-Datenbankdatei.
    output_dir : str
        Verzeichnis, in dem die Analyseergebnisse gespeichert werden.
    rating_filter : list of int
        Liste von Bewertungswerten, um die Reviews zu filtern.
    analysis_filename : str
        Basisname für die Ausgabedatei (CSV), die die Analyseergebnisse enthält.
    is_negative : bool, optional
        Flag, das angibt, ob die Analyse eine Logik für negative Bewertungen verwenden soll (Standard ist False).
    engine : sqlalchemy.engine.Engine
        SQLAlchemy-Engine zur Verbindung mit der Datenbank.
    SessionLocal : sqlalchemy.orm.sessionmaker
        SQLAlchemy-Session-Factory, die an die Datenbank-Engine gebunden ist.
    nlp : spacy.lang.de.German
        SpaCy-Sprachmodell für die Textanalyse auf Deutsch.
    """

    def __init__(self, db_path, output_dir, rating_filter, analysis_filename, is_negative=False):
        """
        Initialisiert den ReviewAnalyzer mit den angegebenen Parametern und richtet die Datenbankverbindung ein.

        Parameter
        ----------
        db_path : str
            Pfad zur SQLite-Datenbankdatei.
        output_dir : str
            Verzeichnis, in dem die Analyseergebnisse gespeichert werden.
        rating_filter : list of int
            Liste von Bewertungswerten, um die Reviews zu filtern.
        analysis_filename : str
            Basisname für die Ausgabedatei (CSV), die die Analyseergebnisse enthält.
        is_negative : bool, optional
            Flag, das angibt, ob die Analyse eine Logik für negative Bewertungen verwenden soll (Standard ist False).
        """        
        
        self.db_path = db_path
        self.output_dir = output_dir
        self.rating_filter = rating_filter
        self.analysis_filename = analysis_filename
        self.is_negative = is_negative  # Neuer Parameter zur Unterscheidung der Logik

        # Initialisiere die Datenbankverbindung
        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Lade das SpaCy Modell für die Textanalyse (Deutsch)
        try:
            self.nlp = spacy.load("de_core_news_sm")
        except OSError:
            from spacy.cli import download
            download("de_core_news_sm")
            self.nlp = spacy.load("de_core_news_sm")

    def analyze_reviews(self, reviews):

        """
        Analysiert die übergebenen Reviews, indem häufige Wortkombinationen extrahiert werden.

        Parameter
        ----------
        reviews : list of str
            Liste von Bewertungen als Text.

        Rückgabe
        ----------
        adj_noun_combinations : collections.Counter
            Zähler für häufige Kombinationen von Adjektiven und Nomen.
        verb_adj_combinations : collections.Counter
            Zähler für häufige Kombinationen von Verben und Adjektiven.
        """

        # Verbinde alle Reviews zu einem langen Text
        all_reviews_text = ' '.join(reviews)

        # Erstelle ein SpaCy-Dokument
        doc = self.nlp(all_reviews_text)

        # Häufige Wortkombinationen zählen
        adj_noun_combinations = Counter()
        verb_adj_combinations = Counter()

        for token in doc:
            # Verwende Lemmatization für Adjektive und deren zugehörige Nomen
            if token.pos_ == 'ADJ' and token.head.pos_ == 'NOUN':
                lemma_combo = f"{token.lemma_} {token.head.lemma_}"
                adj_noun_combinations[lemma_combo] += 1

            # Verwende Lemmatization für Adjektive und deren zugehörige Verben
            if token.pos_ == 'ADJ' and token.head.pos_ == 'VERB':
                lemma_combo = f"{token.lemma_} {token.head.lemma_}"
                verb_adj_combinations[lemma_combo] += 1

        return adj_noun_combinations, verb_adj_combinations

    def filter_combinations(self, combinations):

        """
        Filtert die gefundenen Wortkombinationen basierend auf ihrer Häufigkeit.

        Parameter
        ----------
        combinations : collections.Counter
            Zähler für Wortkombinationen, die gefiltert werden sollen.

        Rückgabe
        ----------
        filtered_combinations : dict
            Gefilterte Kombinationen, die den festgelegten Kriterien entsprechen.
        """

        # Unterschiedliche Filterlogik für negative Bewertungen
        if self.is_negative:
            # Weniger restriktive Logik: Erlaube auch Kombinationen, die nur einmal vorkommen
            filtered_combinations = {combo: count for combo, count in combinations.items() if count > 0}
        else:
            # Standard-Filterlogik: Nur Kombinationen mit mehr als 2 Vorkommen
            filtered_combinations = {combo: count for combo, count in combinations.items() if count > 2}
        
        return filtered_combinations
    
    def run_analysis(self):

        """
        Führt die vollständige Analyse durch, einschließlich des Abrufens der Bewertungen aus der Datenbank, 
        der Analyse und des Speicherns der Ergebnisse in einer CSV-Datei.
        """
        
    # Erstelle eine neue Session
        session = self.SessionLocal()

        try:
            # Abfrage: Alle Reviews mit den gewünschten Bewertungen abrufen und die zugehörigen Produkte joinen
            reviews = (
                session.query(Review)
                .join(Product, Review.produkt_id == Product.id)
                .filter(Review.rating.in_(self.rating_filter))
                .all()
            )

            reviews_data = [
                {
                    "review": review.review,
                    "rating": review.rating,
                    "produktname": review.product.produktname,
                    "marke": review.product.marke
                }
                for review in reviews
            ]

            # Erstelle DataFrame
            df_reviews = pd.DataFrame(reviews_data)

            results_combined = []

            grouped = df_reviews.groupby(['marke', 'produktname'])

            # Initialisiere den Fortschrittsbalken basierend auf der Anzahl der Gruppen (Marke/Produktname)
            with tqdm(total=len(grouped), desc="Analyse-Fortschritt der gefilterten Gruppen") as pbar:
                for (brand, product), group in grouped:
                    reviews_texts = group['review'].tolist()
                    adj_noun_combinations, verb_adj_combinations = self.analyze_reviews(reviews_texts)

                    filtered_adj_noun_combinations = self.filter_combinations(adj_noun_combinations)
                    filtered_verb_adj_combinations = self.filter_combinations(verb_adj_combinations)

                    for combo, count in filtered_adj_noun_combinations.items():
                        results_combined.append({"marke": brand, "produktname": product, "kombination": combo, "anzahl": count})

                    for combo, count in filtered_verb_adj_combinations.items():
                        results_combined.append({"marke": brand, "produktname": product, "kombination": combo, "anzahl": count})

                    # Fortschrittsbalken nach jeder Verarbeitung einer Gruppe aktualisieren
                    pbar.update(1)

            # Strukturierte Ergebnisse in DataFrame umwandeln und in CSV-Datei speichern
            combined_df = pd.DataFrame(results_combined)

            # Stelle sicher, dass das Output-Verzeichnis existiert
            os.makedirs(self.output_dir, exist_ok=True)

            # Speichere DataFrame als CSV-Datei mit Timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            combined_df.to_csv(os.path.join(self.output_dir, f'{self.analysis_filename}_{timestamp}.csv'), index=False)

        finally:
            session.close()