from __future__ import annotations
from typing import List
from datetime import date
from .models import FlightOffer
from .providers.amadeus_provider import AmadeusProvider
from .providers.tequila_provider import TequilaProvider

def get_providers():
    return [AmadeusProvider(), TequilaProvider()]

def search_all(origin: str, destination: str, dep_date: date, currency: str = "EUR", max_stops: int = 1) -> List[FlightOffer]:
    offers: List[FlightOffer] = []
    for p in get_providers():
        try:
            offers.extend(p.search_one_way(origin, destination, dep_date, currency, max_stops))
        except Exception:
            continue
    # нормализуем валюту в EUR — тут предполагается, что провайдеры уже отдают EUR по параметру currency
    # TODO: подключить конвертацию при необходимости
    offers.sort(key=lambda x: x.price)
    return offers
