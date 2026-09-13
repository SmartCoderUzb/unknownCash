from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu
from bot.keyboards.inline import get_admin_settings_keyboard, get_earn_photo_settings_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

settings_router = Router()


@settings_router.message(F.text == "⚙ Asosiy sozlamalar")
async def on_general_settings(message: Message):
    if not settings.is_admin(message.from_user.id):
        return

    markup = get_admin_settings_keyboard()
    await message.answer("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


@settings_router.callback_query(F.data == "asosiy")
async def on_back_to_settings(callback: CallbackQuery):
    markup = get_admin_settings_keyboard()
    await callback.message.edit_text("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


@settings_router.callback_query(F.data == "holat")
async def on_current_status(callback: CallbackQuery, session: AsyncSession):
    all_s = await crud.get_all_settings(session)
    valyuta = all_s.get("valyuta", "uc")
    taklif = all_s.get("taklif", "5")
    narx = all_s.get("narx", "210")
    admin_user = all_s.get("admin_user", "Kiritilmagan")
    earn_photo = all_s.get("earn_photo", "https://t.me/BOT_UCHUN_RASMLAR/12")

    text = (
        f"<b>Hozirgi holat:\n\n"
        f"1. Valyuta:</b> {valyuta}\n"
        f"<b>2. Taklif narxi:</b> {taklif} {valyuta}\n"
        f"<b>3. Uc yechish narxi:</b> {narx} {valyuta}\n"
        f"<b>4. Admin useri:</b> {admin_user}\n"
        f"<b>5. Taklif rasmi:</b> {earn_photo}"
    )
    back_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="asosiy")]
        ]
    )
    await callback.message.edit_text(text=text, reply_markup=back_markup)


@settings_router.callback_query(F.data == "taklif")
async def on_change_taklif(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Taklif narxini yuboring:</b>", reply_markup=get_boshqarish_keyboard())
    await state.set_state(AdminStates.waiting_for_taklif_price)


@settings_router.message(AdminStates.waiting_for_taklif_price)
async def process_taklif_price(message: Message, session: AsyncSession, state: FSMContext):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    val = message.text.strip().replace(",", ".")
    try:
        float(val)
        await crud.set_setting(session, "taklif", val)
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")


@settings_router.callback_query(F.data == "valyuta")
async def on_change_valyuta(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Uc birligini yuboring:</b>", reply_markup=get_boshqarish_keyboard())
    await state.set_state(AdminStates.waiting_for_currency_name)


@settings_router.message(AdminStates.waiting_for_currency_name)
async def process_valyuta(message: Message, session: AsyncSession, state: FSMContext):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    val = message.text.strip()
    await crud.set_setting(session, "valyuta", val)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>Muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)


@settings_router.callback_query(F.data == "narx")
async def on_change_narx(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Minimal uc yechish narxini yuboring:</b>", reply_markup=get_boshqarish_keyboard())
    await state.set_state(AdminStates.waiting_for_min_withdrawal)


@settings_router.message(AdminStates.waiting_for_min_withdrawal)
async def process_narx(message: Message, session: AsyncSession, state: FSMContext):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    val = message.text.strip().replace(",", ".")
    try:
        float(val)
        await crud.set_setting(session, "narx", val)
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)
    except ValueError:
        await message.answer("⚠️ Iltimos, faqat raqam kiriting!")


@settings_router.callback_query(F.data == "admin_user_setting")
async def on_change_admin_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("<b>Admin userini yuboring:</b>", reply_markup=get_boshqarish_keyboard())
    await state.set_state(AdminStates.waiting_for_admin_user)


@settings_router.message(AdminStates.waiting_for_admin_user)
async def process_admin_user(message: Message, session: AsyncSession, state: FSMContext):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    val = message.text.strip()
    await crud.set_setting(session, "admin_user", val)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>Muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)


@settings_router.callback_query(F.data == "taklif_rasm")
async def on_earn_photo_setting(callback: CallbackQuery, session: AsyncSession):
    earn_photo = await crud.get_setting(session, "earn_photo", "https://t.me/BOT_UCHUN_RASMLAR/12")
    markup = get_earn_photo_settings_keyboard()
    text = (
        f"<b>🖼 Taklif rasmi sozlamasi</b>\n\n"
        f"<b>Hozirgi rasm / havola:</b>\n<code>{earn_photo}</code>\n\n"
        f"Yangi rasm o'rnatish uchun quyidagi tugmani bosing."
    )
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=markup)


@settings_router.callback_query(F.data == "set_earn_photo")
async def on_set_earn_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Yangi taklif rasmini yuboring:</b>\n\n"
        "<i>Rasm yuborishingiz yoki to'g'ridan-to'g'ri rasm havolasini (URL) yuborishingiz mumkin.</i>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_earn_photo)


@settings_router.message(AdminStates.waiting_for_earn_photo)
async def process_earn_photo(message: Message, session: AsyncSession, state: FSMContext):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    photo_val = None
    if message.photo:
        photo_val = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        photo_val = message.document.file_id
    elif message.text:
        photo_val = message.text.strip()

    if not photo_val:
        await message.answer("⚠️ Iltimos, rasm yoki rasm havolasini yuboring!")
        return

    await crud.set_setting(session, "earn_photo", photo_val)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>Taklif rasmi muvaffaqiyatli o'zgartirildi!</b>", reply_markup=panel_kb)


@settings_router.callback_query(F.data == "reset_earn_photo")
async def on_reset_earn_photo(callback: CallbackQuery, session: AsyncSession):
    default_photo = "https://t.me/BOT_UCHUN_RASMLAR/12"
    await crud.set_setting(session, "earn_photo", default_photo)
    await callback.answer("Rasm standart holatga qaytarildi!", show_alert=True)
    markup = get_earn_photo_settings_keyboard()
    text = (
        f"<b>🖼 Taklif rasmi sozlamasi</b>\n\n"
        f"<b>Hozirgi rasm / havola:</b>\n<code>{default_photo}</code>\n\n"
        f"Yangi rasm o'rnatish uchun quyidagi tugmani bosing."
    )
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        pass

