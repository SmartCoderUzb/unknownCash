from aiogram import Router
from .panel import panel_router
from .settings import settings_router
from .channels import channels_router
from .users import users_router
from .payments import payments_router
from .texts import texts_router
from .broadcast import broadcast_router
from .withdrawals import withdrawals_admin_router
from .tariffs import tariffs_admin_router
from .orders import orders_admin_router

admin_router = Router()
admin_router.include_router(panel_router)
admin_router.include_router(settings_router)
admin_router.include_router(channels_router)
admin_router.include_router(users_router)
admin_router.include_router(payments_router)
admin_router.include_router(texts_router)
admin_router.include_router(broadcast_router)
admin_router.include_router(withdrawals_admin_router)
admin_router.include_router(tariffs_admin_router)
admin_router.include_router(orders_admin_router)

__all__ = ["admin_router"]
