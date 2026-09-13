from aiogram import Router
from aiogram.types import ErrorEvent
import logging

logger = logging.getLogger("CommonHandler")
common_router = Router()


@common_router.errors()
async def error_handler(event: ErrorEvent):
    logger.exception(f"Xatolik yuz berdi: {event.exception}", exc_info=event.exception)
