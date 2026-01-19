from typing import Annotated
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, extract, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import math

from app.core.database import get_db
from app.models.stock import Stock, MarketType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionWithStock,
    TransactionUpdate,
    TransactionPageResponse,
)
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service

router = APIRouter()


def calculate_realized_gains_for_transactions(
    transactions: list[Transaction],
) -> dict[int, dict[str, float]]:
    sorted_txns = sorted(transactions, key=lambda t: (t.transaction_date, t.id))
    buy_queue: list[dict[str, float]] = []
    realized_gains: dict[int, dict[str, float]] = {}
    
    for txn in sorted_txns:
        if txn.transaction_type == TransactionType.BUY:
            buy_queue.append({
                'quantity': float(txn.quantity),
                'price': float(txn.price),
                'rate': float(txn.exchange_rate),
            })
        elif txn.transaction_type == TransactionType.SELL:
            sell_qty = float(txn.quantity)
            sell_price = float(txn.price)
            sell_rate = float(txn.exchange_rate)
            total_cost_krw = 0.0
            remaining = sell_qty
            
            while remaining > 0 and buy_queue:
                buy = buy_queue[0]
                take = min(remaining, buy['quantity'])
                total_cost_krw += take * buy['price'] * buy['rate']
                
                buy['quantity'] -= take
                remaining -= take
                
                if buy['quantity'] <= 0:
                    buy_queue.pop(0)
            
            sell_proceeds_krw = sell_qty * sell_price * sell_rate
            realized_gain = sell_proceeds_krw - total_cost_krw
            realized_gain_percent = (
                (realized_gain / total_cost_krw * 100) if total_cost_krw > 0 else 0.0
            )
            
            realized_gains[txn.id] = {
                'realized_gain': realized_gain,
                'realized_gain_percent': realized_gain_percent,
            }
    
    return realized_gains


@router.post("", response_model=TransactionResponse)
async def create_transaction(
    txn_data: TransactionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    stmt = select(Stock).where(Stock.id == txn_data.stock_id)
    result = await db.execute(stmt)
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    transaction = Transaction(
        user_id=current_user.id,
        stock_id=txn_data.stock_id,
        transaction_type=txn_data.transaction_type,
        quantity=txn_data.quantity,
        price=txn_data.price,
        exchange_rate=txn_data.exchange_rate,
        fees=txn_data.fees,
        transaction_date=txn_data.transaction_date,
        notes=txn_data.notes,
    )
    db.add(transaction)
    await db.flush()

    await holding_service.recalculate_holding(db, current_user.id, txn_data.stock_id)

    return transaction


@router.get("", response_model=list[TransactionWithStock])
async def list_transactions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    stock_id: Annotated[int | None, Query()] = None,
    transaction_type: Annotated[TransactionType | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.stock))
        .where(Transaction.user_id == current_user.id)
    )

    if stock_id:
        stmt = stmt.where(Transaction.stock_id == stock_id)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if start_date:
        stmt = stmt.where(Transaction.transaction_date >= start_date)
    if end_date:
        stmt = stmt.where(Transaction.transaction_date <= end_date)

    stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/by-stock/{stock_id}", response_model=TransactionPageResponse)
async def get_transactions_by_stock(
    stock_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    year: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> TransactionPageResponse:
    all_txns_stmt = (
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .where(Transaction.stock_id == stock_id)
        .order_by(Transaction.transaction_date, Transaction.id)
    )
    all_txns_result = await db.execute(all_txns_stmt)
    all_transactions = list(all_txns_result.scalars().all())
    
    realized_gains = calculate_realized_gains_for_transactions(all_transactions)
    
    base_stmt = (
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .where(Transaction.stock_id == stock_id)
    )
    
    if year:
        base_stmt = base_stmt.where(extract('year', Transaction.transaction_date) == year)
    
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count_result = await db.execute(count_stmt)
    total_elements = count_result.scalar() or 0
    total_pages = math.ceil(total_elements / size) if total_elements > 0 else 1
    
    offset = (page - 1) * size
    data_stmt = (
        base_stmt
        .options(selectinload(Transaction.stock))
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(data_stmt)
    transactions = list(result.scalars().all())
    
    years_stmt = (
        select(distinct(extract('year', Transaction.transaction_date)))
        .where(Transaction.user_id == current_user.id)
        .where(Transaction.stock_id == stock_id)
        .order_by(extract('year', Transaction.transaction_date).desc())
    )
    years_result = await db.execute(years_stmt)
    available_years = [int(y) for y in years_result.scalars().all()]
    
    content = []
    for txn in transactions:
        txn_data = TransactionWithStock.model_validate(txn)
        if txn.id in realized_gains:
            txn_data.realized_gain = realized_gains[txn.id]['realized_gain']
            txn_data.realized_gain_percent = realized_gains[txn.id]['realized_gain_percent']
        content.append(txn_data)
    
    return TransactionPageResponse(
        content=content,
        total_elements=total_elements,
        total_pages=total_pages,
        current_page=page,
        available_years=available_years,
    )


@router.get("/{transaction_id}", response_model=TransactionWithStock)
async def get_transaction(
    transaction_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.stock))
        .where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    txn_update: TransactionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Transaction:
    stmt = select(Transaction).where(
        Transaction.id == transaction_id, Transaction.user_id == current_user.id
    )
    result = await db.execute(stmt)
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = txn_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(txn, key, value)

    await db.flush()
    await holding_service.recalculate_holding(db, current_user.id, txn.stock_id)
    
    return txn


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    stmt = select(Transaction).where(
        Transaction.id == transaction_id, Transaction.user_id == current_user.id
    )
    result = await db.execute(stmt)
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    stock_id = txn.stock_id
    await db.delete(txn)
    await db.flush()

    await holding_service.recalculate_holding(db, current_user.id, stock_id)

    return {"message": "Transaction deleted"}
