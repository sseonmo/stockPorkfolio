from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.stock import MarketType
from app.models.user import User
from app.schemas.holding import HoldingWithMetrics
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service

router = APIRouter()


@router.get("", response_model=list[HoldingWithMetrics])
async def list_holdings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    market: Annotated[MarketType | None, Query()] = None,
) -> list[dict]:
    holdings = await holding_service.get_holdings_with_metrics(db, current_user.id)

    if market:
        holdings = [h for h in holdings if h["stock"] and h["stock"].market_type == market]

    return holdings
