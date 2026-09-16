import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.database.models import UcOrder
from bot.keyboards.inline import get_paid_channel_keyboard, get_user_paid_receipt_keyboard

logger = logging.getLogger("AdminOrders")
orders_admin_router = Router()


@orders_admin_router.callback_query(F.data.startswith("order_approve_"))
async def on_order_approved(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(callback.data.split("order_approve_")[1])
    order = await crud.mark_order_approved(session, order_id)
    if not order:
        await callback.answer("Buyurtma allaqachon ko'rib chiqilgan yoki topilmadi!", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    user = await crud.get_user(session, order.user_id)
    user_name = user.first_name if user else "Foydalanuvchi"

    await callback.message.answer(
        f"✅ <b>#{order.id} raqamli {order.uc_amount} UC xarid arizasi tasdiqlandi!</b>"
    )

    all_settings = await crud.get_all_settings(session)
    vazifa = all_settings.get("vazifa", "Kiritilmagan")
    bot_info = await bot.get_me()

    channel_msg_id = None
    clean_chan = vazifa.lstrip("@") if vazifa else None

    # Isbot kanaliga post chiqarish
    if vazifa and vazifa != "Kiritilmagan":
        proof_text = (
            f"✅ <b>Yangi UC xaridi amalga oshirildi!</b>\n\n"
            f"👤 <b>Mijoz:</b> <a href='tg://user?id={order.user_id}'>{user_name}</a>\n"
            f"🎮 <b>PUBG ID:</b> <code>{order.pubg_id}</code>\n"
            f"💎 <b>Paket:</b> <b>{order.uc_amount} UC</b>\n"
            f"💰 <b>Narxi:</b> <b>{order.price_uzs:,} so'm</b>\n\n"
            f"🤖 <b>Rasmiy botimiz:</b> @{bot_info.username}"
        )
        chan_markup = get_paid_channel_keyboard("🤖 Botga o'tish", bot_info.username)
        try:
            sent_msg = await bot.send_message(
                chat_id=vazifa,
                text=proof_text,
                reply_markup=chan_markup,
                disable_web_page_preview=True
            )
            channel_msg_id = sent_msg.message_id
        except Exception as e:
            logger.error(f"Isbot kanalga buyurtma postini yuborishda xatolik: {e}")

    # Foydalanuvchiga bildirishnoma
    user_text = (
        f"🎉 <b>Tabriklaymiz, hurmatli {user_name}!</b>\n\n"
        f"Sizning <b>#{order.id}</b> raqamli arizangiz tasdiqlandi!\n"
        f"💎 <b>{order.uc_amount} UC</b> PUBG hisobingizga (ID: <code>{order.pubg_id}</code>) muvaffaqiyatli yuklandi!\n\n"
        f"<i>Xaridingiz uchun tashakkur!</i>"
    )
    user_markup = None
    if channel_msg_id and clean_chan:
        receipt_url = f"https://t.me/{clean_chan}/{channel_msg_id}"
        user_markup = get_user_paid_receipt_keyboard(receipt_url)

    try:
        await bot.send_message(
            chat_id=order.user_id,
            text=user_text,
            reply_markup=user_markup
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga buyurtma tasdiq xabarini yuborishda xatolik: {e}")


@orders_admin_router.callback_query(F.data.startswith("order_reject_"))
async def on_order_rejected(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    order_id = int(callback.data.split("order_reject_")[1])
    order = await crud.mark_order_rejected(session, order_id)
    if not order:
        await callback.answer("Buyurtma allaqachon ko'rib chiqilgan yoki topilmadi!", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    user = await crud.get_user(session, order.user_id)
    user_name = user.first_name if user else "Foydalanuvchi"

    await callback.message.answer(
        f"❌ <b>#{order.id} raqamli {order.uc_amount} UC xarid arizasi rad etildi.</b>"
    )

    # Foydalanuvchiga xabar
    user_text = (
        f"❌ <b>Hurmatli {user_name}!</b>\n\n"
        f"Sizning <b>#{order.id}</b> raqamli {order.uc_amount} UC xarid arizangiz rad etildi.\n"
        f"To'lov cheki topilmadi yoki to'lov tasdiqlanmadi.\n\n"
        f"Agar to'lovni amalga oshirgan bo'lsangiz, adminga murojaat qiling."
    )
    try:
        await bot.send_message(chat_id=order.user_id, text=user_text)
    except Exception as e:
        logger.warning(f"Foydalanuvchiga rad xabari yuborishda ogohlantirish: {e}")


@orders_admin_router.callback_query(F.data.startswith("block_user_"))
async def on_order_block_user(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot
):
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    user_id = int(callback.data.split("block_user_")[1])
    if settings.is_admin(user_id):
        await callback.answer("Adminni bloklash mumkin emas!", show_alert=True)
        return

    await crud.set_user_ban(session, user_id, True)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer(f"🔔 <b>Foydalanuvchi ({user_id}) muvaffaqiyatli bloklandi.</b>")
    try:
        await bot.send_message(
            chat_id=user_id,
            text="⛔ <b>Qoidalarni buzganligingiz sababli botdan bloklandingiz.</b>",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception:
        pass
