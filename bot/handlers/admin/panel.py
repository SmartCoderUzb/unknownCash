import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.keyboards.reply import get_admin_panel_menu
from bot.keyboards.inline import get_close_keyboard

panel_router = Router()


@panel_router.message(Command(commands=["panel", "admin"]))
@panel_router.message(F.text.in_(["🗄 Boshqarish", "/panel", "/admin"]))
async def on_admin_panel_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if not settings.is_admin(message.from_user.id):
        return

    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)


@panel_router.callback_query(F.data == "yopish")
async def on_close_callback(callback: CallbackQuery):
    await callback.message.delete()


@panel_router.message(F.text == "📊 Statistika")
async def on_statistics_command(
    message: Message,
    session: AsyncSession
):
    if not settings.is_admin(message.from_user.id):
        return

    total_users = await crud.get_users_count(session)
    try:
        load = round(os.getloadavg()[0], 2)
    except Exception:
        load = "0.0"

    stat_text = (
        f"<b>💡 O'rtacha yuklanish:</b> <code>{load}</code>\n\n"
        f"👥 <b>Foydalanuvchilar: {total_users} ta</b>"
    )
    await message.answer(text=stat_text, reply_markup=get_close_keyboard())
