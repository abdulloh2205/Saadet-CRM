# app/schemas/finance.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FinancialTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_type: str
    category: str
    amount: float
    order_id: int | None = None
    description: str | None = None
    created_at: datetime


class ABCItem(BaseModel):
    product_sku: str
    product_title: str
    total_revenue: float
    revenue_share_pct: float
    abc_class: str  # "A", "B", or "C"


class FinanceDashboardOut(BaseModel):
    total_revenue: float
    total_expenses: float
    gross_profit: float
    net_profit: float
    cash_flow: float
    receivables_outstanding: float
    abc_analysis: list[ABCItem]
    period_label: str = "All time"
