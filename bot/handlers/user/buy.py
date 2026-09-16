import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.database.models import User
from bot.states.user_states import UserStates
from bot.services.text_manager import TextService
from bot.keyboards.reply import get_main_menu, get_cancel_keyboard
from bot.keyboards.inline import (
    get_buy_withdraw_choice_keyboard,
    get_tariffs_keyboard,
    get_use_saved_pubg_id_keyboard,
    get_buy_confirm_keyboard,
    get_admin_order_request_keyboard
)
from bot.handlers.user.start import check_user_access

logger = logging.getLogger("UserBuy")
buy_router = Router()


@buy_router.message(F.text.in_(["💎 UC sotib olish / Yechish", "UC sotib olish / Yechish", "🛒 UC sotib olish", "UC sotib olish", "/buy"]))
async def on_buy_withdraw_menu(
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

    text = (
        "💎 <b>UC xizmatlari bo'limi:</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:\n"
        "• <b>🛒 UC sotib olish:</b> Hamyonbop narxlardagi rasmiy UC paketlari\n"
        "• <b>💰 UC yechib olish:</b> Botda to'plagan balansingizni PUBG ID raqamingizga yechish"
    )
    await message.answer(text=text, reply_markup=get_buy_withdraw_choice_keyboard())


@buy_router.callback_query(F.data == "back_to_buy_withdraw")
async def on_back_to_buy_withdraw(callback: CallbackQuery):
    text = (
        "💎 <b>UC xizmatlari bo'limi:</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:"
    )
    await callback.message.edit_text(text=text, reply_markup=get_buy_withdraw_choice_keyboard())


@buy_router.callback_query(F.data == "action_buy_uc")
async def on_start_buy_uc(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await state.clear()
    can_proceed = await check_user_access(callback, session, state, bot, db_user)
    if not can_proceed:
        return

    tariffs = await crud.get_active_tariffs(session)
    if not tariffs:
        await callback.answer("Hozirda sotuvda mavjud tariflar yo'q!", show_alert=True)
        return

    text = (
        "🛒 <b>UC Sotib Olish:</b>\n\n"
        "Quyidagi tariflardan birini tanlang:"
    )
    markup = get_tariffs_keyboard(tariffs)
    await callback.message.edit_text(text=text, reply_markup=markup)


@buy_router.callback_query(F.data.startswith("buy_tariff_"))
async def on_tariff_selected(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    db_user: User
):
    tariff_id = int(callback.data.split("buy_tariff_")[1])
    tariff = await crud.get_tariff(session, tariff_id)
    if not tariff:
        await callback.answer("Tarif topilmadi!", show_alert=True)
        return

    await state.update_data(tariff_id=tariff.id, uc_amount=tariff.uc_amount, price_uzs=tariff.price_uzs)

    # Foydalanuvchida saqlangan PUBG ID bormi?
    if db_user.pubg_id:
        text = (
            f"💎 <b>Tanlangan paket:</b> {tariff.uc_amount} UC\n"
            f"💰 <b>Narxi:</b> {tariff.price_uzs:,} so'm\n\n"
            f"Sizda saqlangan PUBG ID: <code>{db_user.pubg_id}</code>\n"
            f"Ushbu hisobga yuklansinmi?"
        )
        await callback.message.edit_text(text=text, reply_markup=get_use_saved_pubg_id_keyboard(db_user.pubg_id))
    else:
        await callback.message.delete()
        text = (
            f"💎 <b>Tanlangan paket:</b> {tariff.uc_amount} UC ({tariff.price_uzs:,} so'm)\n\n"
            f"🎮 <b>PUBG Mobile Akkaunt ID raqamingizni kiriting:</b>\n<i>(Masalan: 5123456789)</i>"
        )
        await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
        await state.set_state(UserStates.buy_waiting_for_pubg_id)


@buy_router.callback_query(F.data.startswith("use_saved_pubg_"))
async def on_use_saved_pubg(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    pubg_id = callback.data.split("use_saved_pubg_")[1]
    await state.update_data(pubg_id=pubg_id)
    data = await state.get_data()
    tariff_id = data.get("tariff_id")
    uc_amount = data.get("uc_amount")
    price_uzs = data.get("price_uzs")

    card_details = await crud.get_setting(
        session,
        "card_details",
        "Karta raqami: 8600 0000 0000 0000\nQabul qiluvchi: Admin"
    )

    text = (
        f"💳 <b>To'lov ma'lumotlari:</b>\n\n"
        f"💎 <b>Paket:</b> {uc_amount} UC\n"
        f"💰 <b>To'lov summasi:</b> <b>{price_uzs:,} so'm</b>\n"
        f"🎮 <b>PUBG ID:</b> <code>{pubg_id}</code>\n\n"
        f"📌 <b>Rekvizitlar:</b>\n{card_details}\n\n"
        f"⚠️ <i>To'lovni amalga oshirgach, to'lov chekini (skrinshot yoki kvitansiya rasmini) botga yuboring:</i>"
    )
    await callback.message.delete()
    await callback.message.answer(text=text, reply_markup=get_cancel_keyboard())
    await state.set_state(UserStates.buy_waiting_for_receipt)


@buy_router.callback_query(F.data == "enter_new_pubg_id")
async def on_prompt_new_pubg_id(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🎮 <b>PUBG Mobile Akkaunt ID raqamingizni kiriting:</b>\n<i>(Masalan: 5123456789)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(UserStates.buy_waiting_for_pubg_id)


@buy_router.message(UserStates.buy_waiting_for_pubg_id)
async def process_buy_pubg_id(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
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
        await message.answer("⚠️ Iltimos, to'g'ri PUBG ID raqamini kiriting (faqat raqamlar):")
        return

    # User profiliga ham saqlab qo'yamiz
    await crud.update_user_pubg_id(session, db_user.id, pubg_id)
    await state.update_data(pubg_id=pubg_id)

    data = await state.get_data()
    uc_amount = data.get("uc_amount")
    price_uzs = data.get("price_uzs")

    card_details = await crud.get_setting(
        session,
        "card_details",
        "Karta raqami: 8600 0000 0000 0000\nQabul qiluvchi: Admin"
    )

    text = (
        f"💳 <b>To'lov ma'lumotlari:</b>\n\n"
        f"💎 <b>Paket:</b> {uc_amount} UC\n"
        f"💰 <b>To'lov summasi:</b> <b>{price_uzs:,} so'm</b>\n"
        f"🎮 <b>PUBG ID:</b> <code>{pubg_id}</code>\n\n"
        f"📌 <b>Rekvizitlar:</b>\n{card_details}\n\n"
        f"⚠️ <i>To'lovni amalga oshirgach, to'lov chekini (skrinshot yoki kvitansiya rasmini) botga yuboring:</i>"
    )
    await message.answer(text=text, reply_markup=get_cancel_keyboard())
    await state.set_state(UserStates.buy_waiting_for_receipt)


@buy_router.message(UserStates.buy_waiting_for_receipt)
async def process_buy_receipt(
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
        await message.answer("Operatsiya bekor qilindi.", reply_markup=menu_kb)
        return

    receipt_file_id = None
    if message.photo:
        receipt_file_id = message.photo[-1].file_id
    elif message.document:
        receipt_file_id = message.document.file_id
    elif message.text:
        receipt_file_id = message.text.strip()

    if not receipt_file_id:
        await message.answer("⚠️ Iltimos, to'lov chekini rasm yoki fayl ko'rinishida yuboring!")
        return

    data = await state.get_data()
    uc_amount = data.get("uc_amount", 0)
    price_uzs = data.get("price_uzs", 0)
    pubg_id = data.get("pubg_id", db_user.pubg_id or "Kiritilmagan")

    # Buyurtmani bazaga yozamiz
    order = await crud.create_order(
        session=session,
        user_id=db_user.id,
        uc_amount=uc_amount,
        price_uzs=price_uzs,
        pubg_id=pubg_id,
        receipt_file_id=str(receipt_file_id)
    )

    await state.clear()
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)

    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        f"• <b>Buyurtma raqami:</b> #{order.id}\n"
        f"• <b>Paket:</b> {uc_amount} UC\n"
        f"• <b>PUBG ID:</b> <code>{pubg_id}</code>\n\n"
        "Arizangiz adminga yuborildi. Tez orada tekshirilib, akkauntingizga UC yuklanadi!",
        reply_markup=menu_kb
    )

    # Adminga jo'natish
    admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
    if admin_target:
        username_part = f"@{db_user.username}" if db_user.username else f"<a href='tg://user?id={db_user.id}'>{db_user.first_name}</a>"
        admin_caption = (
            f"🛒 <b>Yangi UC sotib olish arizasi! [#{order.id}]</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {username_part}\n"
            f"🆔 <b>Telegram ID:</b> <code>{db_user.id}</code>\n"
            f"🎮 <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
            f"💎 <b>Paket:</b> {uc_amount} UC\n"
            f"💰 <b>Narxi:</b> {price_uzs:,} so'm\n\n"
            f"To'lovni tekshirib, qaror qabul qiling:"
        )
        admin_markup = get_admin_order_request_keyboard(order.id, db_user.id)

        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=admin_target,
                    photo=message.photo[-1].file_id,
                    caption=admin_caption,
                    reply_markup=admin_markup
                )
            elif message.document:
                await bot.send_document(
                    chat_id=admin_target,
                    document=message.document.file_id,
                    caption=admin_caption,
                    reply_markup=admin_markup
                )
            else:
                await bot.send_message(
                    chat_id=admin_target,
                    text=f"{admin_caption}\n\n<b>To'lov matni/kodi:</b>\n{receipt_file_id}",
                    reply_markup=admin_markup
                )
        except Exception as e:
            logger.error(f"Adminga buyurtma yuborishda xatolik: {e}")
