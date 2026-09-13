import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.services.text_manager import TextService
from bot.keyboards.inline import get_share_keyboard
from bot.handlers.user.start import check_user_access

logger = logging.getLogger("UserEarn")
earn_router = Router()

EARN_PHOTO_URL = "https://t.me/BOT_UCHUN_RASMLAR/12"


@earn_router.message(F.text.in_(["🎁 Uc ishlash", "Uc ishlash"]))
async def on_earn_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    bot_info = await bot.get_me()
    all_settings = await crud.get_all_settings(session)
    currency = all_settings.get("valyuta", "uc")
    taklif_price = all_settings.get("taklif", "5")
    reflink = f"https://t.me/{bot_info.username}?start={db_user.id}"

    earn_text = await TextService.get_text(
        session=session,
        key="earnRef",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id,
        reflink=reflink,
        refpay=taklif_price,
        refcount=db_user.referral_count,
        balance=db_user.balance,
        currency=currency
    )

    share_btn = await TextService.get_button(session, "share")
    markup = get_share_keyboard(share_btn, bot_info.username, db_user.id)

    try:
        await message.answer_photo(
            photo=EARN_PHOTO_URL,
            caption=earn_text,
            reply_markup=markup
        )
    except Exception as e:
        logger.warning(f"Rasm yuborishda xatolik ({e}), matn ko'rinishida yuborilmoqda.")
        await message.answer(
            text=earn_text,
            reply_markup=markup,
            disable_web_page_preview=True
        )
