from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Date, Time
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base



# Tabelle zu Produkte
# Die meisten Felder mussten auf nullable = True gesetzt werden.
# Obwohl der Crawler stabil läuft kann es in seltenen Fällen dazu kommen
# das nicht alles extrahiert wird und um Fehler beim Schreiben in dei DB zu vermeiden -> nullable = True

class Product(Base):
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_url: Mapped[str] = mapped_column(String, nullable=True)
    artikelnummer: Mapped[str] = mapped_column(String, nullable=True)
    produktname: Mapped[str] = mapped_column(String, nullable=True)
    preis: Mapped[float] = mapped_column(Float, nullable=True)
    promo_preis: Mapped[float] = mapped_column(Float, nullable=True)
    on_promo: Mapped[bool] = mapped_column(Boolean, default=False)
    waehrung: Mapped[str] = mapped_column(String, nullable=True)
    marke: Mapped[str] = mapped_column(String, nullable=True)
    artikelbeschreibung: Mapped[str] = mapped_column(Text, nullable=True)
    inhaltsstoffe: Mapped[str] = mapped_column(Text, nullable=True)
    gesamtrating: Mapped[float] = mapped_column(Float, nullable=True)
    gesamtanzahl_reviews: Mapped[int] = mapped_column(Integer, nullable=True)
    produkt_id: Mapped[int] = mapped_column(Integer, nullable=False)  
    session_date: Mapped[Date] = mapped_column(Date, nullable=False)  
    session_time: Mapped[Time] = mapped_column(Time, nullable=False)  

    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product")


# Tabelle zu Reviews
class Review(Base):
    __tablename__ = 'reviews'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reviewer: Mapped[str] = mapped_column(String, nullable=False)
    review: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(String, nullable=False)
    author_location: Mapped[str] = mapped_column(String)
    review_count: Mapped[int] = mapped_column(Integer)
    review_votes: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String)
    age: Mapped[str] = mapped_column(String)
    review_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # FK zur Produkt-Tabelle  
    produkt_id: Mapped[int] = mapped_column(Integer, ForeignKey('products.id'), nullable=False)  
    session_date: Mapped[Date] = mapped_column(Date, nullable=False)  
    session_time: Mapped[Time] = mapped_column(Time, nullable=False)  

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
