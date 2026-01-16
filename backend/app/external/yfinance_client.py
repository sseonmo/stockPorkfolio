from datetime import date, datetime, timedelta
from typing import Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf
import pandas as pd


_executor = ThreadPoolExecutor(max_workers=4)


def _sync_get_stock_info(ticker: str) -> dict[str, Any] | None:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or info.get("regularMarketPrice") is None:
            return None
        return {
            "ticker": ticker,
            "name": info.get("shortName", info.get("longName", ticker)),
            "current_price": info.get("regularMarketPrice"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange", ""),
            "sector": info.get("sector"),
            "change": info.get("regularMarketChange"),
            "change_percent": info.get("regularMarketChangePercent"),
        }
    except Exception:
        return None


def _sync_search_stocks(query: str) -> list[dict[str, Any]]:
    try:
        tickers = yf.Tickers(query)
        results = []
        for ticker_str in query.split():
            ticker = yf.Ticker(ticker_str)
            info = ticker.info
            if info and info.get("regularMarketPrice"):
                results.append({
                    "ticker": ticker_str.upper(),
                    "name": info.get("shortName", info.get("longName", ticker_str)),
                    "current_price": info.get("regularMarketPrice"),
                    "exchange": info.get("exchange", ""),
                })
        return results
    except Exception:
        return []


def _sync_get_historical_data(
    ticker: str, start_date: date, end_date: date
) -> list[dict[str, Any]]:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start_date, end=end_date)
        if hist.empty:
            return []
        
        result = []
        for idx, row in hist.iterrows():
            result.append({
                "date": idx.date(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            })
        return result
    except Exception:
        return []


def _sync_get_exchange_rate() -> float:
    try:
        usd_krw = yf.Ticker("USDKRW=X")
        info = usd_krw.info
        return info.get("regularMarketPrice", 1300.0)
    except Exception:
        return 1300.0


class YFinanceClient:
    async def get_stock_info(self, ticker: str) -> dict[str, Any] | None:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _sync_get_stock_info, ticker)

    async def search_stocks(self, query: str) -> list[dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _sync_search_stocks, query)

    async def get_historical_data(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor, _sync_get_historical_data, ticker, start_date, end_date
        )

    async def get_exchange_rate(self) -> float:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, _sync_get_exchange_rate)

    async def get_benchmark_data(
        self, benchmark: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        benchmark_tickers = {
            "KOSPI": "^KS11",
            "SP500": "^GSPC",
            "NASDAQ": "^IXIC",
        }
        ticker = benchmark_tickers.get(benchmark, benchmark)
        return await self.get_historical_data(ticker, start_date, end_date)


yfinance_client = YFinanceClient()
