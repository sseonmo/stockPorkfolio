from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.dividend import Dividend
from app.models.user import User
from app.models.stock import Stock
from app.schemas.dividend import DividendCreate, DividendResponse, DividendUpdate

router = APIRouter()


@router.get("", response_model=List[DividendResponse])
async def get_dividends(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    stock_id: Optional[int] = None,
    year: Optional[str] = None,
):
    query = (
        select(Dividend)
        .where(Dividend.user_id == current_user.id)
        .options(selectinload(Dividend.stock))
        .order_by(desc(Dividend.dividend_date))
    )

    if stock_id:
        query = query.where(Dividend.stock_id == stock_id)
        
    # 날짜 필터링은 DB 종속적일 수 있으므로 Python에서 처리하거나 extract 사용
    # 여기서는 간단히 모든 데이터를 가져와서 필터링 (데이터 양이 많지 않다고 가정)
    # 또는 extract('year', Dividend.dividend_date) == year 사용
    
    result = await db.execute(query)
    dividends = result.scalars().all()
    
    if year:
        dividends = [d for d in dividends if str(d.dividend_date.year) == year]
        
    return dividends[skip : skip + limit]


@router.post("", response_model=DividendResponse)
async def create_dividend(
    dividend_in: DividendCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Stock 존재 확인
    stock = await db.get(Stock, dividend_in.stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    dividend = Dividend(
        **dividend_in.model_dump(),
        user_id=current_user.id
    )
    db.add(dividend)
    await db.commit()
    await db.refresh(dividend)
    
    # 관계 로드
    stmt = select(Dividend).where(Dividend.id == dividend.id).options(selectinload(Dividend.stock))
    result = await db.execute(stmt)
    dividend = result.scalar_one()
    
    return dividend


@router.put("/{dividend_id}", response_model=DividendResponse)
async def update_dividend(
    dividend_id: int,
    dividend_in: DividendUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = (
        select(Dividend)
        .where(Dividend.id == dividend_id, Dividend.user_id == current_user.id)
        .options(selectinload(Dividend.stock))
    )
    result = await db.execute(stmt)
    dividend = result.scalar_one_or_none()

    if not dividend:
        raise HTTPException(status_code=404, detail="Dividend not found")

    update_data = dividend_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dividend, field, value)

    await db.commit()
    await db.refresh(dividend)
    return dividend


@router.delete("/{dividend_id}")
async def delete_dividend(
    dividend_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(Dividend).where(
        Dividend.id == dividend_id, Dividend.user_id == current_user.id
    )
    result = await db.execute(stmt)
    dividend = result.scalar_one_or_none()

    if not dividend:
        raise HTTPException(status_code=404, detail="Dividend not found")

    await db.delete(dividend)
    await db.commit()
    return {"status": "success"}
