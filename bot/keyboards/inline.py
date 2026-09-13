from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_continue_keyboard(continue_text: str = "✅ Davom etish") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=continue_text, callback_data="davom")]
        ]
    )


def get_share_keyboard(share_text: str, bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=share_text,
                url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start={user_id}"
            )]
        ]
    )


def get_cabinet_keyboard(solve_text: str = "💰Ucni yechish") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=solve_text, callback_data="yechish")]
        ]
    )


def get_payment_systems_keyboard(payment_systems: list) -> InlineKeyboardMarkup:
    buttons = []
    for ps in payment_systems:
        name = ps.name if hasattr(ps, "name") else str(ps)
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"pay-{name}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_withdrawal_confirm_keyboard(
    confirm_text: str,
    cancel_text: str,
    wallet: str,
    number: str,
    amount: float
) -> InlineKeyboardMarkup:
    # Saqlash callback ma'lumotlari
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_text, callback_data=f"tasdiq-{wallet}-{number}-{amount}")],
            [InlineKeyboardButton(text=cancel_text, callback_data="bekor")]
        ]
    )


def get_admin_withdrawal_request_keyboard(
    user_id: int,
    user_display: str,
    number: str,
    amount: float
) -> InlineKeyboardMarkup:
    clean_display = user_display.replace("-", "_")[:20]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Banlash", callback_data=f"block-{user_id}-{clean_display}")],
            [
                InlineKeyboardButton(text="✅ To'landi", callback_data=f"tolandi-{user_id}-{clean_display}-{number}-{amount}"),
                InlineKeyboardButton(text="❌ To'lanmadi", callback_data=f"tolanmadi-{user_id}-{clean_display}-{amount}")
            ]
        ]
    )


def get_paid_channel_keyboard(transition_text: str, bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=transition_text, url=f"https://t.me/{bot_username}")]
        ]
    )


def get_user_paid_receipt_keyboard(channel_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 To'lovlar kanali", url=channel_url)]
        ]
    )


def get_close_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Yopish", callback_data="yopish")]
        ]
    )


def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📑 Hozirgi holat", callback_data="holat")],
            [
                InlineKeyboardButton(text="👥️️ Taklif narxi", callback_data="taklif"),
                InlineKeyboardButton(text="💶 Valyuta", callback_data="valyuta")
            ],
            [InlineKeyboardButton(text="💸Minimal uc yechish narxi", callback_data="narx")],
            [
                InlineKeyboardButton(text="📎 Admin useri", callback_data="admin_user_setting"),
                InlineKeyboardButton(text="Yopish", callback_data="yopish")
            ]
        ]
    )


def get_admin_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Majburiy obunalar", callback_data="majburiy")],
            [InlineKeyboardButton(text="*⃣ Qo'shimcha kanallar", callback_data="qoshimcha")],
            [InlineKeyboardButton(text="Yopish", callback_data="yopish")]
        ]
    )


def get_mandatory_channels_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Qo'shish", callback_data="qoshish")],
            [
                InlineKeyboardButton(text="📑 Ro'yxat", callback_data="royxat"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data="ochirish")
            ],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="kanallar")]
        ]
    )


def get_additional_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕️ To'lovlar uchun", callback_data="vazifa")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="kanallar")]
        ]
    )


def get_payment_systems_admin_keyboard(payment_systems: list) -> InlineKeyboardMarkup:
    rows = []
    for ps in payment_systems:
        name = ps.name if hasattr(ps, "name") else str(ps)
        rows.append([InlineKeyboardButton(text=f"{name} - ni o'chirish", callback_data=f"del-{name}")])
    rows.append([InlineKeyboardButton(text="➕ To'lov tizimi qo'shish", callback_data="new_payment")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_broadcast_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Oddiy xabar", callback_data="broadcast_simple"),
                InlineKeyboardButton(text="Forward xabar", callback_data="broadcast_forward")
            ],
            [InlineKeyboardButton(text="Foydalanuvchiga xabar", callback_data="broadcast_direct")]
        ]
    )


def get_user_manage_keyboard(target_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_label = "🔕 Bandan olish" if is_banned else "🔔 Banlash"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ban_label, callback_data=f"toggle_ban-{target_id}")],
            [
                InlineKeyboardButton(text="➕ Uc qo'shish", callback_data=f"plus-{target_id}"),
                InlineKeyboardButton(text="➖ Uc ayirish", callback_data=f"minus-{target_id}")
            ]
        ]
    )
