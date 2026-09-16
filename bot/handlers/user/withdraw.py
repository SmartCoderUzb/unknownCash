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
from bot.keyboards.reply import get_main_menu, get_back_keyboard, get_amount_keyboard, get_cancel_keyboard
from bot.keyboards.inline import (
    get_withdrawal_confirm_keyboard,
    get_admin_withdrawal_request_keyboard,
    get_use_saved_pubg_id_keyboard
)
from bot.handlers.user.start import check_user_access

logger = logging.getLogger("UserWithdraw")
withdraw_router = Router()


async def start_withdrawal_flow(
    target: Message | CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    """UC yechish jarayonini boshlash."""
    await state.clear()
    can_proceed = await check_user_access(target, session, state, bot, db_user)
    if not can_proceed:
        return

    all_settings = await crud.get_all_settings(session)
    narx = float(all_settings.get("narx", "60"))
    currency = all_settings.get("valyuta", "UC")

    # Balans tekshiruvi
    if float(db_user.balance) < narx:
        min_text = (
            f"⛔ <b>Hisobingizda mablag' yetarli emas!</b>\n\n"
            f"• <b>Minimal yechib olish miqdori:</b> {narx} {currency}\n"
            f"• <b>Sizning balansingiz:</b> {db_user.balance} {currency}\n\n"
            f"<i>Do'stlaringizni taklif qilib yoki xarid qilib balansingizni to'ldirishingiz mumkin.</i>"
        )
        if isinstance(target, CallbackQuery):
            await target.answer(f"Minimal yechish: {narx} {currency}. Balansingiz: {db_user.balance} {currency}", show_alert=True)
        else:
            await target.answer(min_text)
        return

    # Foydalanuvchida saqlangan PUBG ID bormi?
    if db_user.pubg_id:
        text = (
            f"💰 <b>UC Yechib Olish:</b>\n\n"
            f"💎 <b>Mavjud balansingiz:</b> {db_user.balance} {currency}\n"
            f"🎮 <b>Saqlangan PUBG ID:</b> <code>{db_user.pubg_id}</code>\n\n"
            f"Ushbu PUBG ID ga yechib olmoqchimisiz?"
        )
        markup = get_use_saved_pubg_id_keyboard(db_user.pubg_id)
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text=text, reply_markup=markup)
        else:
            await target.answer(text=text, reply_markup=markup)
    else:
        text = (
            f"💰 <b>UC Yechib Olish:</b>\n\n"
            f"💎 <b>Mavjud balansingiz:</b> {db_user.balance} {currency}\n\n"
            f"🎮 <b>PUBG Mobile Akkaunt ID raqamingizni kiriting:</b>\n<i>(Masalan: 5123456789)</i>"
        )
        if isinstance(target, CallbackQuery):
            await target.message.delete()
            await target.message.answer(text=text, reply_markup=get_cancel_keyboard())
        else:
            await target.answer(text=text, reply_markup=get_cancel_keyboard())
        await state.set_state(UserStates.withdraw_waiting_for_pubg_id)


