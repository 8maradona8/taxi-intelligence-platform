import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.settings import settings


def setup_logging() -> None:
    logger = logging.getLogger()

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    logger.info(
        "logging_initialized",
        extra={
            "service": settings.app_name,
            "environment": settings.environment,
        },
    )


logger = logging.getLogger(settings.app_name)