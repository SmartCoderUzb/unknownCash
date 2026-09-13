from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu
from bot.keyboards.inline import get_user_manage_keyboard

users_router = Router()


@users_router.message(F.text == "🔎 Foydalanuvchini boshqarish")
async def on_manage_user_prompt(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        return

    await message.answer(
        "<b>Kerakli foydalanuvchining ID raqamini kiriting:</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_user_id)


@users_router.message(AdminStates.waiting_for_user_id)
async def process_user_id(
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
        await message.answer("⚠️ Iltimos, faqat foydalanuvchi ID raqamini kiriting:")
        return

    target_id = int(val)
    target_user = await crud.get_user(session, target_id)
    if not target_user:
        await message.answer("<b>Foydalanuvchi topilmadi.</b>\n\nQayta urinib ko'ring:")
        return

    await state.clear()
    valyuta = await crud.get_setting(session, "valyuta", "uc")

    text = (
        f"<b>Foydalanuvchi topildi!\n\n"
        f"ID:</b> <a href='tg://user?id={target_user.id}'>{target_user.id}</a>\n"
        f"<b>Balans:</b> {target_user.balance} {valyuta}\n"
        f"<b>Takliflar:</b> {target_user.referral_count} ta"
    )
    markup = get_user_manage_keyboard(target_user.id, target_user.is_banned)
    await message.answer(text=text, reply_markup=markup)


@users_router.callback_query(F.data.startswith("toggle_ban-"))
async def on_toggle_ban(
    callback: CallbackQuery,
    session: AsyncSession
):
    target_id = int(callback.data.split("-")[1])
    if settings.is_admin(target_id):
        await callback.answer("Asosiy adminlarni blocklash mumkin emas!", show_alert=True)
        return

    target_user = await crud.get_user(session, target_id)
    if not target_user:
        await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return

    new_ban_state = not target_user.is_banned
    await crud.set_user_ban(session, target_id, new_ban_state)

    msg = f"Foydalanuvchi ({target_id}) bandan olindi!" if not new_ban_state else f"Foydalanuvchi ({target_id}) banlandi!"
    await callback.answer(msg, show_alert=True)

    valyuta = await crud.get_setting(session, "valyuta", "uc")
    text = (
        f"<b>Foydalanuvchi topildi!\n\n"
        f"ID:</b> <a href='tg://user?id={target_user.id}'>{target_user.id}</a>\n"
        f"<b>Balans:</b> {target_user.balance} {valyuta}\n"
        f"<b>Takliflar:</b> {target_user.referral_count} ta"
    )
    markup = get_user_manage_keyboard(target_user.id, new_ban_state)
    try:
        await callback.message.edit_text(text=text, reply_markup=markup)
    except Exception:
        pass


@users_router.callback_query(F.data.startswith("plus-"))
async def on_plus_amount_prompt(
    callback: CallbackQuery,
    state: FSMContext
):
    target_id = int(callback.data.split("-")[1])
    await callback.message.delete()
    await callback.message.answer(
        f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobiga qancha uc qo'shmoqchisiz?</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_plus_amount)
    await state.update_data(target_id=target_id)


@users_router.message(AdminStates.waiting_for_plus_amount)
async def process_plus_amount(
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

    val = message.text.strip().replace(",", ".")
    try:
        amount = float(val)
    except ValueError:
        await message.answer("⚠️ Faqat raqamlardan foydalaning!")
        return

    data = await state.get_data()
    target_id = data.get("target_id")
    valyuta = await crud.get_setting(session, "valyuta", "uc")

    await crud.update_user_balance(session, target_id, amount)

    # Foydalanuvchiga xabar
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"<b>Adminlar tomonidan hisobingiz {amount} {valyuta} to'ldirildi</b>"
        )
    except Exception:
        pass

    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer(
        f"<b>Foydalanuvchi hisobiga {amount} {valyuta} qo'shildi!</b>",
        reply_markup=panel_kb
    )


@users_router.callback_query(F.data.startswith("minus-"))
async def on_minus_amount_prompt(
    callback: CallbackQuery,
    state: FSMContext
):
    target_id = int(callback.data.split("-")[1])
    await callback.message.delete()
    await callback.message.answer(
        f"<a href='tg://user?id={target_id}'>{target_id}</a> <b>ning hisobidan qancha uc ayirmoqchisiz?</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_minus_amount)
    await state.update_data(target_id=target_id)


@users_router.message(AdminStates.waiting_for_minus_amount)
async def process_minus_amount(
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

    val = message.text.strip().replace(",", ".")
    try:
        amount = float(val)
    except ValueError:
        await message.answer("⚠️ Faqat raqamlardan foydalaning!")
        return

    data = await state.get_data()
    target_id = data.get("target_id")
    valyuta = await crud.get_setting(session, "valyuta", "uc")

    await crud.update_user_balance(session, target_id, -amount)

    # Foydalanuvchiga xabar
    try:
        await bot.send_message(
            chat_id=target_id,
            text=f"<b>Adminlar tomonidan hisobingizdan {amount} {valyuta} olib tashlandi</b>"
        )
    except Exception:
        pass

    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer(
        f"<b>Foydalanuvchi hisobidan {amount} {valyuta} olib tashlandi!</b>",
        reply_markup=panel_kb
    )
