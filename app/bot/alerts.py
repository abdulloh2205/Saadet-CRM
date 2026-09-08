# app/bot/alerts.py
"""Alert dispatcher — sends beautiful HTML notifications to ADMIN_CHAT_ID."""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)

# Global bot reference set at startup
_bot_instance = None


def set_bot(bot) -> None:
    global _bot_instance
    _bot_instance = bot


async def send_admin_alert(text: str, bot=None) -> None:
    """
    Send an HTML alert to ADMIN_CHAT_ID.
    Uses global bot instance if bot arg not provided.
    Silently swallows errors (never crash the main flow).
    """
    from app.config import settings

    b = bot or _bot_instance
    chat_id = settings.admin_chat_id

    if not b or not chat_id:
        logger.warning(f"Admin alert skipped (no bot or ADMIN_CHAT_ID): {text[:80]}")
        return

    try:
        await b.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send admin alert: {e}")


# ── Specific Alert Formatters ──────────────────────────────────────────────────

def fmt_price(amount) -> str:
    """Format number as '1 200 000 сум'."""
    try:
        return f"{int(round(float(amount))):,}".replace(",", " ") + " сум"
    except (ValueError, TypeError):
        return str(amount)


async def alert_new_order(order_id: int, customer_name: str, total: float,
                          district: str | None = None, source: str = "bot",
                          items_summary: str = "") -> None:
    """New order created."""
    src = "🌐 Сайт" if source == "website" else "🤖 Бот"
    text = (
        f"🛒 <b>Новый заказ!</b>\n\n"
        f"Номер: <b>#{order_id:04d}</b>\n"
        f"Клиент: <b>{customer_name}</b>\n"
        f"Сумма: <b>{fmt_price(total)}</b>\n"
    )
    if district:
        text += f"Район: {district}\n"
    if items_summary:
        text += f"\n📦 Состав:\n{items_summary}\n"
    text += f"\nИсточник: {src}"
    await send_admin_alert(text)


async def alert_order_status_changed(order_id: int, customer_name: str,
                                     old_status: str, new_status: str,
                                     total: float = 0) -> None:
    """Order status transition."""
    emoji_map = {
        "NEW": "🆕",
        "PACKED": "📦",
        "DELIVERING": "🚚",
        "DELIVERED": "✅",
        "CANCELLED": "❌",
    }
    emoji = emoji_map.get(new_status, "🔄")

    text = (
        f"{emoji} <b>Статус заказа изменён</b>\n\n"
        f"Заказ: <b>#{order_id:04d}</b>\n"
        f"Клиент: <b>{customer_name}</b>\n"
        f"Статус: <s>{old_status}</s> → <b>{new_status}</b>\n"
    )
    if new_status == "DELIVERED":
        text += f"\n💰 Сумма к получению: <b>{fmt_price(total)}</b>"
    await send_admin_alert(text)


async def alert_payment_received(order_id: int, customer_name: str,
                                 amount: float) -> None:
    """Payment confirmed."""
    text = (
        f"💳 <b>Оплата получена!</b>\n\n"
        f"Заказ: <b>#{order_id:04d}</b>\n"
        f"Клиент: <b>{customer_name}</b>\n"
        f"Сумма: <b>{fmt_price(amount)}</b>"
    )
    await send_admin_alert(text)


async def alert_stock_transferred(product_title: str, quantity: int,
                                  from_wh: str, to_wh: str,
                                  from_remaining: int, to_total: int) -> None:
    """Stock transferred between warehouses."""
    text = (
        f"📦 <b>Перемещение товара</b>\n\n"
        f"Товар: <b>{product_title}</b>\n"
        f"Количество: <b>{quantity} шт.</b>\n"
        f"Откуда: {from_wh} (ост. {from_remaining})\n"
        f"Куда: {to_wh} (итого {to_total})"
    )
    await send_admin_alert(text)


async def alert_capacity_warning(warehouse_name: str, current: int,
                                 limit: int) -> None:
    """Warehouse capacity is running high."""
    pct = round(current / limit * 100) if limit > 0 else 0
    if pct >= 90:
        emoji = "🔴"
        urgency = "КРИТИЧНО"
    elif pct >= 75:
        emoji = "🟡"
        urgency = "ВНИМАНИЕ"
    else:
        return  # Don't alert below 75%

    text = (
        f"{emoji} <b>Склад: {urgency}!</b>\n\n"
        f"Склад: <b>{warehouse_name}</b>\n"
        f"Заполнен: <b>{current}/{limit}</b> ({pct}%)\n"
        f"Свободно: <b>{limit - current} коробок</b>"
    )
    await send_admin_alert(text)


async def alert_low_stock(product_title: str, warehouse_name: str,
                          qty: int) -> None:
    """Product stock is critically low."""
    text = (
        f"📉 <b>Низкий остаток!</b>\n\n"
        f"Товар: <b>{product_title}</b>\n"
        f"Склад: {warehouse_name}\n"
        f"Осталось: <b>{qty} шт.</b>"
    )
    await send_admin_alert(text)


# Legacy compat
async def send_capacity_alert(bot, chat_id: int, warehouse_name: str,
                               current: int, limit: int) -> None:
    await alert_capacity_warning(warehouse_name, current, limit)


async def send_low_stock_alert(bot, chat_id: int, product_title: str,
                                warehouse_name: str, qty: int) -> None:
    await alert_low_stock(product_title, warehouse_name, qty)
