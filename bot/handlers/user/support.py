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
from bot.keyboards.inline import get_support_inline_keyboard
from bot.handlers.user.start import check_user_access

logger = logging.getLogger("UserSupport")
support_router = Router()


@support_router.message(F.text.in_(["💬 Yordam", "Yordam", "💌 Yordam"]))
async def on_support_command(
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

    all_settings = await crud.get_all_settings(session)
    admin_user = all_settings.get("admin_user", "Kiritilmagan")
    proof_channel = all_settings.get("vazifa", "Kiritilmagan")

    text = (
        "💬 <b>Yordam va Qo'llab-quvvatlash markazi:</b>\n\n"
        "Savollaringiz, takliflaringiz yoki bot bo'yicha tushunmovchiliklar bo'lsa, "
        "quyidagi tugmalar orqali adminga to'g'ridan-to'g'ri yozishingiz yoki bot orqali murojaat yuborishingiz mumkin.\n\n"
        "Shuningdek, barcha to'lovlar va isbotlarni kanalimizda kuzatib borishingiz mumkin!"
    )
    markup = get_support_inline_keyboard(admin_user, proof_channel)
    await message.answer(text=text, reply_markup=markup, disable_web_page_preview=True)


@support_router.callback_query(F.data == "send_support_msg")
async def on_prompt_support_msg(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📝 <b>Murojaat yoki savolingizni yozib qoldiring:</b>\n<i>(Bekor qilish uchun pastdagi tugmani bosing)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(UserStates.waiting_for_support_message)


@support_router.message(UserStates.waiting_for_support_message)
async def on_support_message_received(
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
        await message.answer("Bosh menyudasiz.", reply_markup=menu_kb)
        return

    text_content = message.text or message.caption or "Fayl/Media"

    # Adminga yuborish
    admin_target = settings.ADMIN_ID or (settings.SUPER_ADMINS[0] if settings.SUPER_ADMINS else 0)
    if admin_target:
        username_link = f"@{message.from_user.username}" if message.from_user.username else f"<a href='tg://user?id={db_user.id}'>{db_user.first_name}</a>"
        admin_msg = (
            f"📩 <b>Yangi foydalanuvchi murojaati:</b>\n\n"
            f"👤 <b>Kimdan:</b> {username_link}\n"
            f"🆔 <b>ID:</b> <code>{db_user.id}</code>\n\n"
            f"💬 <b>Xabar:</b>\n{text_content}"
        )
        try:
            await bot.send_message(
                chat_id=admin_target,
                text=admin_msg,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"Adminga murojaatni uzatishda xatolik: {e}")

    is_admin = settings.is_admin(db_user.id)
    menu_kb = await get_main_menu(session, is_admin=is_admin)

    await state.clear()
    await message.answer(
        "✅ <b>Murojaatingiz adminga yuborildi!</b>\nTez orada ko'rib chiqiladi.",
        reply_markup=menu_kb
    )
