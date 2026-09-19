import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core.config import settings
from bot.database import crud
from bot.keyboards.reply import get_admin_panel_menu
from bot.keyboards.inline import get_close_keyboard

panel_router = Router()


@panel_router.message(Command(commands=["panel", "admin"]))
@panel_router.message(F.text.in_(["🗄 Boshqarish", "/panel", "/admin"]))
async def on_admin_panel_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot
):
    if not settings.is_admin(message.from_user.id):
        return

    await state.clear()
    panel_kb = await get_admin_panel_menu(session)
    bot_info = await bot.get_me()
    await message.answer(f"<b>{bot_info.first_name} | Admin Panel 🔽 Kerakli buyruqni tanlang:</b>", reply_markup=panel_kb)


@panel_router.callback_query(F.data == "yopish")
async def on_close_callback(callback: CallbackQuery):
    await callback.message.delete()


@panel_router.message(F.text == "📊 Statistika")
async def on_statistics_command(
    message: Message,
    session: AsyncSession
):
    if not settings.is_admin(message.from_user.id):
        return

    total_users = await crud.get_users_count(session)
    pending_orders = await crud.get_pending_orders_count(session)
    pending_withdrawals = await crud.get_pending_withdrawals_count(session)
    tariffs = await crud.get_active_tariffs(session)
    channels = await crud.get_mandatory_channels(session)
    settings_data = await crud.get_all_settings(session)
    currency = settings_data.get("valyuta", "UC")

    try:
        load = round(os.getloadavg()[0], 2)
    except Exception:
        load = "0.0"

    stat_text = (
        f"📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {total_users} ta\n"
        f"🛒 <b>Kutilayotgan UC xaridlar:</b> {pending_orders} ta\n"
        f"💸 <b>Kutilayotgan UC yechishlar:</b> {pending_withdrawals} ta\n"
        f"💎 <b>Faol UC tariflari:</b> {len(tariffs)} ta\n"
        f"📢 <b>Majburiy kanallar:</b> {len(channels)} ta\n"
        f"💶 <b>Asosiy valyuta:</b> {currency}\n\n"
        f"💡 <b>Server yuklanishi (Load Avg):</b> <code>{load}</code>"
    )
    await message.answer(text=stat_text, reply_markup=get_close_keyboard())


# ================= ADMINLARNI BOSHQARISH (KINO BOT ANDOZASI) =================

from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def _get_config_admins(cfg) -> list[int]:
    result = set()
    for attr in ["all_admin_ids", "admin_list", "get_all_admin_ids", "SUPER_ADMINS", "ADMINS", "ADMIN_ID", "admin_id"]:
        if hasattr(cfg, attr):
            try:
                val = getattr(cfg, attr)
                if callable(val):
                    val = val()
                if isinstance(val, (list, set, tuple)):
                    for x in val:
                        if str(x).isdigit() and int(x) > 0:
                            result.add(int(x))
                elif isinstance(val, int) and val > 0:
                    result.add(val)
                elif isinstance(val, str):
                    for part in val.replace(";", ",").split(","):
                        if part.strip().isdigit() and int(part.strip()) > 0:
                            result.add(int(part.strip()))
            except Exception:
                pass
    return sorted(list(result))

def _is_config_admin(cfg, user_id: int) -> bool:
    if hasattr(cfg, "is_admin"):
        try:
            if cfg.is_admin(user_id):
                return True
        except Exception:
            pass
    return user_id in _get_config_admins(cfg)

def _get_admins_list_kb(db_admins: list[int], config_admins: list[int], back_callback: str = "adm_close") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Yangi admin qo'shish", callback_data="admin:add_new")]
    ]
    for adm_id in db_admins:
        if adm_id not in config_admins:
            buttons.append([InlineKeyboardButton(text=f"🗑 {adm_id}ni o'chirish", callback_data=f"admin:remove:{adm_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from bot.states.admin_states import AdminManageAdmin

@panel_router.message(StateFilter("*"), F.text.in_(["👮 Adminlar", "👮‍♂️ Adminlar", "Adminlar", "adminlar"]))
@panel_router.callback_query(F.data == "admin:admins")
async def cb_admin_admins(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext = None):
    user_id = event.from_user.id
    is_adm = _is_config_admin(settings, user_id)
    if not is_adm:
        db_adms = await crud.get_admins(session)
        is_adm = user_id in db_adms
    if not is_adm:
        if isinstance(event, CallbackQuery):
            await event.answer("❌ Ruxsat berilmagan!", show_alert=True)
        return

    if state:
        await state.clear()

    db_admins = await crud.get_admins(session)
    config_admins = _get_config_admins(settings)
    all_admin_ids = list(set(config_admins + db_admins))

    lines = ["👮‍♂️ <b>Bot Adminlari ro'yxati:</b>", ""]
    for a_id in all_admin_ids:
        role_label = " (Bosh admin)" if a_id in config_admins else ""
        lines.append(f"• <code>{a_id}</code>{role_label}")
    text = "\n".join(lines)

    kb = _get_admins_list_kb(db_admins, config_admins, back_callback="yopish")
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@panel_router.callback_query(F.data == "admin:add_new")
async def cb_add_admin_start(call: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = call.from_user.id
    is_adm = _is_config_admin(settings, user_id) or (user_id in await crud.get_admins(session))
    if not is_adm:
        return await call.answer("❌ Ruxsat berilmagan!", show_alert=True)

    await state.set_state(AdminManageAdmin.waiting_for_user_id)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin:admins")]
    ])
    try:
        await call.message.edit_text(
            "👮‍♂️ Yangi adminning <b>Telegram ID</b>sini kiriting:",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
    except Exception:
        await call.message.answer(
            "👮‍♂️ Yangi adminning <b>Telegram ID</b>sini kiriting:",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )
    await call.answer()


@panel_router.message(AdminManageAdmin.waiting_for_user_id)
async def process_add_admin(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id
    is_adm = _is_config_admin(settings, user_id) or (user_id in await crud.get_admins(session))
    if not is_adm:
        await state.clear()
        return

    text = message.text.strip() if message.text else ""
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin:admins")]
    ])

    if not text.isdigit():
        return await message.answer(
            "❌ Faqat sonlardan iborat Telegram ID kiriting:",
            reply_markup=cancel_kb,
            parse_mode="HTML"
        )

    new_admin_id = int(text)
    await crud.add_admin(session, new_admin_id)
    await state.clear()

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Adminlar ro'yxatiga qaytish", callback_data="admin:admins")]
    ])
    await message.answer(
        f"✅ <code>{new_admin_id}</code> IDli foydalanuvchi muvaffaqiyatli admin etib tayinlandi!",
        reply_markup=back_kb,
        parse_mode="HTML"
    )


@panel_router.callback_query(F.data.startswith("admin:remove:"))
async def cb_remove_admin(call: CallbackQuery, session: AsyncSession):
    user_id = call.from_user.id
    if not _is_config_admin(settings, user_id):
        return await call.answer("⚠️ Faqat asosiy admin boshqa adminlarni o'chira oladi!", show_alert=True)

    rem_id = int(call.data.split(":")[-1])
    await crud.remove_admin(session, rem_id)
    await call.answer(f"🗑 {rem_id} adminlikdan olib tashlandi!", show_alert=True)
    await cb_admin_admins(call, session)
