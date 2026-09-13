import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database.models import User
from bot.states.user_states import UserStates
from bot.services.text_manager import TextService
from bot.keyboards.reply import get_main_menu, get_back_keyboard
from bot.handlers.user.start import check_user_access

logger = logging.getLogger("UserSupport")
support_router = Router()


@support_router.message(F.text.in_(["💌 Yordam", "Yordam"]))
async def on_support_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    send_supp_text = await TextService.get_text(
        session=session,
        key="sendSuppMsg",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id
    )
    back_kb = await get_back_keyboard(session)
    await message.answer(text=send_supp_text, reply_markup=back_kb)
    await state.set_state(UserStates.waiting_for_support_message)


@support_router.message(UserStates.waiting_for_support_message)
async def on_support_message_received(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    text_content = message.text or message.caption or "Fayl/Media"

    # Adminga yuborish
    admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
    if admin_target:
        username_link = f"@{message.from_user.username}" if message.from_user.username else str(db_user.id)
        admin_msg = (
            f"<a href='https://t.me/{message.from_user.username or ''}'>{db_user.id}</a> "
            f"<b>dan yangi murojaat:</b>\n\n{text_content}"
        )
        try:
            await bot.send_message(
                chat_id=admin_target,
                text=admin_msg,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Adminga murojaatni uzatishda xatolik: {e}")

    # Foydalanuvchiga tasdiqlash xabari
    supp_send_text = await TextService.get_text(
        session=session,
        key="SuppSend",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id
    )
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)

    await state.clear()
    await message.answer(text=supp_send_text, reply_markup=menu_kb)
