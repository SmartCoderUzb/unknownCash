import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database import crud

logger = logging.getLogger("SubscriptionService")


class SubscriptionService:
    @staticmethod
    async def check_user_subscriptions(bot: Bot, session: AsyncSession, user_id: int) -> tuple[bool, list[dict]]:
        """
        Majburiy kanallarga foydalanuvchi obunasini tekshiradi.
        (is_subscribed_all, channels_info_list) qaytaradi.
        """
        channels = await crud.get_mandatory_channels(session)
        if not channels:
            return True, []

        all_joined = True
        status_list = []

        for ch in channels:
            username = ch.username.lstrip("@")
            chat_id = f"@{username}"
            title = ch.title or username

            try:
                # Agar kanal sarlavhasi saqlanmagan bo'lsa, Telegramdan olishga harakat qilamiz
                if not ch.title:
                    try:
                        chat_info = await bot.get_chat(chat_id)
                        if chat_info.title:
                            title = chat_info.title
                            ch.title = title
                            await session.commit()
                    except Exception:
                        pass

                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                is_member = member.status in ("creator", "administrator", "member", "restricted")
                if not is_member:
                    all_joined = False
                status_list.append({
                    "username": username,
                    "title": title,
                    "is_member": is_member,
                    "url": f"https://t.me/{username}"
                })
            except Exception as e:
                logger.warning(f"Kanal {chat_id} da obunachini tekshirishda ogohlantirish: {e}")
                # Agar bot kanalda admin bo'lmasa yoki kanal yopiq bo'lsa, foydalanuvchini bloklab qo'ymaslik uchun
                status_list.append({
                    "username": username,
                    "title": title,
                    "is_member": False,
                    "url": f"https://t.me/{username}"
                })
                all_joined = False

        return all_joined, status_list

    @staticmethod
    def build_subscription_keyboard(status_list: list[dict], check_btn_text: str = "🔄 Tekshirish") -> InlineKeyboardMarkup:
        keyboard = []
        for ch in status_list:
            prefix = "✅" if ch["is_member"] else "❌"
            btn_text = f"{prefix} {ch['title']}"
            keyboard.append([InlineKeyboardButton(text=btn_text, url=ch["url"])])

        keyboard.append([InlineKeyboardButton(text=check_btn_text, callback_data="check_subscription")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
