# app/api/public_router.py
"""
Public API endpoints for the upcoming website integration.
No authentication required (rate-limiting should be added in production).
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.alerts import send_admin_alert
from app.database import get_db
from app.models.order import Customer, Order, OrderItem, OrderStatus, PaymentStatus
from app.models.stock import MovementType, StockBalance, StockMovement
from app.models.finance import FinancialTransaction, TransactionCategory, TransactionType
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public"])


# ── Request schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    phone: str
    email: str | None = None


class PublicOrderItem(BaseModel):
    product_id: int
    quantity: int


class PublicOrderRequest(BaseModel):
    customer_name: str
    phone: str
    district: str              # "Ташкент, Юнусабад"
    items: list[PublicOrderItem]
    total_price: float
    notes: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_customer(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new customer from the website contact form.
    Fires an immediate Telegram admin alert.
    """
    # Upsert by phone
    existing = (await db.execute(
        select(Customer).where(Customer.phone == payload.phone)
    )).scalar_one_or_none()

    if existing:
        return {"status": "exists", "customer_id": existing.id, "message": "Клиент уже зарегистрирован."}

    customer = Customer(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        tags="Сайт",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    # Alert admin immediately
    await send_admin_alert(
        f"👤 <b>Новая регистрация на сайте</b>\n"
        f"Имя: <b>{payload.full_name}</b>\n"
        f"Тел: <b>{payload.phone}</b>"
        + (f"\nEmail: {payload.email}" if payload.email else "")
    )

    return {"status": "created", "customer_id": customer.id}


@router.post("/order", status_code=status.HTTP_201_CREATED)
async def create_website_order(payload: PublicOrderRequest, db: AsyncSession = Depends(get_db)):
    """
    Create an order from the website.
    Decrements stock, saves order, fires Telegram admin alert.
    """
    from app.models.product import Product

    # Fetch or create customer
    cust = (await db.execute(
        select(Customer).where(Customer.phone == payload.phone)
    )).scalar_one_or_none()

    if not cust:
        cust = Customer(
            full_name=payload.customer_name,
            phone=payload.phone,
            tags="Сайт",
        )
        db.add(cust)
        await db.flush()

    # Create order
    order = Order(
        customer_id=cust.id,
        status=OrderStatus.NEW,
        payment_status=PaymentStatus.UNPAID,
        total_amount=payload.total_price,
        amount_paid=0.0,
        district=payload.district,
        notes=payload.notes,
        source="website",
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.add(order)
    await db.flush()

    order_ref = f"ORD-{order.id:04d}"
    product_lines: list[str] = []

    for item_data in payload.items:
        # Get product title
        prod = (await db.execute(
            select(Product).where(Product.id == item_data.product_id)
        )).scalar_one_or_none()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Товар {item_data.product_id} не найден.")

        # Decrement stock (from first warehouse that has enough)
        bal_result = await db.execute(
            select(StockBalance)
            .where(StockBalance.product_id == item_data.product_id, StockBalance.quantity >= item_data.quantity)
            .order_by(StockBalance.warehouse_id)
            .limit(1)
            .with_for_update()
        )
        bal = bal_result.scalar_one_or_none()

        if not bal:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Недостаточно товара: {prod.title}",
            )

        bal.quantity -= item_data.quantity
        db.add(StockMovement(
            warehouse_id=bal.warehouse_id,
            product_id=item_data.product_id,
            movement_type=MovementType.SALE_DISPATCH,
            quantity=item_data.quantity,
            reference_id=order_ref,
        ))

        order.dispatch_warehouse_id = bal.warehouse_id

        # Check low stock threshold
        from app.services.inventory_service import check_low_stock
        await check_low_stock(db, item_data.product_id)

        item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=float(prod.retail_price),
        )
        db.add(item)
        product_lines.append(f"  • {prod.title} — {item_data.quantity} шт.")

    await db.commit()

    # Format total
    total_fmt = f"{int(payload.total_price):,}".replace(",", " ") + " сум"

    # Alert admin
    items_text = "\n".join(product_lines)
    await send_admin_alert(
        f"🔔 <b>НОВЫЙ ЗАКАЗ С САЙТА!</b>\n"
        f"Номер: <b>#{order.id:04d}</b>\n"
        f"Клиент: <b>{payload.customer_name}</b> (тел: {payload.phone})\n"
        f"Район: <b>{payload.district}</b>\n"
        f"Товары:\n{items_text}\n"
        f"Сумма: <b>{total_fmt}</b>"
        + (f"\nПримечание: {payload.notes}" if payload.notes else "")
    )

    return {
        "status": "created",
        "order_id": order.id,
        "order_ref": order_ref,
        "message": "Заказ принят. Мы свяжемся с вами в ближайшее время.",
    }
