from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu, get_cancel_keyboard

texts_router = Router()


# ==============================================================================
# DIZAYN MENYUSI
# ==============================================================================

@texts_router.message(F.text == "🎨 Dizayn")
async def on_design_menu(message: Message):
    if not settings.is_admin(message.from_user.id):
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎛 Tugmalar", callback_data="design_buttons")],
            [InlineKeyboardButton(text="📃 Matnlar", callback_data="design_texts")],
            [InlineKeyboardButton(text="Yopish", callback_data="yopish")]
        ]
    )
    await message.answer("<b>🎨 Dizayn va matnlarni sozlash bo'limi:</b>\n\nQuyidagilardan birini tanlang:", reply_markup=markup)


@texts_router.callback_query(F.data == "design_buttons")
async def on_design_buttons_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    codes = ", ".join([f"<code>{k}</code>" for k in crud.DEFAULT_BUTTONS.keys()])
    await callback.message.answer(
        f"<b>Tugma kodini kiriting:</b>\n\n"
        f"Mavjud kodlar:\n{codes}",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_button_code)


@texts_router.callback_query(F.data == "design_texts")
async def on_design_texts_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    codes = ", ".join([f"<code>{k}</code>" for k in crud.DEFAULT_TEXTS.keys()])
    await callback.message.answer(
        f"<b>Matn kodini kiriting:</b>\n\n"
        f"Mavjud kodlar:\n{codes}",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_text_code)


# ==============================================================================
# TUGMALAR TAHRIRI
# ==============================================================================

@texts_router.message(F.text == "🎛 Tugmalar")
async def on_buttons_editor_prompt(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        return

    codes = ", ".join([f"<code>{k}</code>" for k in crud.DEFAULT_BUTTONS.keys()])
    await message.answer(
        f"<b>Tugma kodini kiriting:</b>\n\n"
        f"Mavjud kodlar:\n{codes}",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_button_code)


@texts_router.message(AdminStates.waiting_for_button_code)
async def process_button_code(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text in ["🗄 Boshqarish", "Bekor qilish", "bekor qilish", "🚫 Bekor qilish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    code = message.text.strip()
    if code not in crud.DEFAULT_BUTTONS:
        await message.answer("⚠️ <b>Mavjud bo'lmagan tugma kodini kiritdingiz!</b>\n\nQayta urinib ko'ring:")
        return

    await state.update_data(button_code=code)
    await state.set_state(AdminStates.waiting_for_button_value)
    current_val = await crud.get_text_or_button(session, code) or crud.DEFAULT_BUTTONS[code]
    await message.answer(
        f"<pre>{code}</pre> <b>qabul qilindi.</b>\n\n"
        f"Hozirgi qiymat: <b>{current_val}</b>\n\n"
        f"<i>Ushbu tugma uchun yangi qiymatni kiriting:</i>",
        reply_markup=get_cancel_keyboard()
    )


@texts_router.message(AdminStates.waiting_for_button_value)
async def process_button_value(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text in ["🗄 Boshqarish", "Bekor qilish", "bekor qilish", "🚫 Bekor qilish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    new_val = message.text.strip()
    data = await state.get_data()
    code = data.get("button_code")

    await crud.set_text_or_button(session, key=code, value=new_val, text_type="button")
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>O'zgartirish yakunlandi!</b>", reply_markup=panel_kb)


# ==============================================================================
# MATNLAR TAHRIRI
# ==============================================================================

@texts_router.message(F.text == "📃 Matnlar")
async def on_texts_editor_prompt(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        return

    codes = ", ".join([f"<code>{k}</code>" for k in crud.DEFAULT_TEXTS.keys()])
    await message.answer(
        f"<b>Matn kodini kiriting:</b>\n\n"
        f"Mavjud kodlar:\n{codes}",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_text_code)


@texts_router.message(AdminStates.waiting_for_text_code)
async def process_text_code(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text in ["🗄 Boshqarish", "Bekor qilish", "bekor qilish", "🚫 Bekor qilish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    code = message.text.strip()
    if code not in crud.DEFAULT_TEXTS:
        await message.answer("⚠️ <b>Mavjud bo'lmagan matn kodini kiritdingiz!</b>\n\nQayta urinib ko'ring:")
        return

    await state.update_data(text_code=code)
    await state.set_state(AdminStates.waiting_for_text_value)
    current_val = await crud.get_text_or_button(session, code) or crud.DEFAULT_TEXTS[code]
    await message.answer(
        f"<pre>{code}</pre> <b>qabul qilindi.</b>\n\n"
        f"Hozirgi qiymat:\n{current_val}\n\n"
        f"<i>Ushbu matn uchun yangi qiymatni kiriting:</i>",
        reply_markup=get_cancel_keyboard()
    )


@texts_router.message(AdminStates.waiting_for_text_value)
async def process_text_value(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text in ["🗄 Boshqarish", "Bekor qilish", "bekor qilish", "🚫 Bekor qilish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    new_val = message.text or message.html_text or ""
    data = await state.get_data()
    code = data.get("text_code")

    await crud.set_text_or_button(session, key=code, value=new_val, text_type="text")
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>O'zgartirish yakunlandi!</b>", reply_markup=panel_kb)
