# app/models/warehouse.py
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    # 0 means unlimited capacity
    capacity_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # relationships (defined here, back-populated from other models)
    stock_balances: Mapped[list["StockBalance"]] = relationship(  # noqa: F821
        "StockBalance", back_populates="warehouse", lazy="select"
    )

    def __repr__(self) -> str:
        cap = self.capacity_limit if self.capacity_limit else "∞"
        return f"<Warehouse id={self.id} name={self.name!r} cap={cap}>"
