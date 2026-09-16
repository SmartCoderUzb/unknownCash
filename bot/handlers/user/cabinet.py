from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.states.user_states import UserStates
from bot.services.text_manager import TextService
from bot.keyboards.inline import get_cabinet_inline_keyboard
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu
from bot.handlers.user.start import check_user_access
from bot.core.config import settings

cabinet_router = Router()


@cabinet_router.message(F.text.in_(["👤 Hisob", "Hisob", "🏦 Hisobim", "Hisobim"]))
async def on_cabinet_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await state.clear()
    can_proceed = await check_user_access(message, session, state, bot, db_user)
    if not can_proceed:
        return

    all_settings = await crud.get_all_settings(session)
    currency = all_settings.get("valyuta", "UC")
    pubg_id_text = db_user.pubg_id or "Kiritilmagan"

    cab_text = await TextService.get_text(
        session=session,
        key="cabinet",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id,
        balance=db_user.balance,
        refcount=db_user.referral_count,
        currency=currency,
        solve=db_user.withdrawn,
        pubgid=pubg_id_text
    )

    markup = get_cabinet_inline_keyboard(db_user.pubg_id)
    await message.answer(text=cab_text, reply_markup=markup)


@cabinet_router.callback_query(F.data == "edit_pubg_id")
async def on_edit_pubg_id_prompt(
    callback: CallbackQuery,
    state: FSMContext,
    db_user: User
):
    current_pubg = f"\n\nJoriy PUBG ID: <code>{db_user.pubg_id}</code>" if db_user.pubg_id else ""
    await callback.message.delete()
    await callback.message.answer(
        f"🎮 <b>PUBG Mobile Akkaunt ID raqamingizni kiriting:</b>{current_pubg}\n\n<i>(Masalan: 5123456789)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(UserStates.waiting_for_pubg_id)


@cabinet_router.message(UserStates.waiting_for_pubg_id)
async def process_user_pubg_id(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    if message.text in ["Bekor qilish", "🚫 Bekor qilish", "◀️ Orqaga"]:
        await state.clear()
        is_admin = settings.is_admin(db_user.id)
        menu_kb = await get_main_menu(session, is_admin=is_admin)
        await message.answer("Bosh menyudasiz.", reply_markup=menu_kb)
        return

    pubg_id = message.text.strip()
    if not pubg_id.isdigit() or len(pubg_id) < 5 or len(pubg_id) > 20:
        await message.answer(
            "⚠️ PUBG ID raqami faqat raqamlardan iborat bo'lishi kerak (masalan: <code>5123456789</code>)!\n\nQayta urinib ko'ring yoki 'Bekor qilish' tugmasini bosing:"
        )
        return

    await crud.update_user_pubg_id(session, db_user.id, pubg_id)
    await state.clear()

    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await message.answer(
        f"✅ <b>PUBG ID raqamingiz muvaffaqiyatli saqlandi:</b> <code>{pubg_id}</code>",
        reply_markup=menu_kb
    )
