from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.database.models import UcTariff, PaymentSystem


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


def get_cabinet_inline_keyboard(pubg_id: str | None = None) -> InlineKeyboardMarkup:
    pubg_btn_text = "✏️ PUBG ID o'zgartirish" if pubg_id else "➕ PUBG ID kiritish"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=pubg_btn_text, callback_data="edit_pubg_id")],
            [
                InlineKeyboardButton(text="🛒 UC sotib olish", callback_data="action_buy_uc"),
                InlineKeyboardButton(text="💰 UC yechish", callback_data="action_withdraw_uc")
            ]
        ]
    )


def get_buy_withdraw_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 UC sotib olish", callback_data="action_buy_uc"),
                InlineKeyboardButton(text="💰 UC yechib olish", callback_data="action_withdraw_uc")
            ]
        ]
    )


def get_tariffs_keyboard(tariffs: list[UcTariff]) -> InlineKeyboardMarkup:
    buttons = []
    for t in tariffs:
        text = f"💎 {t.uc_amount} UC — {t.price_uzs:,} so'm"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_tariff_{t.id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_buy_withdraw")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_use_saved_pubg_id_keyboard(saved_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ PUBG ID: {saved_id}", callback_data=f"use_saved_pubg_{saved_id}")],
            [InlineKeyboardButton(text="✏️ Boshqa PUBG ID kiritish", callback_data="enter_new_pubg_id")],
            [InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="bekor")]
        ]
    )


def get_buy_confirm_keyboard(tariff_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧾 To'lov qildim (Chek yuborish)", callback_data=f"send_receipt_{tariff_id}")],
            [InlineKeyboardButton(text="🚫 Bekor qilish", callback_data="bekor")]
        ]
    )


def get_admin_order_request_keyboard(order_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash (Isbot kanalga)", callback_data=f"order_approve_{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"order_reject_{order_id}")
            ],
            [InlineKeyboardButton(text="🔔 Foydalanuvchini banlash", callback_data=f"block_user_{user_id}")]
        ]
    )


def get_payment_systems_keyboard(payment_systems: list[PaymentSystem]) -> InlineKeyboardMarkup:
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_text, callback_data=f"tasdiq-{wallet}-{number}-{amount}")],
            [InlineKeyboardButton(text=cancel_text, callback_data="bekor")]
        ]
    )


def get_admin_withdrawal_request_keyboard(
    withdrawal_id: int,
    user_id: int,
    user_display: str = "",
    number: str = "",
    amount: float = 0.0
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ To'landi (Isbot kanalga)", callback_data=f"tolandi_{withdrawal_id}"),
                InlineKeyboardButton(text="❌ To'lanmadi", callback_data=f"tolanmadi_{withdrawal_id}")
            ],
            [InlineKeyboardButton(text="🔔 Foydalanuvchini banlash", callback_data=f"block_user_{user_id}")]
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
            [InlineKeyboardButton(text="📢 Isbot kanalini ko'rish", url=channel_url)]
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
            [InlineKeyboardButton(text="📄 Hozirgi holat", callback_data="holat")],
            [
                InlineKeyboardButton(text="👥 Referal narxi", callback_data="taklif"),
                InlineKeyboardButton(text="💸 Minimal yechish narxi", callback_data="narx")
            ],
            [
                InlineKeyboardButton(text="💳 To'lov rekvizitlari", callback_data="card_details_setting"),
                InlineKeyboardButton(text="📎 Admin useri", callback_data="admin_user_setting")
            ],
            [
                InlineKeyboardButton(text="🖼 Taklif rasmi", callback_data="taklif_rasm"),
                InlineKeyboardButton(text="💶 Valyuta", callback_data="valyuta")
            ],
            [
                InlineKeyboardButton(text="Yopish", callback_data="yopish")
            ]
        ]
    )


def get_admin_tariffs_keyboard(tariffs: list[UcTariff]) -> InlineKeyboardMarkup:
    rows = []
    for t in tariffs:
        rows.append([
            InlineKeyboardButton(
                text=f"💎 {t.uc_amount} UC — {t.price_uzs:,} so'm 🗑",
                callback_data=f"del_tariff_{t.id}"
            )
        ])
    rows.append([InlineKeyboardButton(text="➕ Yangi tarif qo'shish", callback_data="add_new_tariff")])
    rows.append([InlineKeyboardButton(text="Yopish", callback_data="yopish")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_admin_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔐 Majburiy obunalar", callback_data="majburiy")],
            [InlineKeyboardButton(text="🧾 Isbot kanal (To'lovlar kanali)", callback_data="qoshimcha")],
            [InlineKeyboardButton(text="Yopish", callback_data="yopish")]
        ]
    )


def get_mandatory_channels_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="qoshish")],
            [
                InlineKeyboardButton(text="📑 Ro'yxat", callback_data="royxat"),
                InlineKeyboardButton(text="🗑 Barchasini o'chirish", callback_data="ochirish")
            ],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="kanallar")]
        ]
    )


def get_additional_channels_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕️ Isbot kanalni sozlash", callback_data="vazifa")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="kanallar")]
        ]
    )


def get_broadcast_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Oddiy xabar (barchaga)", callback_data="broadcast_simple"),
                InlineKeyboardButton(text="Forward xabar (barchaga)", callback_data="broadcast_forward")
            ],
            [InlineKeyboardButton(text="Aynan bir foydalanuvchiga", callback_data="broadcast_direct")]
        ]
    )


def get_user_manage_keyboard(target_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_label = "🔕 Bandan olish" if is_banned else "🔔 Banlash"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ban_label, callback_data=f"toggle_ban-{target_id}")],
            [
                InlineKeyboardButton(text="➕ UC qo'shish", callback_data=f"plus-{target_id}"),
                InlineKeyboardButton(text="➖ UC ayirish", callback_data=f"minus-{target_id}")
            ]
        ]
    )


def get_support_inline_keyboard(admin_username: str, proof_channel: str | None = None) -> InlineKeyboardMarkup:
    buttons = []
    clean_admin = admin_username.lstrip("@")
    if admin_username and admin_username != "Kiritilmagan":
        buttons.append([InlineKeyboardButton(text="👨‍💻 Admin bilan bog'lanish", url=f"https://t.me/{clean_admin}")])
    buttons.append([InlineKeyboardButton(text="✍️ Bot orqali murojaat yuborish", callback_data="send_support_msg")])

    if proof_channel and proof_channel != "Kiritilmagan":
        clean_proof = proof_channel.lstrip("@")
        buttons.append([InlineKeyboardButton(text="🧾 Isbot kanal", url=f"https://t.me/{clean_proof}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_systems_admin_keyboard(payment_systems: list[PaymentSystem]) -> InlineKeyboardMarkup:
    buttons = []
    for ps in payment_systems:
        name = ps.name if hasattr(ps, "name") else str(ps)
        buttons.append([InlineKeyboardButton(text=f"🗑 {name}", callback_data=f"del-{name}")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi to'lov tizimi qo'shish", callback_data="new_payment")])
    buttons.append([InlineKeyboardButton(text="Yopish", callback_data="yopish")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_earn_photo_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Rasm o'rnatish", callback_data="rasm_ornatish")],
            [InlineKeyboardButton(text="🔄 Standart rasmga qaytarish", callback_data="reset_earn_photo")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="asosiy")]
        ]
    )


# Alias
get_cabinet_keyboard = get_cabinet_inline_keyboard
