import os
import sys
import pandas as pd
from collections import Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Dynamischer Pfad zur SQLite-Datenbank
db_path = os.path.join(os.path.dirname(__file__), 'DB/mueller_crawler.db')
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Erstelle eine Engine und eine Session
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Füge den Pfad zum DB-Verzeichnis zu sys.path hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), 'DB'))


# Definiere den Namen der Tabellen, die du laden möchtest
table_products = 'products'
table_reviews = 'reviews'

# SQL-Abfrage mit RAW-SQL
sql_query = f"SELECT * FROM {table_products}"

# Lade die Tabelle in ein Pandas DataFrame
df_products = pd.read_sql_query(sql_query, engine)
df_csv_export = df_products.to_csv('Analyse/Data/products.csv', sep=';')

# SQL-Abfrage mit RAW-SQL
sql_query = f"SELECT * FROM {table_reviews}"

# Lade die Tabelle in ein Pandas DataFrame
df_reviews = pd.read_sql_query(sql_query, engine)
df_csv_export = df_reviews.to_csv('Analyse/Data/reviews.csv', sep=';')


# DataFrame anzeigen
print(df_products)
