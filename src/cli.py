from __future__ import annotations
import csv
from datetime import date, timedelta
from typing import List, Optional
import os
import pandas as pd
import typer
from tabulate import tabulate
from dotenv import load_dotenv

from .aggregator import search_all
from .storage import ensure_db, insert_offers, select_deals
from .models import FlightOffer

app = typer.Typer(add_completion=False)
load_dotenv()

def iter_dates(days_ahead: int):
    today = date.today()
    for i in range(days_ahead + 1):
        yield today + timedelta(days=i)

def read_airports_csv(path: str) -> List[str]:
    codes: List[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            codes.append(row["IATA"].strip().upper())
    return codes

@app.command()
def scan(
    origins: str = typer.Option(..., help="Список IATA через запятую, например: RIX,TLL,VNO"),
    destinations: Optional[str] = typer.Option(None, help="Список IATA через запятую"),
    destinations_from_csv: Optional[str] = typer.Option(None, help="CSV файл со столбцом IATA"),
    days_ahead: int = typer.Option(30, help="Сколько дней вперёд сканировать"),
    currency: str = typer.Option("EUR", help="Валюта запроса"),
    max_stops: int = typer.Option(1, help="Максимум пересадок"),
):
    """Сканирует цены на ближайшие даты и сохраняет в SQLite."""
    engine = ensure_db()
    origin_list = [x.strip().upper() for x in origins.split(",") if x.strip()]
    if destinations_from_csv:
        dest_list = read_airports_csv(destinations_from_csv)
    else:
        dest_list = [x.strip().upper() for x in destinations.split(",")] if destinations else []

    totals = 0
    for o in origin_list:
        for d in dest_list:
            if o == d:
                continue
            for dep in iter_dates(days_ahead):
                offers: List[FlightOffer] = search_all(o, d, dep, currency=currency, max_stops=max_stops)
                if not offers:
                    continue
                insert_offers(engine, [o.model_dump() for o in offers[:1]])  # берём лучшую цену
                totals += 1
                typer.echo(f"{o}->{d} {dep}: saved {offers[0].price} {currency}")
    typer.echo(f"Готово. Обновлено маршрутов: {totals}")

@app.command()
def deals(
    threshold: float = typer.Option(-20.0, help="Порог % к средней (отрицательное — дешевле)"),
    limit: int = typer.Option(50, help="Максимум строк"),
    export_csv: Optional[str] = typer.Option("deals_export.csv", help="Имя CSV для сохранения"),
):
    """Показывает направления, где текущая цена ниже 365‑дневной средней на указанный порог."""
    engine = ensure_db()
    rows = select_deals(engine, threshold_pct=threshold, limit=limit)
    if not rows:
        typer.echo("Нет направлений, удовлетворяющих условию.")
        return
    df = pd.DataFrame([{
        "FROM": r["origin"],
        "TO": r["destination"],
        "DATE": r["dep_date"],
        "PRICE_EUR": round(r["price"], 2),
        "AVG365_EUR": round(r["avg365"], 2),
        "% vs AVG": round(r["pct_vs_avg"], 1),
        "PROVIDER": r["provider"],
    } for r in rows])
    print(tabulate(df, headers='keys', tablefmt='github', showindex=False))
    if export_csv:
        df.to_csv(export_csv, index=False, encoding="utf-8")
        typer.echo(f"CSV сохранён: {export_csv}")

if __name__ == "__main__":
    app()
