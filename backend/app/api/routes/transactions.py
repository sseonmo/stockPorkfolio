from typing import Annotated
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.stock import Stock, MarketType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionWithStock,
    TransactionUpdate,
)
from app.api.routes.auth import get_current_user
from app.services.holding_service import holding_service

router = APIRouter()


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
