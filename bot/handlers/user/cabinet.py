from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.services.text_manager import TextService
from bot.keyboards.inline import get_cabinet_keyboard
from bot.handlers.user.start import check_user_access

cabinet_router = Router()


@cabinet_router.message(F.text.in_(["🏦 Hisobim", "Hisobim"]))
async def on_cabinet_command(
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
    currency = all_settings.get("valyuta", "uc")

    cab_text = await TextService.get_text(
        session=session,
        key="cabinet",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id,
        balance=db_user.balance,
        refcount=db_user.referral_count,
        currency=currency,
        solve=db_user.withdrawn
    )

    solve_btn = await TextService.get_button(session, "solve")
    markup = get_cabinet_keyboard(solve_btn)
    await message.answer(text=cab_text, reply_markup=markup)
