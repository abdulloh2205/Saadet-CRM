# app/api/inventory_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.finance import FinancialTransaction, TransactionType
from app.models.stock import StockBalance
from app.models.warehouse import Warehouse
from app.schemas.inventory import (
    ProductOut, StockBalanceOut, TransferRequest, TransferResponse, WarehouseOut,
)
from app.services import inventory_service
from app.bot.alerts import alert_stock_transferred, alert_capacity_warning
from sqlalchemy import func as sqlfunc

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


def _build_balance_out(sb) -> StockBalanceOut:
    wh, prod = sb.warehouse, sb.product
    margin = 0.0
    if prod.retail_price:
        margin = round((float(prod.retail_price) - float(prod.cost_price)) / float(prod.retail_price) * 100, 2)
    return StockBalanceOut(
        id=sb.id,
        warehouse=WarehouseOut(id=wh.id, name=wh.name, capacity_limit=wh.capacity_limit, address=wh.address),
        product=ProductOut(id=prod.id, sku=prod.sku, title=prod.title,
                           retail_price=float(prod.retail_price), cost_price=float(prod.cost_price),
                           gross_margin_pct=margin),
        quantity=sb.quantity,
        updated_at=sb.updated_at,
    )


@router.get("/stocks", response_model=list[StockBalanceOut])
async def get_stocks(db: AsyncSession = Depends(get_db)):
    balances = await inventory_service.get_all_balances(db)
    return [_build_balance_out(b) for b in balances]


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """
    Unified dashboard payload:
    - Revenue, expenses, net profit
    - Per-warehouse stock grouped by product
    - Uchtepa capacity stats
    """
    # All balances
    balances = await inventory_service.get_all_balances(db)

    # Group by warehouse
    wh_map: dict[int, dict] = {}
    for sb in balances:
        wid = sb.warehouse.id
        if wid not in wh_map:
            wh_map[wid] = {
                "id": wid,
                "name": sb.warehouse.name,
                "capacity_limit": sb.warehouse.capacity_limit,
                "products": [],
                "total_qty": 0,
            }
        wh_map[wid]["products"].append({
            "id": sb.product.id,
            "sku": sb.product.sku,
            "title": sb.product.title,
            "quantity": sb.quantity,
            "retail_price": float(sb.product.retail_price),
        })
        wh_map[wid]["total_qty"] += sb.quantity

    warehouses = list(wh_map.values())

    # Uchtepa capacity
    uchtepa_data = next((w for w in warehouses if "Учтепа" in w["name"] or "Uchtepa" in w.get("name","")), None)
    uchtepa_cap = {
        "current": uchtepa_data["total_qty"] if uchtepa_data else 0,
        "limit": uchtepa_data["capacity_limit"] if uchtepa_data else 100,
    }

    # Finance totals
    income_q = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.sum(FinancialTransaction.amount), 0))
        .where(FinancialTransaction.transaction_type == TransactionType.INCOME)
    )
    expense_q = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.sum(FinancialTransaction.amount), 0))
        .where(FinancialTransaction.transaction_type == TransactionType.EXPENSE)
    )
    total_revenue = float(income_q.scalar_one())
    total_expenses = float(expense_q.scalar_one())

    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": total_revenue - total_expenses,
        "cash_flow": total_revenue - total_expenses,
        "warehouses": warehouses,
        "uchtepa_capacity": uchtepa_cap,
    }


@router.post("/transfer", response_model=TransferResponse)
async def transfer_stock(payload: TransferRequest, db: AsyncSession = Depends(get_db)):
    try:
        from_bal, to_bal = await inventory_service.transfer_stock(
            db,
            product_id=payload.product_id,
            from_warehouse_id=payload.from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            quantity=payload.quantity,
        )
        response = TransferResponse(
            success=True,
            message=f"Перемещено {payload.quantity} шт. Откуда: {from_bal.quantity} ост., Куда: {to_bal.quantity} итого.",
            from_balance=from_bal.quantity,
            to_balance=to_bal.quantity,
        )

        # Send transfer notification
        await alert_stock_transferred(
            product_title=from_bal.product.title,
            quantity=payload.quantity,
            from_wh=from_bal.warehouse.name,
            to_wh=to_bal.warehouse.name,
            from_remaining=from_bal.quantity,
            to_total=to_bal.quantity,
        )

        # Check capacity warning on destination
        if to_bal.warehouse.capacity_limit and to_bal.warehouse.capacity_limit > 0:
            total_at_dest = await inventory_service._get_warehouse_total(db, to_bal.warehouse.id)
            await alert_capacity_warning(
                warehouse_name=to_bal.warehouse.name,
                current=total_at_dest,
                limit=to_bal.warehouse.capacity_limit,
            )

        # Check low stock on the product that was moved out
        await inventory_service.check_low_stock(db, payload.product_id)

        return response
    except inventory_service.CapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except inventory_service.InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except inventory_service.WarehouseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
