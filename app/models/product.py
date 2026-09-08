# app/models/product.py
from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Prices stored in UZS (integer or 2-decimal Numeric)
    cost_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    retail_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    # Minimum gross-margin threshold as percentage (e.g. 32 means 32%)
    min_margin_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    # Low-stock alert threshold (units). Alert fires when total stock across all warehouses <= this.
    min_stock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(default=True)

    stock_balances: Mapped[list["StockBalance"]] = relationship(  # noqa: F821
        "StockBalance", back_populates="product", lazy="select"
    )
    order_items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821
        "OrderItem", back_populates="product", lazy="select"
    )

    @property
    def gross_margin_pct(self) -> float:
        if self.retail_price == 0:
            return 0.0
        return round((float(self.retail_price) - float(self.cost_price)) / float(self.retail_price) * 100, 2)

    def __repr__(self) -> str:
        return f"<Product sku={self.sku!r} title={self.title!r}>"
