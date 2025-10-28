from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class FlightOffer(BaseModel):
    provider: str
    origin: str
    destination: str
    departure_date: date
    return_date: Optional[date] = None
    price: float
    currency: str = "EUR"
    airline: Optional[str] = None
    flight_number: Optional[str] = None
    stops: int = 0
    baggage_included: Optional[bool] = None
    deep_link: Optional[str] = None

class DealRow(BaseModel):
    origin: str
    destination: str
    dep_date: date
    price_eur: float
    avg365_eur: float
    pct_vs_avg: float  # negative means cheaper than average
    provider: str
    airline: Optional[str] = None
    deep_link: Optional[str] = None
