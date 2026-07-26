from sqlalchemy import text

from app.core.logging import logger
from app.database.engine import engine


async def check_database() -> bool:
    """
    Verify that PostgreSQL is reachable.
    """

    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT version();"))

            version = result.scalar_one()

            logger.info(f"Connected to PostgreSQL: {version}")

            return True

    except Exception:
        logger.exception("Unable to connect to PostgreSQL.")

        return False
