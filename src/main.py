from __future__ import annotations
# Пример программного использования.
# Для запуска используйте CLI (see cli.py).
from .aggregator import search_all
from datetime import date
from dotenv import load_dotenv
load_dotenv()

def example():
    offers = search_all("RIX", "FRA", date.today())
    for o in offers:
        print(o)

if __name__ == "__main__":
    example()
