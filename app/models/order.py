# app/models/order.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    PACKED = "PACKED"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(256), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instagram_handle: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer", lazy="select")

    def __repr__(self) -> str:
        return f"<Customer id={self.id} name={self.full_name!r}>"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    dispatch_warehouse_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW, nullable=False
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False
    )
    total_amount: Mapped[float] = mapped_column(Numeric(16, 2), default=0.0)
    amount_paid: Mapped[float] = mapped_column(Numeric(16, 2), default=0.0)
    # City + district only, e.g. "Ташкент, Юнусабад"
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="bot", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    dispatch_warehouse: Mapped["Warehouse | None"] = relationship("Warehouse")  # noqa: F821
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status} total={self.total_amount}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")  # noqa: F821

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} prod={self.product_id} qty={self.quantity}>"
