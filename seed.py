# seed.py — Standalone seed runner
"""
Run this script once to populate the database with realistic mock data.
Safe to run multiple times (idempotent).

Usage:
    python seed.py
"""
import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def main():
    # Init DB tables first
    from app.database import init_db, SessionLocal
    from app.services.seed_service import seed_all

    logger.info("🔧 Initialising database tables...")
    await init_db()
    logger.info("✅ Tables created / verified.")

    logger.info("🌱 Running seed data...")
    async with SessionLocal() as db:
        summary = await seed_all(db)

    logger.info("✅ Seed complete! Summary:")
    for key, count in summary.items():
        if count > 0:
            logger.info(f"   + {count} {key}")
        else:
            logger.info(f"   ~ {key}: already seeded (skipped)")

    logger.info("\n🚀 Ready! Run the app with:  python main.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Seed failed: {e}", exc_info=True)
        sys.exit(1)
