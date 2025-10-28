from __future__ import annotations
from typing import List
from datetime import date
from ..models import FlightOffer

class ProviderBase:
    name: str = "base"

    def search_one_way(self, origin: str, destination: str, dep_date: date, currency: str = "EUR", max_stops: int = 1) -> List[FlightOffer]:
        raise NotImplementedError
