# app/api/order_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.finance import FinancialTransaction, TransactionCategory, TransactionType
from app.schemas.order import CreateOrderRequest, CustomerOut, OrderItemOut, OrderOut
from app.services import order_service
from app.bot.alerts import (
    alert_order_status_changed, alert_payment_received, alert_new_order
)

router = APIRouter(prefix="/api/orders", tags=["orders"])


class UpdateStatusRequest(BaseModel):
    status: str | None = None
    payment_status: str | None = None


def _build_order_out(order) -> OrderOut:
    cust = order.customer
    items = [
        OrderItemOut(
            id=i.id, product_id=i.product_id,
            quantity=i.quantity, unit_price=float(i.unit_price),
            line_total=float(i.unit_price) * i.quantity,
        )
        for i in order.items
    ]
    return OrderOut(
        id=order.id,
        customer=CustomerOut(
            id=cust.id, full_name=cust.full_name,
            phone=cust.phone, telegram_username=cust.telegram_username,
            instagram_handle=cust.instagram_handle, tags=cust.tags,
        ),
        status=order.status.value if hasattr(order.status, "value") else order.status,
        payment_status=order.payment_status.value if hasattr(order.payment_status, "value") else order.payment_status,
        total_amount=float(order.total_amount),
        amount_paid=float(order.amount_paid),
        district=order.district,
        delivery_address=order.delivery_address,
        notes=order.notes,
        source=order.source,
        items=items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("", response_model=list[OrderOut])
async def list_orders(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    orders = await order_service.get_orders(db, limit=limit, offset=offset)
    return [_build_order_out(o) for o in orders]


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(payload: CreateOrderRequest, db: AsyncSession = Depends(get_db)):
    try:
        order = await order_service.create_order(db, payload)
        out = _build_order_out(order)
        # Send notification
        await alert_new_order(
            order_id=order.id,
            customer_name=order.customer.full_name,
            total=float(order.total_amount),
            district=order.district,
            source=order.source,
        )
        return out
    except order_service.InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# Valid status transitions
_VALID_TRANSITIONS = {
    "NEW":        ["PACKED", "CANCELLED"],
    "PACKED":     ["DELIVERING", "CANCELLED"],
    "DELIVERING": ["DELIVERED", "CANCELLED"],
    "DELIVERED":  [],
    "CANCELLED":  [],
}


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: int,
    payload: UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update order status and/or payment status.
    Enforces valid transitions: NEW → PACKED → DELIVERING → DELIVERED.
    When marking DELIVERED + PAID, auto-records a financial income transaction.
    """
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status.value if hasattr(order.status, "value") else order.status
    old_payment = order.payment_status.value if hasattr(order.payment_status, "value") else order.payment_status

    # Update order status
    if payload.status:
        new_status = payload.status.upper()
        valid = _VALID_TRANSITIONS.get(old_status, [])
        if new_status not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {old_status} to {new_status}. "
                       f"Allowed: {valid}"
            )
        order.status = OrderStatus(new_status)

        # Notify status change
        await alert_order_status_changed(
            order_id=order.id,
            customer_name=order.customer.full_name,
            old_status=old_status,
            new_status=new_status,
            total=float(order.total_amount),
        )

    # Update payment status
    if payload.payment_status:
        new_pay = payload.payment_status.upper()
        order.payment_status = PaymentStatus(new_pay)

        if new_pay == "PAID" and old_payment != "PAID":
            order.amount_paid = float(order.total_amount)

            # Record financial transaction
            tx = FinancialTransaction(
                transaction_type=TransactionType.INCOME,
                category=TransactionCategory.SALES_REVENUE,
                amount=float(order.total_amount),
                order_id=order.id,
                description=f"Payment received for order ORD-{order.id:04d}",
            )
            db.add(tx)

            await alert_payment_received(
                order_id=order.id,
                customer_name=order.customer.full_name,
                amount=float(order.total_amount),
            )

    await db.commit()
    await db.refresh(order)

    # Re-fetch with relationships
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    order = result.scalar_one()
    return _build_order_out(order)

