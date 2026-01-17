from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.holding import Holding
from app.models.transaction import Transaction, TransactionType
from app.models.stock import Stock, MarketType
from app.models.dividend import Dividend  # 추가
from app.external.yfinance_client import yfinance_client


class HoldingService:
    async def recalculate_holding(
        self, db: AsyncSession, user_id: int, stock_id: int
    ) -> Holding | None:
        stmt = (
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.stock_id == stock_id)
            .order_by(Transaction.transaction_date, Transaction.id)
        )
        result = await db.execute(stmt)
        transactions = result.scalars().all()

        if not transactions:
            holding_stmt = select(Holding).where(
                Holding.user_id == user_id, Holding.stock_id == stock_id
            )
            holding_result = await db.execute(holding_stmt)
            existing = holding_result.scalar_one_or_none()
            if existing:
                await db.delete(existing)
            return None

        quantity = Decimal("0")
        total_cost = Decimal("0")
        total_cost_krw = Decimal("0")
        total_dividends = Decimal("0")
        realized_gain = Decimal("0")

        # 배당금 조회 및 합산
        dividend_stmt = select(Dividend).where(
            Dividend.user_id == user_id, Dividend.stock_id == stock_id
        )
        dividend_result = await db.execute(dividend_stmt)
        dividends = dividend_result.scalars().all()
        
        for div in dividends:
            total_dividends += Decimal(str(div.amount))

        for txn in transactions:
            txn_qty = Decimal(str(txn.quantity))
            txn_price = Decimal(str(txn.price))
            txn_rate = Decimal(str(txn.exchange_rate))

            if txn.transaction_type == TransactionType.BUY:
                total_cost += txn_qty * txn_price
                total_cost_krw += txn_qty * txn_price * txn_rate
                quantity += txn_qty

            elif txn.transaction_type == TransactionType.SELL:
                if quantity > 0:
                    avg_cost = total_cost / quantity
                    avg_cost_krw = total_cost_krw / quantity
                    sell_qty = min(txn_qty, quantity)
                    
                    sell_proceeds = sell_qty * txn_price * txn_rate
                    sell_cost = sell_qty * avg_cost_krw
                    realized_gain += sell_proceeds - sell_cost
                    
                    total_cost -= sell_qty * avg_cost
                    total_cost_krw -= sell_qty * avg_cost_krw
                    quantity -= sell_qty

        holding_stmt = select(Holding).where(
            Holding.user_id == user_id, Holding.stock_id == stock_id
        )
        holding_result = await db.execute(holding_stmt)
        holding = holding_result.scalar_one_or_none()

        if quantity <= 0:
            if holding:
                await db.delete(holding)
            return None

        avg_cost = float(total_cost / quantity)
        avg_cost_krw = float(total_cost_krw / quantity)
        avg_exchange_rate = avg_cost_krw / avg_cost if avg_cost > 0 else 1.0

        if holding:
            holding.quantity = float(quantity)
            holding.average_cost = avg_cost
            holding.average_exchange_rate = avg_exchange_rate
            holding.total_invested = float(total_cost_krw)
            holding.total_dividends = float(total_dividends)
            holding.realized_gain = float(realized_gain)
        else:
            holding = Holding(
                user_id=user_id,
                stock_id=stock_id,
                quantity=float(quantity),
                average_cost=avg_cost,
                average_exchange_rate=avg_exchange_rate,
                total_invested=float(total_cost_krw),
                total_dividends=float(total_dividends),
                realized_gain=float(realized_gain),
            )
            db.add(holding)

        return holding

    async def get_holdings_with_metrics(
        self, db: AsyncSession, user_id: int, exchange_rate: float | None = None
    ) -> list[dict]:
        if exchange_rate is None:
            exchange_rate = await yfinance_client.get_exchange_rate()

        stmt = (
            select(Holding)
            .options(selectinload(Holding.stock))
            .where(Holding.user_id == user_id)
        )
        result = await db.execute(stmt)
        holdings = result.scalars().all()

        total_value_krw = Decimal("0")
        holdings_data = []

        for h in holdings:
            if not h.stock:
                continue
            
            current_price = h.stock.current_price or h.average_cost
            current_value = Decimal(str(h.quantity)) * Decimal(str(current_price))
            
            if h.stock.market_type == MarketType.US:
                current_value_krw = current_value * Decimal(str(exchange_rate))
            else:
                current_value_krw = current_value
            
            total_value_krw += current_value_krw
            
            holdings_data.append({
                "holding": h,
                "current_value": float(current_value),
                "current_value_krw": float(current_value_krw),
            })

        result_list = []
        for data in holdings_data:
            h = data["holding"]
            unrealized_gain = data["current_value_krw"] - float(h.total_invested)
            unrealized_gain_pct = (
                (unrealized_gain / float(h.total_invested) * 100)
                if float(h.total_invested) > 0 else 0.0
            )
            weight = (
                (Decimal(str(data["current_value_krw"])) / total_value_krw * 100)
                if total_value_krw > 0 else Decimal("0")
            )

            result_list.append({
                "id": h.id,
                "user_id": h.user_id,
                "stock_id": h.stock_id,
                "quantity": h.quantity,
                "average_cost": h.average_cost,
                "average_exchange_rate": h.average_exchange_rate,
                "total_invested": h.total_invested,
                "total_dividends": h.total_dividends,
                "realized_gain": h.realized_gain,
                "created_at": h.created_at,
                "updated_at": h.updated_at,
                "stock": h.stock,
                "current_value": data["current_value"],
                "current_value_krw": data["current_value_krw"],
                "unrealized_gain": float(unrealized_gain),
                "unrealized_gain_percent": float(unrealized_gain_pct),
                "weight_percent": float(weight),
            })

        return result_list


holding_service = HoldingService()
