from __future__ import annotations
import os
from typing import List, Optional, Tuple
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "flight_deals.sqlite")

def ensure_db() -> Engine:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
    with engine.begin() as conn:
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_utc TEXT NOT NULL,
            provider TEXT NOT NULL,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            dep_date TEXT NOT NULL,
            currency TEXT NOT NULL,
            price REAL NOT NULL
        );
        """)
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_prices_route_date ON prices(origin, destination, dep_date);")
    return engine

def insert_offers(engine: Engine, offers: List[dict]):
    ts = datetime.utcnow().isoformat()
    with engine.begin() as conn:
        for o in offers:
            conn.execute(text("""
                INSERT INTO prices(ts_utc, provider, origin, destination, dep_date, currency, price)
                VALUES (:ts, :provider, :origin, :destination, :dep_date, :currency, :price)
            """), {
                "ts": ts,
                "provider": o["provider"],
                "origin": o["origin"],
                "destination": o["destination"],
                "dep_date": o["departure_date"].isoformat(),
                "currency": o.get("currency", "EUR"),
                "price": float(o["price"]),
            })

def get_avg365(engine: Engine, origin: str, destination: str, dep_date: date, currency: str = "EUR") -> Optional[float]:
    start = dep_date - timedelta(days=365)
    end = dep_date
    with engine.begin() as conn:
        res = conn.execute(text("""
            SELECT AVG(price) FROM prices
             WHERE origin=:o AND destination=:d
               AND dep_date>=:start AND dep_date<:end AND currency=:cur
        """), {"o": origin, "d": destination, "start": start.isoformat(), "end": end.isoformat(), "cur": currency}).scalar()
    return float(res) if res is not None else None

def select_deals(engine: Engine, threshold_pct: float = -20.0, limit: int = 50):
    # Возвращает последние актуальные записи по каждой комбинации (origin, destination, dep_date, provider),
    # у которых цена ниже 365-дневной средней на threshold_pct или больше (в отрицательную сторону).
    with engine.begin() as conn:
        rows = conn.execute(text("""
            WITH latest AS (
              SELECT p.*,
                     ROW_NUMBER() OVER (PARTITION BY origin, destination, dep_date, provider ORDER BY ts_utc DESC) AS rn
              FROM prices p
            )
            SELECT origin, destination, dep_date, provider, currency, price, ts_utc
            FROM latest WHERE rn=1
            ORDER BY dep_date ASC, price ASC
        """)).mappings().all()

    results = []
    for r in rows:
        dep_date = date.fromisoformat(r["dep_date"])
        avg = get_avg365(engine, r["origin"], r["destination"], dep_date, r["currency"])
        if avg is None or avg <= 0:
            continue
        pct_vs = (r["price"] / avg - 1.0) * 100.0
        if pct_vs <= threshold_pct:
            results.append({
                "origin": r["origin"],
                "destination": r["destination"],
                "dep_date": dep_date,
                "provider": r["provider"],
                "currency": r["currency"],
                "price": r["price"],
                "avg365": avg,
                "pct_vs_avg": pct_vs,
                "ts_utc": r["ts_utc"],
            })
    results = sorted(results, key=lambda x: (x["pct_vs_avg"], x["price"]))[:limit]
    return results
