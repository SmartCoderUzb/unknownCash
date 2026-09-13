from aiogram import Router
from .start import start_router
from .cabinet import cabinet_router
from .earn import earn_router
from .withdraw import withdraw_router
from .support import support_router
from .other import other_router

user_router = Router()
user_router.include_router(start_router)
user_router.include_router(cabinet_router)
user_router.include_router(earn_router)
user_router.include_router(withdraw_router)
user_router.include_router(support_router)
user_router.include_router(other_router)

__all__ = ["user_router"]
