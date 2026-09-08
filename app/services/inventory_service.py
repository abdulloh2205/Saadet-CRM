# app/services/inventory_service.py
"""
Core inventory business logic.
INVARIANT: Transferring stock to warehouse "Учтепа" (capacity_limit > 0)
           MUST raise CapacityExceededError if the resulting total would
           exceed capacity_limit.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.stock import MovementType, StockBalance, StockMovement
from app.models.warehouse import Warehouse


class InsufficientStockError(Exception):
    pass


class CapacityExceededError(Exception):
    pass


class WarehouseNotFoundError(Exception):
    pass


async def _get_or_create_balance(
    db: AsyncSession, warehouse_id: int, product_id: int
) -> StockBalance:
    result = await db.execute(
        select(StockBalance)
        .where(
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .with_for_update()
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        balance = StockBalance(warehouse_id=warehouse_id, product_id=product_id, quantity=0)
        db.add(balance)
        await db.flush()
    return balance


async def _get_warehouse_total(db: AsyncSession, warehouse_id: int) -> int:
    """Sum of all product quantities at a given warehouse."""
    result = await db.execute(
        select(StockBalance).where(StockBalance.warehouse_id == warehouse_id)
    )
    balances = result.scalars().all()
    return sum(b.quantity for b in balances)


async def transfer_stock(
    db: AsyncSession,
    *,
    product_id: int,
    from_warehouse_id: int,
    to_warehouse_id: int,
    quantity: int,
    notes: str | None = None,
) -> tuple[StockBalance, StockBalance]:
    """
    Atomically move `quantity` units of `product_id` from one warehouse
    to another. Enforces capacity limit on the destination warehouse.

    Returns:
        (from_balance, to_balance) after the transfer.

    Raises:
        InsufficientStockError: source does not have enough stock.
        CapacityExceededError:  destination capacity_limit would be exceeded.
        WarehouseNotFoundError: one of the warehouse IDs is invalid.
    """
    if quantity <= 0:
        raise ValueError("Transfer quantity must be a positive integer.")

    # --- Validate warehouses ---
    from_wh_result = await db.execute(
        select(Warehouse).where(Warehouse.id == from_warehouse_id)
    )
    from_wh = from_wh_result.scalar_one_or_none()
    if from_wh is None:
        raise WarehouseNotFoundError(f"Warehouse {from_warehouse_id} not found.")

    to_wh_result = await db.execute(select(Warehouse).where(Warehouse.id == to_warehouse_id))
    to_wh = to_wh_result.scalar_one_or_none()
    if to_wh is None:
        raise WarehouseNotFoundError(f"Warehouse {to_warehouse_id} not found.")

    # --- Lock and fetch balances ---
    from_balance = await _get_or_create_balance(db, from_warehouse_id, product_id)
    to_balance = await _get_or_create_balance(db, to_warehouse_id, product_id)

    # --- Check source stock ---
    if from_balance.quantity < quantity:
        raise InsufficientStockError(
            f"Cannot transfer {quantity} units: only {from_balance.quantity} available "
            f"at warehouse '{from_wh.name}'."
        )

    # --- Enforce capacity limit on destination ---
    if to_wh.capacity_limit > 0:
        current_total = await _get_warehouse_total(db, to_warehouse_id)
        if current_total + quantity > to_wh.capacity_limit:
            available_space = to_wh.capacity_limit - current_total
            raise CapacityExceededError(
                f"Transfer would exceed capacity of warehouse '{to_wh.name}' "
                f"(limit={to_wh.capacity_limit}). "
                f"Current total: {current_total}, trying to add: {quantity}. "
                f"Available space: {available_space}."
            )

    # --- Perform transfer ---
    from_balance.quantity -= quantity
    to_balance.quantity += quantity

    # --- Record ledger entries ---
    ref = f"TRANSFER-{from_warehouse_id}->{to_warehouse_id}"
    db.add(
        StockMovement(
            warehouse_id=from_warehouse_id,
            product_id=product_id,
            movement_type=MovementType.TRANSFER_OUT,
            quantity=quantity,
            reference_id=ref,
            notes=notes,
        )
    )
    db.add(
        StockMovement(
            warehouse_id=to_warehouse_id,
            product_id=product_id,
            movement_type=MovementType.TRANSFER_IN,
            quantity=quantity,
            reference_id=ref,
            notes=notes,
        )
    )

    await db.commit()

    # Re-fetch both balances with eager relationships for serialization
    from_result = await db.execute(
        select(StockBalance)
        .where(StockBalance.id == from_balance.id)
        .options(selectinload(StockBalance.warehouse), selectinload(StockBalance.product))
    )
    to_result = await db.execute(
        select(StockBalance)
        .where(StockBalance.id == to_balance.id)
        .options(selectinload(StockBalance.warehouse), selectinload(StockBalance.product))
    )
    return from_result.scalar_one(), to_result.scalar_one()


async def get_all_balances(db: AsyncSession) -> list[StockBalance]:
    result = await db.execute(
        select(StockBalance)
        .options(
            selectinload(StockBalance.warehouse),
            selectinload(StockBalance.product),
        )
        .order_by(StockBalance.warehouse_id, StockBalance.product_id)
    )
    return list(result.scalars().all())


async def check_low_stock(db: AsyncSession, product_id: int) -> None:
    """
    Check if the total stock of a product across ALL warehouses
    has fallen to or below its min_stock_threshold. If so, fire an alert.
    """
    from app.bot.alerts import alert_low_stock
    from sqlalchemy import func as sqlfunc

    # Get product
    prod_result = await db.execute(select(Product).where(Product.id == product_id))
    product = prod_result.scalar_one_or_none()
    if not product or product.min_stock_threshold <= 0:
        return

    # Sum total quantity across all warehouses
    total_result = await db.execute(
        select(sqlfunc.coalesce(sqlfunc.sum(StockBalance.quantity), 0))
        .where(StockBalance.product_id == product_id)
    )
    total_qty = int(total_result.scalar_one())

    if total_qty <= product.min_stock_threshold:
        await alert_low_stock(
            product_title=product.title,
            warehouse_name="Все склады (суммарно)",
            qty=total_qty,
        )
