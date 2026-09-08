# app/schemas/inventory.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WarehouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity_limit: int
    address: str | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    title: str
    retail_price: float
    cost_price: float
    gross_margin_pct: float = 0.0

    @classmethod
    def from_orm_product(cls, obj) -> "ProductOut":
        margin = 0.0
        if obj.retail_price:
            margin = round(
                (float(obj.retail_price) - float(obj.cost_price)) / float(obj.retail_price) * 100, 2
            )
        return cls(
            id=obj.id,
            sku=obj.sku,
            title=obj.title,
            retail_price=float(obj.retail_price),
            cost_price=float(obj.cost_price),
            gross_margin_pct=margin,
        )


class StockBalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    warehouse: WarehouseOut
    product: ProductOut
    quantity: int
    updated_at: datetime


class StockMovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movement_type: str
    quantity: int
    reference_id: str | None = None
    notes: str | None = None
    created_at: datetime


class TransferRequest(BaseModel):
    product_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    quantity: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "from_warehouse_id": 1,
                "to_warehouse_id": 2,
                "quantity": 10,
            }
        }
    )


class TransferResponse(BaseModel):
    success: bool
    message: str
    from_balance: int
    to_balance: int
