# app/models/finance.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionCategory(str, enum.Enum):
    SALES_REVENUE = "SALES_REVENUE"
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"
    SALARY = "SALARY"
    LOGISTICS = "LOGISTICS"
    MARKETING = "MARKETING"
    OFFICE = "OFFICE"
    OTHER = "OTHER"


class ReceivableStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    SETTLED = "SETTLED"
    OVERDUE = "OVERDUE"


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    category: Mapped[TransactionCategory] = mapped_column(
        Enum(TransactionCategory), default=TransactionCategory.OTHER, nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    # Optional link to the order that triggered this transaction
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped["Order | None"] = relationship("Order")  # noqa: F821

    def __repr__(self) -> str:
        return f"<FinTx {self.transaction_type} {self.amount} cat={self.category}>"


class Receivable(Base):
    """Tracks money owed by customers (credit sales / partial payments)."""

    __tablename__ = "receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    original_amount: Mapped[float] = mapped_column(Numeric(16, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0.0)
    status: Mapped[ReceivableStatus] = mapped_column(
        Enum(ReceivableStatus), default=ReceivableStatus.OPEN, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer")  # noqa: F821

    @property
    def outstanding(self) -> float:
        return float(self.original_amount) - float(self.paid_amount)

    def __repr__(self) -> str:
        return f"<Receivable cust={self.customer_id} outstanding={self.outstanding}>"
