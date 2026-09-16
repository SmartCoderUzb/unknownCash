import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from bot.core.config import settings
from bot.database import crud

logger = logging.getLogger("UserTrackerMiddleware")


class UserTrackerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: TgUser | None = data.get("event_from_user")
        if not event_user or event_user.is_bot:
            return await handler(event, data)

        session: AsyncSession = data.get("session")
        if not session:
            return await handler(event, data)

        bot: Bot = data.get("bot")

        # 1. Foydalanuvchini bazadan olish yoki yaratish
        user, is_new = await crud.get_or_create_user(
            session=session,
            user_id=event_user.id,
            username=event_user.username,
            first_name=event_user.first_name,
            last_name=event_user.last_name
        )

        data["db_user"] = user
        data["is_new_user"] = is_new

        # 2. Ban tekshiruvi: agar bloklangan bo'lsa va admin bo'lmasa, jarayon to'xtatiladi
        is_admin = settings.is_admin(event_user.id)
        if user.is_banned and not is_admin:
            if isinstance(event, CallbackQuery):
                await event.answer("Siz botdan bloklangansiz!", show_alert=True)
            return

        # 3. Yangi obunachi bo'lsa, adminga bildirishnoma yuborish
        if is_new and bot:
            admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
            if admin_target and admin_target != event_user.id:
                try:
                    await bot.send_message(
                        chat_id=admin_target,
                        text="<b>👤 Yangi obunachi botga qo'shildi!</b>",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Adminga yangi a'zo xabarini yuborishda ogohlantirish: {e}")

        return await handler(event, data)
