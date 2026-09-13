import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu
from bot.keyboards.inline import get_broadcast_type_keyboard

logger = logging.getLogger("AdminBroadcast")
broadcast_router = Router()


@broadcast_router.message(F.text == "💌 Xabarnoma")
async def on_broadcast_menu(message: Message):
    if not settings.is_admin(message.from_user.id):
        return
    markup = get_broadcast_type_keyboard()
    await message.answer("<b>Yuboriladigan xabar turini tanlang:</b>", reply_markup=markup)


# ==============================================================================
# ODDIY XABAR
# ==============================================================================

@broadcast_router.callback_query(F.data == "broadcast_simple")
async def on_simple_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_text)


@broadcast_router.message(AdminStates.waiting_for_broadcast_text)
async def process_simple_broadcast(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    user_ids = await crud.get_all_user_ids(session)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer(f"⏳ Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda...")

    sent_count = 0
    for uid in user_ids:
        try:
            await bot.copy_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            continue

    await message.answer(
        f"<b>Hammaga yuborildi ✅</b>\n\nJami: {sent_count}/{len(user_ids)} ta foydalanuvchiga yetkazildi.",
        reply_markup=panel_kb
    )


# ==============================================================================
# FORWARD XABAR
# ==============================================================================

@broadcast_router.callback_query(F.data == "broadcast_forward")
async def on_forward_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Barcha foydalanuvchilarga uzatiladigan (forward) xabarni yuboring:</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_forward)


@broadcast_router.message(AdminStates.waiting_for_broadcast_forward)
async def process_forward_broadcast(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    user_ids = await crud.get_all_user_ids(session)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer(f"⏳ Forward xabar {len(user_ids)} ta foydalanuvchiga uzatilmoqda...")

    sent_count = 0
    for uid in user_ids:
        try:
            await bot.forward_message(
                chat_id=uid,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            sent_count += 1
            await asyncio.sleep(0.04)
        except Exception:
            continue

    await message.answer(
        f"<b>Hammaga yuborildi ✅</b>\n\nJami: {sent_count}/{len(user_ids)} ta foydalanuvchiga yetkazildi.",
        reply_markup=panel_kb
    )


# ==============================================================================
# FOYDALANUVCHIGA TO'G'RIDAN-TO'G'RI XABAR
# ==============================================================================

@broadcast_router.callback_query(F.data == "broadcast_direct")
async def on_direct_message_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Foydalanuvchi ID raqamini kiriting:</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_direct_user_id)


@broadcast_router.message(AdminStates.waiting_for_direct_user_id)
async def process_direct_user_id(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    val = message.text.strip()
    if not val.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan foydalaning!")
        return

    target_id = int(val)
    target_user = await crud.get_user(session, target_id)
    if not target_user:
        await message.answer("⚠️ Foydalanuvchi topilmadi. Qayta urinib ko'ring:")
        return

    await state.update_data(direct_user_id=target_id)
    await state.set_state(AdminStates.waiting_for_direct_message)
    await message.answer("<b>Xabaringizni kiriting:</b>")


@broadcast_router.message(AdminStates.waiting_for_direct_message)
async def process_direct_message(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    data = await state.get_data()
    target_id = data.get("direct_user_id")

    try:
        await bot.copy_message(
            chat_id=target_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Xabaringiz yuborildi ✅</b>", reply_markup=panel_kb)
    except Exception as e:
        await message.answer(f"❌ Xabar yuborishda xatolik: {e}")
