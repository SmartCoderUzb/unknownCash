from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.text_manager import TextService


async def get_main_menu(session: AsyncSession, is_admin: bool = False) -> ReplyKeyboardMarkup:
    earn = await TextService.get_button(session, "earn")
    cabinet = await TextService.get_button(session, "cabinet")
    solve = await TextService.get_button(session, "solve")
    tolov = await TextService.get_button(session, "tolov")
    support = await TextService.get_button(session, "support")
    manual = await TextService.get_button(session, "manual")

    keyboard = [
        [KeyboardButton(text=earn)],
        [KeyboardButton(text=cabinet), KeyboardButton(text=solve)],
        [KeyboardButton(text=tolov)],
        [KeyboardButton(text=support), KeyboardButton(text=manual)],
    ]
    if is_admin:
        keyboard.append([KeyboardButton(text="🗄 Boshqarish")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def get_admin_panel_menu(session: AsyncSession) -> ReplyKeyboardMarkup:
    back = await TextService.get_button(session, "back")
    keyboard = [
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="💳 To'lov tizimi")],
        [KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="✉️ Xabar yuborish")],
        [KeyboardButton(text="🔎 Foydalanuvchini boshqarish"), KeyboardButton(text="🎨 Dizayn")],
        [KeyboardButton(text="⚙️ Asosiy sozlamalar"), KeyboardButton(text=back)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def get_back_keyboard(session: AsyncSession) -> ReplyKeyboardMarkup:
    back = await TextService.get_button(session, "back")
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=back)]], resize_keyboard=True)


def get_boshqarish_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🗄 Boshqarish")]], resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Bekor qilish")]], resize_keyboard=True)


def get_contact_keyboard(btn_text: str = "☎️ Kontaktni yuborish") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn_text, request_contact=True)]],
        resize_keyboard=True
    )


def get_amount_keyboard(balance: float | str, back_text: str = "◀️ Orqaga") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=str(balance))],
            [KeyboardButton(text=back_text)]
        ],
        resize_keyboard=True
    )
