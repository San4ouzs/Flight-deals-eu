from __future__ import annotations
import os
from typing import List
from datetime import date
from amadeus import Client, ResponseError
from ..models import FlightOffer
from .base import ProviderBase

class AmadeusProvider(ProviderBase):
    name = "amadeus"

    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY")
        self.api_secret = os.getenv("AMADEUS_API_SECRET")
        self.client = None
        if self.api_key and self.api_secret:
            self.client = Client(
                client_id=self.api_key,
                client_secret=self.api_secret
            )

    def search_one_way(self, origin: str, destination: str, dep_date: date, currency: str = "EUR", max_stops: int = 1) -> List[FlightOffer]:
        if not self.client:
            # Мок-данные, чтобы можно было протестировать пайплайн без ключей
            price = 50.0 + hash((origin, destination, dep_date)) % 200
            return [FlightOffer(
                provider=self.name,
                origin=origin, destination=destination,
                departure_date=dep_date,
                price=price, currency=currency, airline="MOCK", stops=0, deep_link=None
            )]

        try:
            res = self.client.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=dep_date.isoformat(),
                adults=1,
                currencyCode=currency,
                max = 10
            )
            offers = []
            for item in res.data:
                price = float(item["price"]["total"])
                itineraries = item.get("itineraries", [])
                stops = 0
                if itineraries and itineraries[0].get("segments"):
                    stops = len(itineraries[0]["segments"]) - 1
                if stops > max_stops:
                    continue
                carrier = None
                if itineraries and itineraries[0].get("segments"):
                    carrier = itineraries[0]["segments"][0].get("carrierCode")
                offers.append(FlightOffer(
                    provider=self.name,
                    origin=origin,
                    destination=destination,
                    departure_date=dep_date,
                    price=price,
                    currency=currency,
                    airline=carrier,
                    stops=stops,
                    deep_link=None
                ))
            # Отсортируем по цене и вернём топ‑1 (или несколько)
            offers.sort(key=lambda x: x.price)
            return offers[:3]
        except ResponseError:
            return []
