import os
import sys
import colorama
from colorama import Fore, Style
from scrapers.review_analyzer import ReviewAnalyzer
from DB.models import Review 

colorama.init(autoreset=True)


def print_banner():
    print(Fore.CYAN + Style.BRIGHT + "=" * 50)
    print(Fore.CYAN + Style.BRIGHT + " Willkommen zum Review Analyzer Tool ")
    print(Fore.CYAN + Style.BRIGHT + "=" * 50)


def print_menu():
    print(Fore.YELLOW + "Welche Bewertungen möchten Sie analysieren?")
    print("[1] Positive Eigenschaften (Bewertungen 4-5 Sterne)")
    print("[2] Negative Eigenschaften (Bewertungen 1-2 Sterne)")
    print("[3] Programm beenden")


def validate_choice(choice):
    if choice in ["1", "2", "3"]:
        return True
    else:
        print(Fore.RED + "Ungültige Auswahl. Bitte wählen Sie 1, 2 oder 3.")
        return False


def analyze(choice):
    # Dynamischer Pfad zur SQLite-Datenbank
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'DB', 'mueller_crawler.db'))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Analyse', 'Data'))

    if choice == "1":
        print(Fore.GREEN + "Sie haben sich für die Analyse der positiven Eigenschaften entschieden.")
        analyzer = ReviewAnalyzer(
            db_path=db_path,
            output_dir=output_dir,
            rating_filter=[4, 5],
            analysis_filename='positive_product_features',
            is_negative=False  # Standardlogik für positive Bewertungen
        )
    elif choice == "2":
        print(Fore.GREEN + "Sie haben sich für die Analyse der negativen Eigenschaften entschieden.")
        analyzer = ReviewAnalyzer(
            db_path=db_path,
            output_dir=output_dir,
            rating_filter=[1, 2],
            analysis_filename='negative_product_features',
            is_negative=True  # Weniger restriktive Logik für negative Bewertungen
        )

    print(Fore.YELLOW + "Analyse läuft...")
    analyzer.run_analysis()
    print(Fore.GREEN + "Analyse abgeschlossen!")


def main():
    print_banner()
    while True:
        print_menu()
        choice = input("Bitte Auswahl eingeben: ")
        if validate_choice(choice):
            if choice == "3":
                print(Fore.CYAN + "Programm wird beendet. Auf Wiedersehen!")
                sys.exit(0)
            analyze(choice)


if __name__ == "__main__":
    main()
