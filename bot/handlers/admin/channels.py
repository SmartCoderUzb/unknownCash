from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu
from bot.keyboards.inline import (
    get_admin_channels_keyboard,
    get_mandatory_channels_management_keyboard,
    get_additional_channels_keyboard
)

channels_router = Router()


@channels_router.message(F.text == "📢 Kanallar")
async def on_channels_menu(message: Message):
    if not settings.is_admin(message.from_user.id):
        return
    markup = get_admin_channels_keyboard()
    await message.answer("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


@channels_router.callback_query(F.data == "kanallar")
async def on_back_to_channels(callback: CallbackQuery):
    markup = get_admin_channels_keyboard()
    await callback.message.edit_text("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


# ==============================================================================
# 1. MAJBURIIY OBUNALAR
# ==============================================================================

@channels_router.callback_query(F.data == "majburiy")
async def on_mandatory_channels_menu(callback: CallbackQuery):
    markup = get_mandatory_channels_management_keyboard()
    await callback.message.edit_text("<b>Majburiy obunalarni sozlash bo'limidasiz:</b>", reply_markup=markup)


@channels_router.callback_query(F.data == "qoshish")
async def on_add_channel_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Kanalingiz userini kiriting:\n\nNamuna:</b> @ORGBuilder",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_mandatory_channel)


@channels_router.message(AdminStates.waiting_for_mandatory_channel)
async def process_add_channel(
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

    text = message.text.strip()
    if not text.startswith("@"):
        text = f"@{text}"

    # Kanal sarlavhasini tekshirib olish
    title = None
    try:
        chat = await bot.get_chat(text)
        title = chat.title
    except Exception:
        pass

    success = await crud.add_mandatory_channel(session, username=text, title=title)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)

    if success:
        await message.answer(f"<b>{text} - kanal muvaffaqiyatli qo'shildi!</b>", reply_markup=panel_kb)
    else:
        await message.answer(f"⚠️ {text} kanali allaqachon mavjud!", reply_markup=panel_kb)


@channels_router.callback_query(F.data == "royxat")
async def on_list_channels(callback: CallbackQuery, session: AsyncSession):
    channels = await crud.get_mandatory_channels(session)
    back_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="majburiy")]]
    )
    if not channels:
        await callback.message.edit_text("📂 <b>Kanallar ro'yxati bo'sh!</b>", reply_markup=back_markup)
        return

    lines = [f"• {c.username} ({c.title or 'Sarlavhasiz'})" for c in channels]
    chan_text = "\n".join(lines)
    count = len(channels)

    res_text = (
        f"<b>📢 Kanallar ro'yxati:</b>\n\n"
        f"{chan_text}\n\n"
        f"<b>Ulangan kanallar soni:</b> {count} ta"
    )
    await callback.message.edit_text(text=res_text, reply_markup=back_markup)


@channels_router.callback_query(F.data == "ochirish")
async def on_delete_channels(callback: CallbackQuery, session: AsyncSession):
    await crud.delete_all_mandatory_channels(session)
    back_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Orqaga", callback_data="majburiy")]]
    )
    await callback.message.edit_text("<b>Kanallar o'chirildi.</b>", reply_markup=back_markup)


# ==============================================================================
# 2. QO'SHIMCHA KANALLAR (TO'LOVLAR KANALI)
# ==============================================================================

@channels_router.callback_query(F.data == "qoshimcha")
async def on_additional_channels_menu(callback: CallbackQuery, session: AsyncSession):
    vazifa = await crud.get_setting(session, "vazifa", "Kiritilmagan")
    text = (
        f"<b>Quyidagilardan birini tanlang:\n\n"
        f"Hozirgi holat:\n"
        f"To'lovlar uchun kanal:</b> {vazifa}"
    )
    markup = get_additional_channels_keyboard()
    await callback.message.edit_text(text=text, reply_markup=markup)


@channels_router.callback_query(F.data == "vazifa")
async def on_prompt_payment_channel(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Kanalingiz userini kiriting:</b>", reply_markup=get_boshqarish_keyboard())
    await state.set_state(AdminStates.waiting_for_payment_channel)


@channels_router.message(AdminStates.waiting_for_payment_channel)
async def process_payment_channel(
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

    text = message.text.strip()
    if not text.startswith("@"):
        text = f"@{text}"

    # Bot kanalda admin ekanligini tekshirish
    is_admin_in_channel = False
    try:
        admins = await bot.get_chat_administrators(chat_id=text)
        bot_info = await bot.get_me()
        is_admin_in_channel = any(adm.user.id == bot_info.id for adm in admins)
    except Exception:
        is_admin_in_channel = False

    if is_admin_in_channel:
        await crud.set_setting(session, "vazifa", text)
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)
    else:
        await message.answer(
            "<b>Bot ushbu kanalda admin emas yoki noto'g'ri kanal manzili yuborildi!</b>\n\n"
            "<i>Botni kanalga admin qilib, qayta urinib ko'ring:</i>"
        )
