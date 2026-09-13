from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.services.text_manager import TextService
from bot.handlers.user.start import check_user_access

other_router = Router()


@other_router.message(F.text.in_(["🧾 To'lovlar kanali", "To'lovlar kanali"]))
async def on_payments_channel(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    all_settings = await crud.get_all_settings(session)
    vazifa = all_settings.get("vazifa", "Kiritilmagan")

    if not vazifa or vazifa == "Kiritilmagan":
        await message.answer("<b>To'lovlar kanali kiritilmagan!</b>")
        return

    clean_chan = vazifa.lstrip("@")
    tolov_text = await TextService.get_text(
        session=session,
        key="tolovtext",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id
    )
    btn_text = await TextService.get_button(session, "tolov")
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=btn_text, url=f"https://t.me/{clean_chan}")]
        ]
    )
    await message.answer(text=tolov_text, reply_markup=markup, disable_web_page_preview=True)


@other_router.message(F.text.in_(["📚 Qo'llanma", "Qo'llanma"]))
async def on_manual_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    manual_text = await TextService.get_text(
        session=session,
        key="manuals",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id
    )
    await message.answer(text=manual_text, disable_web_page_preview=True)
