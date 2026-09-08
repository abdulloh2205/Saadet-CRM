# app/bot/handlers.py
"""
ToyStore Ops — Telegram Bot handlers (aiogram 3.x)
Clean, no reply keyboard clutter. Menu button + inline WebApp button only.
"""
import logging

import httpx
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Message,
    WebAppInfo,
)

from app.bot.alerts import send_admin_alert, set_bot
from app.config import settings

logger = logging.getLogger(__name__)
router = Router(name="toystore-router")


def build_dp() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp


async def setup_bot_ui(bot: Bot) -> None:
    """Configure native Telegram menu button + command list at startup."""
    set_bot(bot)
    try:
        # Native bottom-left menu button pointing to the WebApp
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📦 Открыть систему",
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        )
        # Bot command list
        await bot.set_my_commands([
            BotCommand(command="start", description="Открыть панель управления"),
            BotCommand(command="stock", description="Остатки на складах"),
            BotCommand(command="help", description="Справка"),
        ])
        logger.info("Bot UI (menu button + commands) configured.")
    except Exception as e:
        logger.warning(f"Could not configure bot UI: {e}")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 Открыть панель управления",
                    web_app=WebAppInfo(url=settings.webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        text=(
            "👋 Добро пожаловать в панель управления магазином детских игрушек.\n\n"
            "Нажмите кнопку ниже для запуска системы."
        ),
        reply_markup=keyboard,
    )


@router.message(Command("stock"))
async def cmd_stock(message: Message) -> None:
    api_url = f"http://localhost:{settings.app_port}/api/inventory/summary"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(api_url)
            resp.raise_for_status()
            data = resp.json()

        wh = data.get("warehouses", [])
        uchtepa = data.get("uchtepa_capacity", {})
        lines = ["📦 <b>Остатки на складах</b>\n"]

        for w in wh:
            lines.append(f"🏭 <b>{w['name']}</b>")
            for item in w.get("products", []):
                lines.append(f"  • {item['title']}: <b>{item['quantity']} шт.</b>")

        if uchtepa:
            cur = uchtepa.get("current", 0)
            cap = uchtepa.get("limit", 100)
            pct = round(cur / cap * 100)
            lines.append(f"\n📊 Офис Учтепа: <b>{cur}/{cap}</b> ({pct}% заполнен)")

        await message.answer("\n".join(lines), parse_mode="HTML")

    except Exception as e:
        logger.exception(e)
        await message.answer("⚠️ Не удалось получить данные. Проверьте, что сервер запущен.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Manager Bot — ToyStore Ops</b>\n\n"
        "/start — открыть панель управления\n"
        "/stock — остатки на складах\n"
        "/help — эта справка",
        parse_mode="HTML",
    )
