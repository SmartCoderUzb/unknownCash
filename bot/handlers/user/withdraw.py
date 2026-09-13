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
from bot.keyboards.reply import get_main_menu, get_back_keyboard, get_amount_keyboard
from bot.keyboards.inline import (
    get_payment_systems_keyboard,
    get_withdrawal_confirm_keyboard,
    get_admin_withdrawal_request_keyboard
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
    """To'lov tizimlarini ko'rsatish va yechish jarayonini boshlash."""
    can_proceed = await check_user_access(target, session, state, bot, db_user)
    if not can_proceed:
        return

    payment_systems = await crud.get_active_payment_systems(session)
    if not payment_systems:
        msg_text = "<b>To'lov tizimlari topilmadi!</b>"
        if isinstance(target, CallbackQuery):
            await target.answer("To'lov tizimlari topilmadi!", show_alert=True)
        else:
            await target.answer(msg_text)
        return

    select_text = await TextService.get_text(
        session=session,
        key="selectPayType",
        first=db_user.first_name,
        last=db_user.last_name,
        user_id=db_user.id
    )
    markup = get_payment_systems_keyboard(payment_systems)

    if isinstance(target, CallbackQuery):
        await target.message.delete()
        await target.message.answer(text=select_text, reply_markup=markup)
    else:
        await target.answer(text=select_text, reply_markup=markup)


@withdraw_router.message(F.text.in_(["💰Ucni yechish", "Ucni yechish"]))
async def on_withdraw_message(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await start_withdrawal_flow(message, session, state, bot, db_user)


@withdraw_router.callback_query(F.data == "yechish")
async def on_withdraw_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    await start_withdrawal_flow(callback, session, state, bot, db_user)


@withdraw_router.callback_query(F.data.startswith("pay-"))
async def on_select_payment_system(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    wallet_name = callback.data.split("pay-", 1)[1]
    all_settings = await crud.get_all_settings(session)
    vazifa = all_settings.get("vazifa", "Kiritilmagan")
    narx = float(all_settings.get("narx", "210"))
    currency = all_settings.get("valyuta", "uc")

    # 1. To'lovlar kanali tekshiruvi
    if vazifa == "Kiritilmagan" or not vazifa:
        no_channel_text = await TextService.get_text(session, "noChannel")
        await callback.answer(no_channel_text, show_alert=True)
        return

    # 2. Minimal yechish miqdori tekshiruvi
    if float(db_user.balance) < narx:
        min_text = await TextService.get_text(
            session=session,
            key="minimum",
            balance=db_user.balance,
            minimum=narx,
            currency=currency
        )
        # HTML teglardan tozalash alert uchun
        plain_min_text = min_text.replace("<b>", "").replace("</b>", "").replace("<pre>", "").replace("</pre>", "")
        await callback.answer(plain_min_text, show_alert=True)
        return

    # 3. Hamyon raqamini so'rash
    await callback.message.delete()
    send_card_text = await TextService.get_text(
        session=session,
        key="sendCard",
        first=db_user.first_name,
        last=db_user.last_name,
        user_id=db_user.id
    )
    back_kb = await get_back_keyboard(session)
    await callback.message.answer(text=send_card_text, reply_markup=back_kb)

    await state.set_state(UserStates.waiting_for_wallet)
    await state.update_data(wallet_name=wallet_name)


@withdraw_router.message(UserStates.waiting_for_wallet)
async def on_wallet_entered(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    db_user: User
):
    wallet_number = message.text.strip()
    data = await state.get_data()
    wallet_name = data.get("wallet_name")

    await state.update_data(wallet_number=wallet_number)
    await state.set_state(UserStates.waiting_for_amount)

    solve_money_text = await TextService.get_text(
        session=session,
        key="solveMoney",
        first=db_user.first_name,
        last=db_user.last_name,
        user_id=db_user.id
    )
    back_btn = await TextService.get_button(session, "back")
    amount_kb = get_amount_keyboard(balance=db_user.balance, back_text=back_btn)
    await message.answer(text=solve_money_text, reply_markup=amount_kb)


@withdraw_router.message(UserStates.waiting_for_amount)
async def on_amount_entered(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    db_user: User
):
    val_text = message.text.strip().replace(",", ".")
    try:
        amount = float(val_text)
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
        return

    all_settings = await crud.get_all_settings(session)
    narx = float(all_settings.get("narx", "210"))
    currency = all_settings.get("valyuta", "uc")

    # Minimal miqdor tekshiruvi
    if amount < narx:
        solve_min_text = await TextService.get_text(
            session=session,
            key="solveMinimum",
            minimum=narx,
            currency=currency
        )
        await message.answer(text=solve_min_text)
        return

    # Balans yetarliligi tekshiruvi
    if amount > float(db_user.balance):
        low_bal_text = await TextService.get_text(session, "lowBalance")
        await message.answer(text=low_bal_text)
        return

    data = await state.get_data()
    wallet_name = data.get("wallet_name")
    wallet_number = data.get("wallet_number")

    accepted_text = await TextService.get_text(
        session=session,
        key="accpeted",
        first=message.from_user.first_name,
        last=message.from_user.last_name,
        user_id=db_user.id,
        wallet=wallet_name,
        amount=amount,
        phone=wallet_number
    )

    confirm_btn = await TextService.get_button(session, "confirm")
    cancel_btn = await TextService.get_button(session, "cancellation")
    markup = get_withdrawal_confirm_keyboard(
        confirm_text=confirm_btn,
        cancel_text=cancel_btn,
        wallet=wallet_name,
        number=wallet_number,
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
    canceled_text = await TextService.get_text(session, "canceled")
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await callback.message.answer(text=canceled_text, reply_markup=menu_kb)


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
    wallet_number = parts[2]
    amount = float(parts[3])

    # Balansni qayta tekshiramiz
    user = await crud.get_user(session, db_user.id)
    if not user or float(user.balance) < amount:
        await callback.answer("Hisobingizda yetarli mablag' mavjud emas!", show_alert=True)
        return

    # Arizani bazaga saqlaymiz va balansni yechamiz
    withdrawal = await crud.create_withdrawal(
        session=session,
        user_id=db_user.id,
        payment_system=wallet_name,
        wallet_number=wallet_number,
        amount=amount
    )

    await callback.message.delete()
    accped_text = await TextService.get_text(session, "accped")
    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)
    await callback.message.answer(text=accped_text, reply_markup=menu_kb)

    # Adminga xabar yuborish
    admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
    if admin_target:
        username_part = f"@{db_user.username}" if db_user.username else str(db_user.id)
        admin_text = (
            f"💸 <a href='https://t.me/{db_user.username or ''}'>{db_user.id}</a> <b>uc yechib olmoqchi!</b>\n\n"
            f"• <b>To'lov turi:</b> {wallet_name}\n"
            f"• <b>Uc miqdori:</b> {amount}\n"
            f"• <b>Hamyon raqami:</b> {wallet_number}\n\n"
            f"Foydalanuvchi ucini to'lab bermoqchi bo'lsangiz ✅ <b>To'landi</b> tugmasini bosing!"
        )
        user_display = db_user.first_name or str(db_user.id)
        admin_markup = get_admin_withdrawal_request_keyboard(
            user_id=db_user.id,
            user_display=user_display,
            number=wallet_number,
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
