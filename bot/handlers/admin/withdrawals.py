import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.services.text_manager import TextService
from bot.keyboards.inline import get_paid_channel_keyboard, get_user_paid_receipt_keyboard

logger = logging.getLogger("AdminWithdrawals")
withdrawals_admin_router = Router()


@withdrawals_admin_router.callback_query(F.data.startswith("tolandi_") | F.data.startswith("tolandi-"))
async def on_withdrawal_paid(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    # ID ni ajratib olish
    if callback.data.startswith("tolandi_"):
        withdrawal_id = int(callback.data.split("tolandi_")[1])
    else:
        parts = callback.data.split("-")
        withdrawal_id = int(parts[1])

    withdrawal = await crud.get_withdrawal(session, withdrawal_id)
    if not withdrawal:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    if withdrawal.status != "pending":
        await callback.answer("Ushbu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    user = await crud.get_user(session, withdrawal.user_id)
    user_name = (user.first_name if user else None) or str(withdrawal.user_id)
    amount = withdrawal.amount
    wallet_number = withdrawal.pubg_id or withdrawal.wallet_number

    # 1. Admin xabaridagi tugmalarni olib tashlash
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    admin_confirm_text = (
        f"<a href='tg://user?id={withdrawal.user_id}'>{user_name}</a> "
        f"<b>foydalanuvchining #{withdrawal.id} sonli {amount} UC yechish arizasi tasdiqlandi va to'landi! ✅</b>"
    )
    await callback.message.answer(text=admin_confirm_text)

    # 2. To'lovlar (Isbot) kanaliga post joylash
    all_settings = await crud.get_all_settings(session)
    vazifa = all_settings.get("vazifa", "Kiritilmagan")
    bot_info = await bot.get_me()

    channel_msg_id = None
    clean_chan = vazifa.lstrip("@") if vazifa else None

    if vazifa and vazifa != "Kiritilmagan":
        been_paid_text = await TextService.get_text(
            session=session,
            key="BeenPaid",
            first=user_name,
            user_id=withdrawal.user_id,
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

    # 3. Bazada statusni paid deb belgilash
    await crud.mark_withdrawal_paid(session, withdrawal.id, channel_msg_id)

    # 4. Foydalanuvchiga bildirishnoma yuborish
    has_been_paid_text = await TextService.get_text(
        session=session,
        key="hasBeenPaid",
        first=user_name,
        user_id=withdrawal.user_id
    )
    user_markup = None
    if channel_msg_id and clean_chan:
        channel_post_url = f"https://t.me/{clean_chan}/{channel_msg_id}"
        user_markup = get_user_paid_receipt_keyboard(channel_post_url)

    try:
        await bot.send_message(
            chat_id=withdrawal.user_id,
            text=has_been_paid_text,
            reply_markup=user_markup
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga to'lov xabarini yuborishda ogohlantirish: {e}")


@withdrawals_admin_router.callback_query(F.data.startswith("tolanmadi_") | F.data.startswith("tolanmadi-"))
async def on_withdrawal_rejected(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    if callback.data.startswith("tolanmadi_"):
        withdrawal_id = int(callback.data.split("tolanmadi_")[1])
    else:
        parts = callback.data.split("-")
        withdrawal_id = int(parts[1])

    withdrawal = await crud.get_withdrawal(session, withdrawal_id)
    if not withdrawal:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    if withdrawal.status != "pending":
        await callback.answer("Ushbu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    # Bazada statusni rejected qilish va mablag'ni foydalanuvchiga qaytarish
    await crud.mark_withdrawal_rejected(session, withdrawal_id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    user = await crud.get_user(session, withdrawal.user_id)
    user_name = (user.first_name if user else None) or str(withdrawal.user_id)

    admin_msg = (
        f"<a href='tg://user?id={withdrawal.user_id}'>{user_name}</a> "
        f"<b>foydalanuvchining #{withdrawal.id} sonli arizasi rad etildi va {withdrawal.amount} UC balansi qaytarildi. ❌</b>"
    )
    await callback.message.answer(text=admin_msg)

    # Foydalanuvchiga xabar
    was_not_paid_text = await TextService.get_text(
        session=session,
        key="wasNotPaid",
        first=user_name,
        user_id=withdrawal.user_id
    )
    try:
        await bot.send_message(
            chat_id=withdrawal.user_id,
            text=was_not_paid_text
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad etish xabarini yuborishda ogohlantirish: {e}")


@withdrawals_admin_router.callback_query(F.data.startswith("block_user_") | F.data.startswith("block-"))
async def on_withdrawal_block(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    if callback.data.startswith("block_user_"):
        user_id = int(callback.data.split("block_user_")[1])
    else:
        parts = callback.data.split("-")
        user_id = int(parts[1])

    if settings.is_admin(user_id):
        await callback.answer("Adminni bloklash mumkin emas!", show_alert=True)
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchini bloklash
    await crud.set_user_ban(session, user_id, True)

    user = await crud.get_user(session, user_id)
    user_name = (user.first_name if user else None) or str(user_id)

    admin_msg = (
        f"<a href='tg://user?id={user_id}'>{user_name}</a> "
        f"<b>foydalanuvchi botdan bloklandi. ⛔</b>"
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
