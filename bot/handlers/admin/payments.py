from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.states.admin_states import AdminStates
from bot.keyboards.reply import get_boshqarish_keyboard, get_admin_panel_menu
from bot.keyboards.inline import get_payment_systems_admin_keyboard

payments_router = Router()


@payments_router.message(F.text == "💳 To'lov tizimi")
async def on_payment_systems_menu(message: Message, session: AsyncSession):
    if not settings.is_admin(message.from_user.id):
        return

    payment_systems = await crud.get_active_payment_systems(session)
    markup = get_payment_systems_admin_keyboard(payment_systems)
    await message.answer("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


@payments_router.callback_query(F.data == "hamyon")
async def on_back_to_payments(callback: CallbackQuery, session: AsyncSession):
    payment_systems = await crud.get_active_payment_systems(session)
    markup = get_payment_systems_admin_keyboard(payment_systems)
    await callback.message.edit_text("<b>Quyidagilardan birini tanlang:</b>", reply_markup=markup)


@payments_router.callback_query(F.data.startswith("del-"))
async def on_delete_payment_system(callback: CallbackQuery, session: AsyncSession):
    name = callback.data.split("del-", 1)[1]
    await crud.delete_payment_system(session, name)

    payment_systems = await crud.get_active_payment_systems(session)
    markup = get_payment_systems_admin_keyboard(payment_systems)
    await callback.answer(f"{name} to'lov tizimi o'chirildi!", show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=markup)
    except Exception:
        pass


@payments_router.callback_query(F.data == "new_payment")
async def on_add_payment_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Yangi to'lov tizimi nomini yuboring:</b>",
        reply_markup=get_boshqarish_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_payment_system_name)


@payments_router.message(AdminStates.waiting_for_payment_system_name)
async def process_new_payment_system(
    message: Message,
    session: AsyncSession,
    state: FSMContext
):
    if message.text == "🗄 Boshqarish":
        await state.clear()
        panel_kb = await get_admin_panel_menu(session)
        await message.answer("<b>Boshqaruv panelidasiz.</b>", reply_markup=panel_kb)
        return

    name = message.text.strip()
    await crud.add_payment_system(session, name)
    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    await message.answer("<b>Yangi to'lov tizimi qo'shildi!</b>", reply_markup=panel_kb)
