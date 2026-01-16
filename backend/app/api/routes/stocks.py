from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.stock import Stock, MarketType
from app.models.user import User
from app.schemas.stock import StockCreate, StockResponse, StockSearchResult
from app.api.routes.auth import get_current_user
from app.external.kis_client import kis_client
from app.external.yfinance_client import yfinance_client

router = APIRouter()


@router.get("/search", response_model=list[StockSearchResult])
async def search_stocks(
    q: Annotated[str, Query(min_length=1, max_length=20)],
    market: Annotated[MarketType | None, Query()] = None,
    _: Annotated[User, Depends(get_current_user)] = None,
) -> list[dict]:
    results = []

    if market is None or market == MarketType.KR:
        kr_results = await kis_client.search_stock(q)
        for item in kr_results[:10]:
            price_str = item.get("prpr", "0")
            try:
                current_price = float(price_str) if price_str else None
            except (ValueError, TypeError):
                current_price = None

            results.append({
                "ticker": item.get("pdno", q),
                "name": item.get("prdt_name", item.get("prdt_abrv_name", "")),
                "market_type": MarketType.KR,
                "exchange": item.get("market", "KRX"),
                "current_price": current_price,
            })

    if market is None or market == MarketType.US:
        us_info = await yfinance_client.get_stock_info(q.upper())
        if us_info:
            results.append({
                "ticker": us_info["ticker"],
                "name": us_info["name"],
                "market_type": MarketType.US,
                "exchange": us_info["exchange"],
                "current_price": us_info["current_price"],
            })

    return results


@router.get("/exchange-rate")
async def get_exchange_rate(
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    rate = await yfinance_client.get_exchange_rate()
    return {"usd_krw": rate}


@router.post("", response_model=StockResponse)
async def create_stock(
    stock_data: StockCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Stock:
    stmt = select(Stock).where(Stock.ticker == stock_data.ticker)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    currency = "KRW" if stock_data.market_type == MarketType.KR else "USD"
    
    sector = stock_data.sector
    if not sector:
        # Try to fetch sector info
        if stock_data.market_type == MarketType.US:
            info = await yfinance_client.get_stock_info(stock_data.ticker)
            if info:
                sector = info.get("sector")
        elif stock_data.market_type == MarketType.KR:
            # Simple mock sector mapping for demo
            mock_sectors = {
                "005930": "Technology", # Samsung
                "000660": "Technology", # SK Hynix
                "035420": "Communication Services", # NAVER
                "035720": "Communication Services", # Kakao
                "005380": "Consumer Cyclical", # Hyundai
            }
            sector = mock_sectors.get(stock_data.ticker, "Unclassified")

    stock = Stock(
        ticker=stock_data.ticker,
        name=stock_data.name,
        market_type=stock_data.market_type,
        exchange=stock_data.exchange,
        sector=sector,
        currency=currency,
    )
    db.add(stock)
    await db.flush()
    return stock


@router.get("/{stock_id}", response_model=StockResponse)
async def get_stock(
    stock_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> Stock:
    stmt = select(Stock).where(Stock.id == stock_id)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/{stock_id}/price")
async def get_stock_price(
    stock_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> dict:
    stmt = select(Stock).where(Stock.id == stock_id)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    if stock.market_type == MarketType.KR:
        price_data = await kis_client.get_stock_price(stock.ticker)
    else:
        price_data = await yfinance_client.get_stock_info(stock.ticker)

    if price_data:
        stock.current_price = price_data.get("current_price")
        return price_data

    return {"ticker": stock.ticker, "current_price": stock.current_price}
