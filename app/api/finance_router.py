# app/api/finance_router.py
from sqlalchemy import select, func as sqlfunc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models.finance import FinancialTransaction, Receivable, TransactionType, TransactionCategory
from app.models.order import OrderItem
from app.models.product import Product
from app.schemas.finance import ABCItem, FinanceDashboardOut

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/dashboard", response_model=FinanceDashboardOut)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated financial metrics:
    - Total Revenue
    - Total Expenses
    - Gross & Net Profit
    - Cash Flow (Revenue - Expenses)
    - Outstanding Receivables
    - ABC Analysis preview (products ranked by revenue contribution)
    """
    # Aggregate income
    income_q = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.sum(FinancialTransaction.amount), 0)).where(
            FinancialTransaction.transaction_type == TransactionType.INCOME
        )
    )
    total_revenue = float(income_q.scalar_one())

    # Aggregate expenses
    expense_q = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.sum(FinancialTransaction.amount), 0)).where(
            FinancialTransaction.transaction_type == TransactionType.EXPENSE
        )
    )
    total_expenses = float(expense_q.scalar_one())

    # COGS estimate: sum of (cost_price * qty) for all dispatched order items
    # (simplified — uses current cost prices)
    cogs_q = await db.execute(
        select(
            sqlfunc.coalesce(
                sqlfunc.sum(OrderItem.quantity * Product.cost_price), 0
            )
        )
        .join(Product, OrderItem.product_id == Product.id)
    )
    cogs = float(cogs_q.scalar_one())

    gross_profit = total_revenue - cogs
    net_profit = total_revenue - total_expenses
    cash_flow = total_revenue - total_expenses

    # Outstanding receivables
    recv_q = await db.execute(
        select(
            sqlfunc.coalesce(
                sqlfunc.sum(Receivable.original_amount - Receivable.paid_amount), 0
            )
        )
    )
    receivables_outstanding = float(recv_q.scalar_one())

    # --- ABC Analysis ---
    # Revenue per product (sum of line totals from order items)
    abc_q = await db.execute(
        select(
            Product.sku,
            Product.title,
            sqlfunc.coalesce(sqlfunc.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("rev"),
        )
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(sqlfunc.sum(OrderItem.quantity * OrderItem.unit_price).desc())
    )
    abc_rows = abc_q.all()

    total_rev_for_abc = sum(float(r.rev) for r in abc_rows) or 1.0
    cumulative = 0.0
    abc_items: list[ABCItem] = []
    for row in abc_rows:
        rev = float(row.rev)
        share = round(rev / total_rev_for_abc * 100, 1)
        cumulative += share
        if cumulative <= 80:
            cls = "A"
        elif cumulative <= 95:
            cls = "B"
        else:
            cls = "C"
        abc_items.append(
            ABCItem(
                product_sku=row.sku,
                product_title=row.title,
                total_revenue=rev,
                revenue_share_pct=share,
                abc_class=cls,
            )
        )

    return FinanceDashboardOut(
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        gross_profit=gross_profit,
        net_profit=net_profit,
        cash_flow=cash_flow,
        receivables_outstanding=receivables_outstanding,
        abc_analysis=abc_items,
        period_label="All time",
    )
