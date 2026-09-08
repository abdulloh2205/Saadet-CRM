# app/services/seed_service.py
"""Idempotent seed: Children toy store data. Wipes stale data and re-seeds."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import (
    FinancialTransaction, Receivable, ReceivableStatus,
    TransactionCategory, TransactionType,
)
from app.models.order import Customer, Order, OrderItem, OrderStatus, PaymentStatus
from app.models.product import Product
from app.models.stock import MovementType, StockBalance, StockMovement
from app.models.user import User, UserRole
from app.models.warehouse import Warehouse


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)

def _days_ago(n: int) -> datetime:
    return _now() - timedelta(days=n)


async def seed_all(db: AsyncSession) -> dict:
    summary: dict[str, int] = {}

    # --- Check if already seeded ---
    wh_check = (await db.execute(select(Warehouse))).scalars().all()
    if wh_check:
        return {"status": "already seeded — skipped"}

    # ── 1. Warehouses ─────────────────────────────────────────────────────────
    rustaveli = Warehouse(
        name="Основной склад (Руставели)",
        capacity_limit=0,
        address="г. Ташкент, ул. Шота Руставели, 24",
        description="Главный склад хранения товаров.",
    )
    uchtepa = Warehouse(
        name="Офис выдачи (Учтепа)",
        capacity_limit=100,
        address="г. Ташкент, Учтепинский р-н",
        description="Офис фасовки и выдачи. Лимит — 100 коробок.",
    )
    db.add_all([rustaveli, uchtepa])
    await db.flush()

    # ── 2. Products ───────────────────────────────────────────────────────────
    p1 = Product(
        sku="TOY-CARD-001",
        title="Карточки «Мир Животных» (50 карт)",
        description="Развивающие карточки с яркими иллюстрациями животных. 50 ламинированных карт.",
        cost_price=35_000, retail_price=120_000, min_margin_pct=0,
    )
    p2 = Product(
        sku="TOY-CARD-002",
        title="Развивающие карточки «Логика и Счёт»",
        description="Карточки для развития логики, счёта и математического мышления. 40 карт.",
        cost_price=40_000, retail_price=140_000, min_margin_pct=0,
    )
    p3 = Product(
        sku="TOY-WOOD-003",
        title="Деревянный сортер «Геометрия»",
        description="Развивающий сортер из натурального дерева. 12 форм, 6 цветов.",
        cost_price=75_000, retail_price=220_000, min_margin_pct=0,
    )
    p4 = Product(
        sku="TOY-SENS-004",
        title="Сенсорные тактильные карточки",
        description="Карточки с тактильными поверхностями для развития осязания. 30 карт.",
        cost_price=50_000, retail_price=160_000, min_margin_pct=0,
    )
    db.add_all([p1, p2, p3, p4])
    await db.flush()

    # ── 3. Stock Balances ─────────────────────────────────────────────────────
    balances = [
        StockBalance(warehouse_id=rustaveli.id, product_id=p1.id, quantity=70),
        StockBalance(warehouse_id=rustaveli.id, product_id=p2.id, quantity=55),
        StockBalance(warehouse_id=rustaveli.id, product_id=p3.id, quantity=35),
        StockBalance(warehouse_id=rustaveli.id, product_id=p4.id, quantity=20),
        StockBalance(warehouse_id=uchtepa.id,   product_id=p1.id, quantity=18),
        StockBalance(warehouse_id=uchtepa.id,   product_id=p2.id, quantity=12),
        StockBalance(warehouse_id=uchtepa.id,   product_id=p3.id, quantity=8),
        StockBalance(warehouse_id=uchtepa.id,   product_id=p4.id, quantity=4),
    ]
    db.add_all(balances)

    movements = [
        StockMovement(warehouse_id=rustaveli.id, product_id=p1.id, movement_type=MovementType.RECEIPT, quantity=80, notes="Первичный приход"),
        StockMovement(warehouse_id=rustaveli.id, product_id=p2.id, movement_type=MovementType.RECEIPT, quantity=60, notes="Первичный приход"),
        StockMovement(warehouse_id=rustaveli.id, product_id=p3.id, movement_type=MovementType.RECEIPT, quantity=40, notes="Первичный приход"),
        StockMovement(warehouse_id=rustaveli.id, product_id=p4.id, movement_type=MovementType.RECEIPT, quantity=25, notes="Первичный приход"),
        StockMovement(warehouse_id=uchtepa.id,   product_id=p1.id, movement_type=MovementType.TRANSFER_IN, quantity=18, reference_id="INIT", notes="Заброска в офис"),
        StockMovement(warehouse_id=uchtepa.id,   product_id=p2.id, movement_type=MovementType.TRANSFER_IN, quantity=12, reference_id="INIT", notes="Заброска в офис"),
        StockMovement(warehouse_id=uchtepa.id,   product_id=p3.id, movement_type=MovementType.TRANSFER_IN, quantity=8,  reference_id="INIT", notes="Заброска в офис"),
        StockMovement(warehouse_id=uchtepa.id,   product_id=p4.id, movement_type=MovementType.TRANSFER_IN, quantity=4,  reference_id="INIT", notes="Заброска в офис"),
    ]
    db.add_all(movements)
    await db.flush()

    # ── 4. Users ──────────────────────────────────────────────────────────────
    users = [
        User(telegram_id=100000001, username="admin_toystore", full_name="Администратор", role=UserRole.OWNER),
        User(telegram_id=100000002, username="manager_ops",    full_name="Менеджер",      role=UserRole.MANAGER),
    ]
    db.add_all(users)
    await db.flush()

    # ── 5. Customers ──────────────────────────────────────────────────────────
    customers = [
        Customer(full_name="Дилноза Юсупова",   phone="+998901112233", instagram_handle="@dilnoza.mama",    tags="Мама,Постоянный"),
        Customer(full_name="Феруза Каримова",    phone="+998907778899", instagram_handle="@feruza_kids",     tags="Мама,VIP"),
        Customer(full_name="Ботир Ниёзов",       phone="+998935556677", telegram_username="botir_n",         tags="Папа"),
        Customer(full_name="Нилуфар Рашидова",   phone="+998974443322", instagram_handle="@nilufar_family",  tags="Мама,Новый"),
    ]
    db.add_all(customers)
    await db.flush()
    c1, c2, c3, c4 = customers

    # ── 6. Orders ─────────────────────────────────────────────────────────────
    ord1 = Order(
        customer_id=c1.id, dispatch_warehouse_id=uchtepa.id,
        status=OrderStatus.DELIVERED, payment_status=PaymentStatus.PAID,
        total_amount=2*120_000 + 1*140_000, amount_paid=2*120_000 + 1*140_000,
        district="Ташкент, Мирзо-Улугбек", source="bot",
        created_at=_days_ago(10), updated_at=_days_ago(9),
    )
    ord2 = Order(
        customer_id=c2.id, dispatch_warehouse_id=uchtepa.id,
        status=OrderStatus.DELIVERED, payment_status=PaymentStatus.PAID,
        total_amount=1*220_000 + 2*160_000, amount_paid=1*220_000 + 2*160_000,
        district="Ташкент, Чиланзар", source="bot",
        created_at=_days_ago(5), updated_at=_days_ago(4),
    )
    ord3 = Order(
        customer_id=c3.id, dispatch_warehouse_id=uchtepa.id,
        status=OrderStatus.DELIVERING, payment_status=PaymentStatus.UNPAID,
        total_amount=3*120_000, amount_paid=0,
        district="Ташкент, Юнусабад", source="bot",
        created_at=_days_ago(2), updated_at=_days_ago(1),
    )
    ord4 = Order(
        customer_id=c4.id, dispatch_warehouse_id=uchtepa.id,
        status=OrderStatus.NEW, payment_status=PaymentStatus.UNPAID,
        total_amount=1*140_000 + 1*220_000, amount_paid=0,
        district="Ташкент, Яшнабад", source="website",
        notes="Доставка после 18:00",
        created_at=_days_ago(0), updated_at=_days_ago(0),
    )
    db.add_all([ord1, ord2, ord3, ord4])
    await db.flush()

    items = [
        OrderItem(order_id=ord1.id, product_id=p1.id, quantity=2, unit_price=120_000),
        OrderItem(order_id=ord1.id, product_id=p2.id, quantity=1, unit_price=140_000),
        OrderItem(order_id=ord2.id, product_id=p3.id, quantity=1, unit_price=220_000),
        OrderItem(order_id=ord2.id, product_id=p4.id, quantity=2, unit_price=160_000),
        OrderItem(order_id=ord3.id, product_id=p1.id, quantity=3, unit_price=120_000),
        OrderItem(order_id=ord4.id, product_id=p2.id, quantity=1, unit_price=140_000),
        OrderItem(order_id=ord4.id, product_id=p3.id, quantity=1, unit_price=220_000),
    ]
    db.add_all(items)

    dispatch_movements = [
        StockMovement(warehouse_id=uchtepa.id, product_id=p1.id, movement_type=MovementType.SALE_DISPATCH, quantity=2, reference_id="ORD-0001"),
        StockMovement(warehouse_id=uchtepa.id, product_id=p2.id, movement_type=MovementType.SALE_DISPATCH, quantity=1, reference_id="ORD-0001"),
        StockMovement(warehouse_id=uchtepa.id, product_id=p3.id, movement_type=MovementType.SALE_DISPATCH, quantity=1, reference_id="ORD-0002"),
        StockMovement(warehouse_id=uchtepa.id, product_id=p4.id, movement_type=MovementType.SALE_DISPATCH, quantity=2, reference_id="ORD-0002"),
        StockMovement(warehouse_id=uchtepa.id, product_id=p1.id, movement_type=MovementType.SALE_DISPATCH, quantity=3, reference_id="ORD-0003"),
    ]
    db.add_all(dispatch_movements)
    await db.flush()

    # ── 7. Financial Transactions ─────────────────────────────────────────────
    txs = [
        FinancialTransaction(transaction_type=TransactionType.INCOME, category=TransactionCategory.SALES_REVENUE,
            amount=380_000, order_id=ord1.id, description="Выручка заказ #1 (Мирзо-Улугбек)", created_at=_days_ago(9)),
        FinancialTransaction(transaction_type=TransactionType.INCOME, category=TransactionCategory.SALES_REVENUE,
            amount=540_000, order_id=ord2.id, description="Выручка заказ #2 (Чиланзар)", created_at=_days_ago(4)),
        FinancialTransaction(transaction_type=TransactionType.EXPENSE, category=TransactionCategory.SUPPLIER_PAYMENT,
            amount=2_050_000, description="Закупка товаров у поставщика", created_at=_days_ago(15)),
        FinancialTransaction(transaction_type=TransactionType.EXPENSE, category=TransactionCategory.LOGISTICS,
            amount=180_000, description="Курьерская доставка", created_at=_days_ago(3)),
        FinancialTransaction(transaction_type=TransactionType.EXPENSE, category=TransactionCategory.MARKETING,
            amount=350_000, description="Реклама Instagram", created_at=_days_ago(7)),
    ]
    db.add_all(txs)
    await db.flush()

    await db.commit()

    summary = {
        "warehouses": 2, "products": 4, "stock_balances": 8,
        "customers": 4, "orders": 4, "transactions": len(txs),
    }
    return summary
