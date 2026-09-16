import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_admin_panel_menu, get_cancel_keyboard
from bot.keyboards.inline import get_admin_tariffs_keyboard

logger = logging.getLogger("AdminTariffs")
tariffs_admin_router = Router()


@tariffs_admin_router.message(F.text.in_(["💎 UC Tariflari", "UC Tariflari", "/tariffs"]))
async def on_tariffs_management(message: Message, session: AsyncSession):
    if not settings.is_admin(message.from_user.id):
        return

    tariffs = await crud.get_all_tariffs(session)
    markup = get_admin_tariffs_keyboard(tariffs)
    text = (
        "💎 <b>UC Sotib Olish Tariflarini Boshqarish:</b>\n\n"
        "Quyidagi ro'yxatdan o'chirmoqchi bo'lgan tarifingiz ustiga bosing yoki yangi tarif qo'shing:"
    )
    await message.answer(text=text, reply_markup=markup)


@tariffs_admin_router.callback_query(F.data == "add_new_tariff")
async def on_prompt_add_tariff(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "💎 <b>Tarifdagi UC miqdorini kiriting:</b>\n<i>(Masalan: 60 yoki 120)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_tariff_uc)


@tariffs_admin_router.message(AdminStates.waiting_for_tariff_uc)
async def process_tariff_uc(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if message.text in ["Bekor qilish", "🚫 Bekor qilish", "🗄 Boshqarish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("Boshqaruv panelidasiz.", reply_markup=panel_kb)
        return

    val = message.text.strip()
    if not val.isdigit() or int(val) <= 0:
        await message.answer("⚠️ Iltimos, faqat musbat butun son kiriting (masalan: 60):")
        return

    await state.update_data(new_tariff_uc=int(val))
    await message.answer(
        f"💰 <b>{val} UC uchun narxni kiriting (so'mda):</b>\n<i>(Masalan: 11000)</i>",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_tariff_price)


@tariffs_admin_router.message(AdminStates.waiting_for_tariff_price)
async def process_tariff_price(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if message.text in ["Bekor qilish", "🚫 Bekor qilish", "🗄 Boshqarish"]:
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("Boshqaruv panelidasiz.", reply_markup=panel_kb)
        return

    val = message.text.strip().replace(" ", "").replace(",", "")
    if not val.isdigit() or int(val) <= 0:
        await message.answer("⚠️ Iltimos, narxni faqat raqamda kiriting (masalan: 11000):")
        return

    data = await state.get_data()
    uc_amount = data.get("new_tariff_uc", 0)
    price_uzs = int(val)

    await crud.add_tariff(session, uc_amount=uc_amount, price_uzs=price_uzs)
    await state.clear()

    panel_kb = await get_admin_panel_menu(session)
    await message.answer(
        f"✅ <b>Yangi tarif muvaffaqiyatli qo'shildi!</b>\n\n💎 {uc_amount} UC — {price_uzs:,} so'm",
        reply_markup=panel_kb
    )


@tariffs_admin_router.callback_query(F.data.startswith("del_tariff_"))
async def on_delete_tariff(callback: CallbackQuery, session: AsyncSession):
    tariff_id = int(callback.data.split("del_tariff_")[1])
    await crud.delete_tariff(session, tariff_id)
    await callback.answer("Tarif muvaffaqiyatli o'chirildi!", show_alert=True)

    tariffs = await crud.get_all_tariffs(session)
    markup = get_admin_tariffs_keyboard(tariffs)
    text = (
        "💎 <b>UC Sotib Olish Tariflarini Boshqarish:</b>\n\n"
        "Tarif o'chirildi. Yangi tarif qo'shishingiz yoki mavjudlarini boshqarishingiz mumkin:"
    )
    await callback.message.edit_text(text=text, reply_markup=markup)
