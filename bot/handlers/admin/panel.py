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
    state: FSMContext,
    bot: Bot
):
    if not settings.is_admin(message.from_user.id):
        return

    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    bot_info = await bot.get_me()
    await message.answer(f"<b>{bot_info.first_name} | Admin Panel 🔽 Kerakli buyruqni tanlang:</b>", reply_markup=panel_kb)


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
    pending_orders = await crud.get_pending_orders_count(session)
    pending_withdrawals = await crud.get_pending_withdrawals_count(session)
    tariffs = await crud.get_active_tariffs(session)
    channels = await crud.get_mandatory_channels(session)
    settings_data = await crud.get_all_settings(session)
    currency = settings_data.get("valyuta", "UC")

    try:
        load = round(os.getloadavg()[0], 2)
    except Exception:
        load = "0.0"

    stat_text = (
        f"📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {total_users} ta\n"
        f"🛒 <b>Kutilayotgan UC xaridlar:</b> {pending_orders} ta\n"
        f"💸 <b>Kutilayotgan UC yechishlar:</b> {pending_withdrawals} ta\n"
        f"💎 <b>Faol UC tariflari:</b> {len(tariffs)} ta\n"
        f"📢 <b>Majburiy kanallar:</b> {len(channels)} ta\n"
        f"💶 <b>Asosiy valyuta:</b> {currency}\n\n"
        f"💡 <b>Server yuklanishi (Load Avg):</b> <code>{load}</code>"
    )
    await message.answer(text=stat_text, reply_markup=get_close_keyboard())
