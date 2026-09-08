# app/models/stock.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovementType(str, enum.Enum):
    RECEIPT = "RECEIPT"               # Goods received from supplier
    TRANSFER_OUT = "TRANSFER_OUT"     # Outbound leg of an inter-warehouse transfer
    TRANSFER_IN = "TRANSFER_IN"       # Inbound leg of an inter-warehouse transfer
    SALE_DISPATCH = "SALE_DISPATCH"   # Goods dispatched on a customer order
    ADJUSTMENT = "ADJUSTMENT"         # Manual stock adjustment / correction


class StockBalance(Base):
    """Current on-hand quantity of a product at a warehouse."""

    __tablename__ = "stock_balances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    warehouse: Mapped["Warehouse"] = relationship(  # noqa: F821
        "Warehouse", back_populates="stock_balances"
    )
    product: Mapped["Product"] = relationship(  # noqa: F821
        "Product", back_populates="stock_balances"
    )

    def __repr__(self) -> str:
        return f"<StockBalance wh={self.warehouse_id} prod={self.product_id} qty={self.quantity}>"


class StockMovement(Base):
    """Immutable ledger of every stock movement event."""

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    warehouse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)  # always positive
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    warehouse: Mapped["Warehouse"] = relationship("Warehouse")  # noqa: F821
    product: Mapped["Product"] = relationship("Product")  # noqa: F821

    def __repr__(self) -> str:
        return f"<StockMovement {self.movement_type} qty={self.quantity} wh={self.warehouse_id}>"
