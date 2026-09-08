# main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.finance_router import router as finance_router
from app.api.inventory_router import router as inventory_router
from app.api.order_router import router as order_router
from app.api.public_router import router as public_router
from app.api.lead_router import router as lead_router
from app.bot.handlers import build_dp, setup_bot_ui
from app.config import settings
from app.database import init_db, SessionLocal
from app.services.seed_service import seed_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database...")
    await init_db()
    logger.info("Database ready.")
    # Auto-seed on first boot (idempotent — skips if data already exists)
    async with SessionLocal() as db:
        result = await seed_all(db)
        logger.info(f"Seed: {result}")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="ToyStore Ops API",
    description="Manager Bot — Children's Toy & Flashcard Store Management",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_router)
app.include_router(order_router)
app.include_router(finance_router)
app.include_router(public_router)
app.include_router(lead_router)

WEBAPP_DIR = Path(__file__).parent / "app" / "webapp"
if WEBAPP_DIR.exists():
    app.mount("/webapp", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")


@app.get("/", include_in_schema=False)
async def root():
    index = WEBAPP_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "ToyStore Ops API v2.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "app": "ToyStore Ops"}


async def run_bot():
    if settings.bot_token == "CHANGE_ME":
        logger.warning("BOT_TOKEN not set — bot polling disabled.")
        return
    logger.info("Starting Telegram bot...")
    bot, dp = build_dp()
    await setup_bot_ui(bot)
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()


async def run_server():
    config = uvicorn.Config(
        app=app,
        host=settings.app_host,
        port=settings.app_port,
        loop="none",
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logger.info(f"Server: http://{settings.app_host}:{settings.app_port}")
    logger.info(f"WebApp: {settings.webapp_url}")
    await asyncio.gather(run_server(), run_bot())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped.")
