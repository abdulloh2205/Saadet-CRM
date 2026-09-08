# app/services/order_service.py
"""
Order business logic.
INVARIANT:
  - Creating/dispatching an order automatically:
    1. Creates StockMovement (SALE_DISPATCH) per order item and decrements stock.
    2. If payment_status == PAID, records a FinancialTransaction (INCOME / SALES_REVENUE).
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.finance import FinancialTransaction, TransactionCategory, TransactionType
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.stock import MovementType, StockBalance, StockMovement
from app.schemas.order import CreateOrderRequest


class InsufficientStockError(Exception):
    pass


async def _decrement_stock(
    db: AsyncSession, warehouse_id: int, product_id: int, quantity: int, order_ref: str
) -> None:
    result = await db.execute(
        select(StockBalance)
        .where(
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .with_for_update()
    )
    balance = result.scalar_one_or_none()
    if balance is None or balance.quantity < quantity:
        avail = balance.quantity if balance else 0
        raise InsufficientStockError(
            f"Insufficient stock for product {product_id}: need {quantity}, have {avail}."
        )
    balance.quantity -= quantity
    db.add(
        StockMovement(
            warehouse_id=warehouse_id,
            product_id=product_id,
            movement_type=MovementType.SALE_DISPATCH,
            quantity=quantity,
            reference_id=order_ref,
            notes=f"Dispatched on order {order_ref}",
        )
    )


async def create_order(db: AsyncSession, payload: CreateOrderRequest) -> Order:
    """
    Creates a new order, decrements stock for each item, and logs an INCOME
    transaction if the order is marked as paid.
    """
    # Calculate totals
    total = sum(item.unit_price * item.quantity for item in payload.items)
    is_paid = payload.mark_paid

    order = Order(
        customer_id=payload.customer_id,
        dispatch_warehouse_id=payload.dispatch_warehouse_id,
        status=OrderStatus.NEW,
        payment_status=PaymentStatus.PAID if is_paid else PaymentStatus.UNPAID,
        total_amount=total,
        amount_paid=total if is_paid else 0.0,
        delivery_address=payload.delivery_address,
        notes=payload.notes,
    )
    db.add(order)
    await db.flush()  # get order.id

    order_ref = f"ORD-{order.id:04d}"

    for item_data in payload.items:
        item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
        )
        db.add(item)
        # Decrement stock + create movement
        await _decrement_stock(
            db,
            warehouse_id=payload.dispatch_warehouse_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            order_ref=order_ref,
        )
        # Check if stock fell below threshold
        from app.services.inventory_service import check_low_stock
        await check_low_stock(db, item_data.product_id)

    # Record income transaction if paid
    if is_paid:
        tx = FinancialTransaction(
            transaction_type=TransactionType.INCOME,
            category=TransactionCategory.SALES_REVENUE,
            amount=total,
            order_id=order.id,
            description=f"Sale revenue for order {order_ref}",
        )
        db.add(tx)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
    )
    return result.scalar_one()


async def get_orders(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
