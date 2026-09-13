import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.services.text_manager import TextService
from bot.keyboards.inline import get_paid_channel_keyboard, get_user_paid_receipt_keyboard

logger = logging.getLogger("AdminWithdrawals")
withdrawals_admin_router = Router()


@withdrawals_admin_router.callback_query(F.data.startswith("tolandi-"))
async def on_withdrawal_paid(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    parts = callback.data.split("-")
    if len(parts) < 5:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    user_id = int(parts[1])
    user_name = parts[2]
    wallet_number = parts[3]
    amount = float(parts[4])

    all_settings = await crud.get_all_settings(session)
    vazifa = all_settings.get("vazifa", "Kiritilmagan")
    bot_info = await bot.get_me()

    # 1. Admin xabarini yangilash
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    admin_confirm_text = (
        f"<a href='tg://user?id={user_id}'>{user_name}</a> "
        f"<b>uclarini yechib olish haqidagi arizasi qabul qilindi.</b>"
    )
    await callback.message.answer(text=admin_confirm_text)

    # 2. To'lovlar kanaliga post joylash
    channel_msg_id = None
    clean_chan = vazifa.lstrip("@")

    if vazifa and vazifa != "Kiritilmagan":
        been_paid_text = await TextService.get_text(
            session=session,
            key="BeenPaid",
            first=user_name,
            user_id=user_id,
            amount=amount,
            phone=wallet_number,
            botname=bot_info.username
        )
        transition_btn = await TextService.get_button(session, "transition")
        chan_markup = get_paid_channel_keyboard(transition_btn, bot_info.username)

        try:
            sent_channel_msg = await bot.send_message(
                chat_id=vazifa,
                text=been_paid_text,
                reply_markup=chan_markup,
                disable_web_page_preview=True
            )
            channel_msg_id = sent_channel_msg.message_id
        except Exception as e:
            logger.error(f"To'lovlar kanaliga post yuborishda xatolik: {e}")

    # 3. Foydalanuvchiga bildirishnoma yuborish
    has_been_paid_text = await TextService.get_text(
        session=session,
        key="hasBeenPaid",
        first=user_name,
        user_id=user_id
    )
    user_markup = None
    if channel_msg_id and clean_chan:
        channel_post_url = f"https://t.me/{clean_chan}/{channel_msg_id}"
        user_markup = get_user_paid_receipt_keyboard(channel_post_url)

    try:
        await bot.send_message(
            chat_id=user_id,
            text=has_been_paid_text,
            reply_markup=user_markup
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga to'lov xabarini yuborishda ogohlantirish: {e}")


@withdrawals_admin_router.callback_query(F.data.startswith("tolanmadi-"))
async def on_withdrawal_rejected(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    parts = callback.data.split("-")
    if len(parts) < 4:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    user_id = int(parts[1])
    user_name = parts[2]
    amount = float(parts[3])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Balansni foydalanuvchiga qaytarish
    await crud.update_user_balance(session, user_id, amount)

    admin_msg = (
        f"<a href='tg://user?id={user_id}'>{user_name}</a> "
        f"<b>uclarini yechib olish haqidagi arizasi qabul qilinmadi.</b>"
    )
    await callback.message.answer(text=admin_msg)

    # Foydalanuvchiga xabar
    was_not_paid_text = await TextService.get_text(
        session=session,
        key="wasNotPaid",
        first=user_name,
        user_id=user_id
    )
    try:
        await bot.send_message(
            chat_id=user_id,
            text=was_not_paid_text
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad etish xabarini yuborishda ogohlantirish: {e}")


@withdrawals_admin_router.callback_query(F.data.startswith("block-"))
async def on_withdrawal_block(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    parts = callback.data.split("-")
    if len(parts) < 3:
        await callback.answer("Noto'g'ri so'rov!", show_alert=True)
        return

    user_id = int(parts[1])
    user_name = parts[2]

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchini bloklash
    await crud.set_user_ban(session, user_id, True)

    admin_msg = (
        f"<a href='tg://user?id={user_id}'>{user_name}</a> "
        f"<b>uclarini yechib olish haqidagi arizasi qabul qilinmadi va botdan blocklandi.</b>"
    )
    await callback.message.answer(text=admin_msg)

    # Foydalanuvchiga blok xabari
    block_text = await TextService.get_text(
        session=session,
        key="block",
        first=user_name,
        user_id=user_id
    )
    try:
        await bot.send_message(
            chat_id=user_id,
            text=block_text,
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga blok xabarini yuborishda ogohlantirish: {e}")
