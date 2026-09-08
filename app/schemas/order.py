# app/schemas/order.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: str | None = None
    telegram_username: str | None = None
    instagram_handle: str | None = None
    tags: str | None = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    quantity: int
    unit_price: float
    line_total: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer: CustomerOut
    status: str
    payment_status: str
    total_amount: float
    amount_paid: float
    district: str | None = None
    delivery_address: str | None = None
    notes: str | None = None
    source: str = "bot"
    items: list[OrderItemOut] = []
    created_at: datetime
    updated_at: datetime


class CreateOrderItemRequest(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class CreateOrderRequest(BaseModel):
    customer_id: int
    dispatch_warehouse_id: int
    items: list[CreateOrderItemRequest]
    district: str | None = None
    delivery_address: str | None = None
    notes: str | None = None
    mark_paid: bool = False