@withdraw_router.message(F.text.in_(["💰 UC yechib olish", "UC yechib olish", "💰Ucni yechish", "Ucni yechish", "UC yechish", "/withdraw"]))
async def on_withdraw_message(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await start_withdrawal_flow(message, session, state, bot, db_user)


@withdraw_router.callback_query(F.data == "action_withdraw_uc")
@withdraw_router.callback_query(F.data == "yechish")
async def on_withdraw_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await start_withdrawal_flow(callback, session, state, bot, db_user)


@withdraw_router.callback_query(F.data.startswith("use_saved_pubg_"))
async def on_use_saved_pubg_for_withdraw(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    db_user: User
):
    pubg_id = callback.data.split("use_saved_pubg_")[1]
    await state.update_data(pubg_id=pubg_id)
    await prompt_for_amount(callback.message, session, state, db_user, is_edit=True)


@withdraw_router.callback_query(F.data == "enter_new_pubg_id")
async def on_prompt_new_pubg_withdraw(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🎮 <b>PUBG Mobile Akkaunt ID raqamingizni kiriting:</b>\n<i>(Masalan: 5123456789)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(UserStates.withdraw_waiting_for_pubg_id)


@withdraw_router.message(UserStates.withdraw_waiting_for_pubg_id)
async def process_withdraw_pubg_id(
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

    await crud.update_user_pubg_id(session, db_user.id, pubg_id)
    await state.update_data(pubg_id=pubg_id)
    await prompt_for_amount(message, session, state, db_user, is_edit=False)


async def prompt_for_amount(
    target_msg: Message,
    session: AsyncSession,
    state: FSMContext,
    db_user: User,
    is_edit: bool = False
):
    all_settings = await crud.get_all_settings(session)
    narx = all_settings.get("narx", "60")
    currency = all_settings.get("valyuta", "UC")

    text = (
        f"💸 <b>Qancha miqdorda UC yechib olmoqchisiz?</b>\n\n"
        f"• <b>Mavjud balans:</b> {db_user.balance} {currency}\n"
        f"• <b>Minimal yechish:</b> {narx} {currency}\n\n"
        f"<i>Yechmoqchi bo'lgan miqdorni kiriting yoki pastdagi tugmani bosing:</i>"
    )
    back_btn = "◀️ Orqaga"
    amount_kb = get_amount_keyboard(balance=db_user.balance, back_text=back_btn)

    if is_edit:
        await target_msg.delete()
        await target_msg.answer(text=text, reply_markup=amount_kb)
    else:
        await target_msg.answer(text=text, reply_markup=amount_kb)

    await state.set_state(UserStates.withdraw_waiting_for_amount)


@withdraw_router.message(UserStates.withdraw_waiting_for_amount)
async def process_withdraw_amount(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    if message.text in ["◀️ Orqaga", "Orqaga", "Bekor qilish", "🚫 Bekor qilish"]:
        await state.clear()
        is_admin = settings.is_admin(db_user.id)
        menu_kb = await get_main_menu(session, is_admin=is_admin)
        await message.answer("Bosh menyudasiz.", reply_markup=menu_kb)
        return

    val_text = message.text.strip().replace(",", ".")
    try:
        amount = float(val_text)
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
        return

    all_settings = await crud.get_all_settings(session)
    narx = float(all_settings.get("narx", "60"))
    currency = all_settings.get("valyuta", "UC")

    if amount < narx:
        await message.answer(f"⚠️ Minimal yechib olish miqdori: <b>{narx} {currency}</b>\nQayta kiriting:")
        return

    if amount > float(db_user.balance):
        await message.answer(f"⚠️ Balansingizda yetarli mablag' mavjud emas! (Balans: {db_user.balance} {currency})\nQayta kiriting:")
        return

    data = await state.get_data()
    pubg_id = data.get("pubg_id", db_user.pubg_id or "Kiritilmagan")

    accepted_text = (
        f"✅ <b>Arizangiz tayyor!</b>\n\n"
        f"• <b>Operatsiya:</b> UC yechib olish\n"
        f"• <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
        f"• <b>Yechilayotgan miqdor:</b> <b>{amount} {currency}</b>\n\n"
        f"<i>Ma'lumotlar to'g'riligini tasdiqlaysizmi?</i>"
    )

    confirm_btn = await TextService.get_button(session, "confirm")
    cancel_btn = await TextService.get_button(session, "cancellation")
    markup = get_withdrawal_confirm_keyboard(
        confirm_text=confirm_btn,
        cancel_text=cancel_btn,
        wallet="PUBG Mobile",
        number=pubg_id,
        amount=amount
    )

    await state.clear()
    await message.answer(text=accepted_text, reply_markup=markup)


@withdraw_router.callback_query(F.data == "bekor")
async def on_withdrawal_cancel(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: User
):
    await callback.message.delete()
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await callback.message.answer(text="⛔ <b>Operatsiya bekor qilindi.</b>", reply_markup=menu_kb)


@withdraw_router.callback_query(F.data.startswith("tasdiq-"))
async def on_withdrawal_confirmed(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    db_user: User
):
    parts = callback.data.split("-")
    if len(parts) < 4:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    wallet_name = parts[1]
    pubg_id = parts[2]
    amount = float(parts[3])

    user = await crud.get_user(session, db_user.id)
    if not user or float(user.balance) < amount:
        await callback.answer("Hisobingizda yetarli mablag' mavjud emas!", show_alert=True)
        return

    withdrawal = await crud.create_withdrawal(
        session=session,
        user_id=db_user.id,
        payment_system=wallet_name,
        wallet_number=pubg_id,
        amount=amount,
        pubg_id=pubg_id
    )

    await callback.message.delete()
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)

    await callback.message.answer(
        "✅ <b>Arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"• <b>Ariza raqami:</b> #{withdrawal.id}\n"
        f"• <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
        f"• <b>Miqdor:</b> {amount} UC\n\n"
        "Tez orada adminlarimiz UC ni hisobingizga yuklab berishadi.",
        reply_markup=menu_kb
    )

    # Adminga yuborish
    admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
    if admin_target:
        username_part = f"@{db_user.username}" if db_user.username else f"<a href='tg://user?id={db_user.id}'>{db_user.first_name}</a>"
        admin_text = (
            f"💸 <b>Yangi UC yechib olish arizasi! [#{withdrawal.id}]</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {username_part}\n"
            f"🆔 <b>Telegram ID:</b> <code>{db_user.id}</code>\n"
            f"🎮 <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
            f"💎 <b>Yechiladigan UC:</b> {amount} UC\n"
            f"💳 <b>Mavjud qoldiq balans:</b> {user.balance} UC\n\n"
            f"To'lovni amalga oshirib, qaror qabul qiling:"
        )
        user_display = db_user.first_name or str(db_user.id)
        admin_markup = get_admin_withdrawal_request_keyboard(
            withdrawal_id=withdrawal.id,
            user_id=db_user.id,
            user_display=user_display,
            number=pubg_id,
            amount=amount
        )
        try:
            await bot.send_message(
                chat_id=admin_target,
                text=admin_text,
                reply_markup=admin_markup,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Adminga yechib olish so'rovini yuborishda xatolik: {e}")
