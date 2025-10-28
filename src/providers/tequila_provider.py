from __future__ import annotations
import os, requests
from typing import List
from datetime import date
from ..models import FlightOffer
from .base import ProviderBase

class TequilaProvider(ProviderBase):
    name = "tequila"

    def __init__(self):
        self.api_key = os.getenv("TEQUILA_API_KEY")

    def search_one_way(self, origin: str, destination: str, dep_date: date, currency: str = "EUR", max_stops: int = 1) -> List[FlightOffer]:
        if not self.api_key:
            # Мок‑режим
            price = 60.0 + hash(("teq", origin, destination, dep_date)) % 220
            return [FlightOffer(
                provider=self.name,
                origin=origin, destination=destination,
                departure_date=dep_date,
                price=price, currency=currency, airline="MOCK", stops=0, deep_link=None
            )]

        url = "https://tequila-api.kiwi.com/v2/search"
        headers = {"apikey": self.api_key}
        params = {
            "fly_from": origin,
            "fly_to": destination,
            "date_from": dep_date.strftime("%d/%m/%Y"),
            "date_to": dep_date.strftime("%d/%m/%Y"),
            "curr": currency,
            "adults": 1,
            "limit": 5,
            "max_stopovers": max_stops
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            offers: List[FlightOffer] = []
            for it in data.get("data", []):
                price = float(it.get("price", 0))
                deep_link = it.get("deep_link")
                route = it.get("route", [])
                stops = max(0, len(route) - 1)
                airline = route[0]["airline"] if route else None
                offers.append(FlightOffer(
                    provider=self.name,
                    origin=origin,
                    destination=destination,
                    departure_date=dep_date,
                    price=price,
                    currency=currency,
                    airline=airline,
                    stops=stops,
                    deep_link=deep_link
                ))
            offers.sort(key=lambda x: x.price)
            return offers[:3]
        except Exception:
            return []
