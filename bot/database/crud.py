import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import (
    User, BotSetting, MandatoryChannel, PaymentSystem, Withdrawal, BotText, UcTariff, UcOrder
)

logger = logging.getLogger("CRUD")

DEFAULT_SETTINGS = {
    "taklif": "5",
    "valyuta": "UC",
    "narx": "60",
    "admin_user": "Kiritilmagan",
    "vazifa": "Kiritilmagan",  # Isbot / To'lovlar kanali
    "earn_photo": "https://t.me/BOT_UCHUN_RASMLAR/12",
    "card_details": "Karta raqami: 8600 0000 0000 0000\nQabul qiluvchi: Admin\nTo'lov izohiga: PUBG ID raqamingizni yozing.",
}

DEFAULT_BUTTONS = {
    "earn": "🎁 UC ishlash",
    "cabinet": "👤 Hisob",
    "buy_withdraw": "💎 UC sotib olish / Yechish",
    "buy_uc": "🛒 UC sotib olish",
    "solve": "💰 UC yechib olish",
    "tolov": "🧾 Isbot kanal",
    "support": "💬 Yordam",
    "manual": "ℹ️ Qo'llanma",
    "back": "◀️ Orqaga",
    "getPhone": "☎️ Kontaktni yuborish",
    "check": "🔄 Tekshirish",
    "contiune": "✅ Davom etish",
    "share": "↗️ Do'stlarga ulashish",
    "cancellation": "🚫 Bekor qilish",
    "confirm": "✅ Tasdiqlash",
    "transition": "🤖 Botga o'tish"
}

DEFAULT_TEXTS = {
    "welcome": "👋 <b>Assalomu alaykum, botimizga xush kelibsiz!</b>\n\nQuyidagi menyu orqali botdan foydalanishingiz mumkin:",
    "subChannels": "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>\n\nObuna bo'lgach <b>🔄 Tekshirish</b> tugmasini bosing:",
    "tolovtext": "<b>⤵️ Quyidagi havola orqali isbotlar va to'lovlarni kuzatib boring:</b>",
    "newRef": "📳 <b>Sizda yangi</b> <a href='tg://user?id=%refid%'>taklif</a> <b>mavjud!</b>",
    "checkRef": "✅ <b>Hisobingizga %refpay% %currency% qo'shildi!</b>",
    "backHome": "🖥 <b>Asosiy menyudasiz.</b>",
    "textPhone": "📲 <b>Botdan to'liq foydalanish uchun telefon raqamingizni yuboring:</b>",
    "conPhone": "<b>✅ Telefon raqamingiz qabul qilindi:</b> %phone%\n\n<i>Botdan foydalanishni boshlash uchun quyidagi tugmani bosing:</i>",
    "noPhone": "<b>Kechirasiz, Botdan faqat O'zbekiston fuqarolari foydalanishi mumkin (+998).</b>",
    "earnRef": (
        "👥 <b>Sizning taklif havolangiz:</b>\n\n"
        "<code>%reflink%</code>\n\n"
        "<i>Yuqoridagi taklif havolangizni do'stlaringizga tarqating va har bir taklifingiz uchun <b>%refpay% %currency%</b> hisobingizga qo'shiladi!</i>"
    ),
    "cabinet": (
        "👤 <b>Foydalanuvchi hisobi:</b>\n\n"
        "🆔 <b>Telegram ID:</b> <code>%id%</code>\n"
        "🎮 <b>PUBG ID:</b> <code>%pubgid%</code>\n\n"
        "💎 <b>Balansingiz:</b> <b>%balance% %currency%</b>\n"
        "👥 <b>Taklif qilgan do'stlaringiz:</b> <b>%refcount% ta</b>\n"
        "💸 <b>Jami yechib olingan:</b> <b>%solve% %currency%</b>"
    ),
    "selectPayType": "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
    "minimum": "⛔ <b>Minimal yechib olish miqdori: %minimum% %currency%!</b>\nSizning balansingiz: %balance% %currency%",
    "noChannel": "Isbot va to'lovlar kanali ulanmagan!",
    "sendCard": "<b>PUBG Akkaunt ID raqamingizni kiriting:</b>",
    "accpeted": "✅ <b>Arizangiz qabul qilindi!</b>\n\n• <b>Operatsiya:</b> UC yechib olish\n• <b>To'lov turi:</b> %wallet%\n• <b>PUBG ID:</b> %phone%\n• <b>UC miqdori:</b> %amount% %currency%\n\n<i>Ma'lumotlar to'g'ri ekanligiga ishonch hosil qilib, tasdiqlang.</i>",
    "solveMoney": "<b>Qancha miqdorda UC yechib olmoqchisiz:</b>",
    "solveMinimum": "<b>Minimal yechib olish miqdori:</b> %minimum% %currency%\n\nQayta urinib ko'ring:",
    "lowBalance": "<b>Hisobingizda yetarli mablag' mavjud emas!</b>\n\nQayta urinib ko'ring:",
    "accped": "✅ <b>Arizangiz qabul qilindi va adminga yuborildi.</b>\nTez orada ko'rib chiqiladi!",
    "canceled": "⛔ <b>Operatsiya bekor qilindi.</b>",
    "hasBeenPaid": "<b>Hurmatli %first%!\n\nUC yechib olish haqidagi arizangiz tasdiqlandi va PUBG hisobingizga tashlab berildi! ✅</b>",
    "wasNotPaid": "<b>Hurmatli %first%!\n\nUC yechib olish haqidagi arizangiz rad etildi va mablag' balansingizga qaytarildi. ❌</b>",
    "block": "<b>Hurmatli %first%!\n\nQoidalarni buzganligingiz sababli botdan bloklandingiz.</b>",
    "BeenPaid": "✅ <a href='tg://user?id=%id%'>%first%</a> <b>foydalanuvchiga UC to'lab berildi!</b>\n\n• <b>UC miqdori:</b> %amount% UC\n• <b>PUBG ID:</b> <code>%phone%</code>\n\n%advertising%",
    "sendSuppMsg": "📝 <b>Murojaat yoki savolingizni yozib qoldiring:</b>",
    "SuppSend": "✅ <b>Murojaatingiz adminga yuborildi.</b>\nTez orada siz bilan bog'lanishadi!",
    "advertising": "🤖 <b>Rasmiy botimiz:</b> @%botname%",
    "manuals": (
        "<b>📚 Botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "1. <b>🎁 UC ishlash:</b>\n"
        "O'zingizning referal havolangizni do'stlaringizga yuboring. Har bir yangi foydalanuvchi homiy kanallarga obuna bo'lganda sizga bepul UC beriladi.\n\n"
        "2. <b>👤 Hisob:</b>\n"
        "Bu yerda siz o'zingizning balansingiz, takliflaringiz soni va PUBG ID raqamingizni ko'rishingiz mumkin.\n\n"
        "3. <b>🛒 UC sotib olish:</b>\n"
        "Hamyonbop narxlardagi UC paketlarini sotib olishingiz mumkin. PUBG ID raqamingizni kiritasiz va to'lov chekini yuborasiz. Admin tasdiqlagach UC akkauntingizga yuklanadi.\n\n"
        "4. <b>💰 UC yechib olish:</b>\n"
        "Balansingizdagi to'plangan UClarni minimal miqdorga yetganda to'g'ridan-to'g'ri o'z PUBG akkauntingizga yechib olishingiz mumkin.\n\n"
        "⚠️ <i>Eslatma: Soxta takliflar (nakrutka) qat'iyan taqiqlanadi, bunday hisoblar bloklanadi.</i>"
    )
}

DEFAULT_TARIFFS = [
    (30, 6000),
    (60, 11000),
    (120, 21000),
    (355, 60000),
    (720, 120000),
]

DEFAULT_PAYMENT_SYSTEMS = ["PUBG Mobile ID (To'g'ridan-to'g'ri)", "Payme", "Click", "Uzum Bank"]


async def init_default_settings(session: AsyncSession):
    """Standart sozlamalar, matnlar va tariflarni bazaga initsializatsiya qiladi."""
    # 1. Sozlamalar
    for k, v in DEFAULT_SETTINGS.items():
        res = await session.execute(select(BotSetting).where(BotSetting.key == k))
        if not res.scalar_one_or_none():
            session.add(BotSetting(key=k, value=v))

    # 2. Tugmalar
    for k, v in DEFAULT_BUTTONS.items():
        res = await session.execute(
            select(BotText).where(BotText.key == k, BotText.type == "button")
        )
        if not res.scalar_one_or_none():
            session.add(BotText(key=k, type="button", value=v))

    # 3. Matnlar
    for k, v in DEFAULT_TEXTS.items():
        res = await session.execute(
            select(BotText).where(BotText.key == k, BotText.type == "text")
        )
        if not res.scalar_one_or_none():
            session.add(BotText(key=k, type="text", value=v))

    # 4. To'lov tizimlari
    p_res = await session.execute(select(func.count(PaymentSystem.id)))
    if p_res.scalar() == 0:
        for p_name in DEFAULT_PAYMENT_SYSTEMS:
            session.add(PaymentSystem(name=p_name, is_active=True))

    # 5. Standart UC tariflari
    t_res = await session.execute(select(func.count(UcTariff.id)))
    if t_res.scalar() == 0:
        for uc, price in DEFAULT_TARIFFS:
            session.add(UcTariff(uc_amount=uc, price_uzs=price, is_active=True))

    await session.commit()


# ==============================================================================
# USER CRUD
# ==============================================================================

async def get_user(session: AsyncSession, user_id: int) -> User | None:
    res = await session.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    referrer_id: int | None = None
) -> tuple[User, bool]:
    user = await get_user(session, user_id)
    if user:
        updated = False
        if username and user.username != username:
            user.username = username
            updated = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            await session.commit()
        return user, False

    user = User(
        id=user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        referrer_id=referrer_id if (referrer_id and referrer_id != user_id) else None
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user, True


async def update_user_phone(session: AsyncSession, user_id: int, phone: str):
    user = await get_user(session, user_id)
    if user:
        user.phone = phone
        await session.commit()


async def update_user_pubg_id(session: AsyncSession, user_id: int, pubg_id: str):
    user = await get_user(session, user_id)
    if user:
        user.pubg_id = pubg_id.strip()
        await session.commit()


async def update_user_balance(session: AsyncSession, user_id: int, delta: float) -> float:
    user = await get_user(session, user_id)
    if user:
        user.balance = max(0.0, round(float(user.balance) + float(delta), 2))
        await session.commit()
        return user.balance
    return 0.0


async def increment_referral(session: AsyncSession, referrer_id: int, reward_amount: float):
    user = await get_user(session, referrer_id)
    if user:
        user.referral_count += 1
        user.balance = round(float(user.balance) + float(reward_amount), 2)
        await session.commit()


async def set_user_ban(session: AsyncSession, user_id: int, is_banned: bool):
    user = await get_user(session, user_id)
    if user:
        user.is_banned = is_banned
        await session.commit()


async def get_users_count(session: AsyncSession) -> int:
    res = await session.execute(select(func.count(User.id)))
    return res.scalar() or 0


async def get_all_user_ids(session: AsyncSession) -> list[int]:
    res = await session.execute(select(User.id))
    return [row[0] for row in res.fetchall()]


# ==============================================================================
# SETTINGS CRUD
# ==============================================================================

async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    res = await session.execute(select(BotSetting.value).where(BotSetting.key == key))
    val = res.scalar_one_or_none()
    return val if val is not None else default


async def set_setting(session: AsyncSession, key: str, value: str):
    setting = await session.get(BotSetting, key)
    if setting:
        setting.value = str(value)
    else:
        session.add(BotSetting(key=key, value=str(value)))
    await session.commit()


async def get_all_settings(session: AsyncSession) -> dict[str, str]:
    res = await session.execute(select(BotSetting))
    return {row.key: row.value for row in res.scalars().all()}


# ==============================================================================
# MANDATORY CHANNELS CRUD
# ==============================================================================

async def get_mandatory_channels(session: AsyncSession) -> list[MandatoryChannel]:
    res = await session.execute(select(MandatoryChannel).order_by(MandatoryChannel.id))
    return list(res.scalars().all())


async def add_mandatory_channel(session: AsyncSession, username: str, title: str | None = None) -> bool:
    clean_user = username.strip()
    if not clean_user.startswith("@"):
        clean_user = f"@{clean_user}"
    existing = await session.execute(select(MandatoryChannel).where(MandatoryChannel.username == clean_user))
    if existing.scalar_one_or_none():
        return False
    session.add(MandatoryChannel(username=clean_user, title=title))
    await session.commit()
    return True


async def delete_all_mandatory_channels(session: AsyncSession):
    await session.execute(delete(MandatoryChannel))
    await session.commit()


async def delete_mandatory_channel(session: AsyncSession, username: str):
    clean_user = username.strip()
    if not clean_user.startswith("@"):
        clean_user = f"@{clean_user}"
    await session.execute(delete(MandatoryChannel).where(MandatoryChannel.username == clean_user))
    await session.commit()


# ==============================================================================
# UC TARIFFS CRUD
# ==============================================================================

async def get_active_tariffs(session: AsyncSession) -> list[UcTariff]:
    res = await session.execute(select(UcTariff).where(UcTariff.is_active == True).order_by(UcTariff.uc_amount))
    return list(res.scalars().all())


async def get_all_tariffs(session: AsyncSession) -> list[UcTariff]:
    res = await session.execute(select(UcTariff).order_by(UcTariff.uc_amount))
    return list(res.scalars().all())


async def get_tariff(session: AsyncSession, tariff_id: int) -> UcTariff | None:
    res = await session.execute(select(UcTariff).where(UcTariff.id == tariff_id))
    return res.scalar_one_or_none()


async def add_tariff(session: AsyncSession, uc_amount: int, price_uzs: int) -> UcTariff:
    tariff = UcTariff(uc_amount=uc_amount, price_uzs=price_uzs, is_active=True)
    session.add(tariff)
    await session.commit()
    await session.refresh(tariff)
    return tariff


async def delete_tariff(session: AsyncSession, tariff_id: int):
    await session.execute(delete(UcTariff).where(UcTariff.id == tariff_id))
    await session.commit()


# ==============================================================================
# UC ORDERS (SOTIB OLISH) CRUD
# ==============================================================================

async def create_order(
    session: AsyncSession,
    user_id: int,
    uc_amount: int,
    price_uzs: int,
    pubg_id: str,
    receipt_file_id: str | None = None
) -> UcOrder:
    order = UcOrder(
        user_id=user_id,
        uc_amount=uc_amount,
        price_uzs=price_uzs,
        pubg_id=pubg_id,
        receipt_file_id=receipt_file_id,
        status="pending"
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_order(session: AsyncSession, order_id: int) -> UcOrder | None:
    res = await session.execute(select(UcOrder).where(UcOrder.id == order_id))
    return res.scalar_one_or_none()


async def mark_order_approved(session: AsyncSession, order_id: int) -> UcOrder | None:
    order = await get_order(session, order_id)
    if order and order.status == "pending":
        order.status = "approved"
        order.processed_at = datetime.now(timezone.utc)
        await session.commit()
    return order


async def mark_order_rejected(session: AsyncSession, order_id: int) -> UcOrder | None:
    order = await get_order(session, order_id)
    if order and order.status == "pending":
        order.status = "rejected"
        order.processed_at = datetime.now(timezone.utc)
        await session.commit()
    return order


async def get_pending_orders_count(session: AsyncSession) -> int:
    res = await session.execute(select(func.count(UcOrder.id)).where(UcOrder.status == "pending"))
    return res.scalar() or 0


# ==============================================================================
# PAYMENT SYSTEMS CRUD
# ==============================================================================

async def get_active_payment_systems(session: AsyncSession) -> list[PaymentSystem]:
    res = await session.execute(select(PaymentSystem).where(PaymentSystem.is_active == True).order_by(PaymentSystem.id))
    return list(res.scalars().all())


async def add_payment_system(session: AsyncSession, name: str) -> bool:
    clean_name = name.strip()
    existing = await session.execute(select(PaymentSystem).where(PaymentSystem.name == clean_name))
    item = existing.scalar_one_or_none()
    if item:
        item.is_active = True
        await session.commit()
        return True
    session.add(PaymentSystem(name=clean_name, is_active=True))
    await session.commit()
    return True


async def delete_payment_system(session: AsyncSession, name: str):
    clean_name = name.strip()
    await session.execute(delete(PaymentSystem).where(PaymentSystem.name == clean_name))
    await session.commit()


# ==============================================================================
# WITHDRAWALS CRUD
# ==============================================================================

async def create_withdrawal(
    session: AsyncSession,
    user_id: int,
    payment_system: str,
    wallet_number: str,
    amount: float,
    pubg_id: str | None = None
) -> Withdrawal:
    withdrawal = Withdrawal(
        user_id=user_id,
        payment_system=payment_system,
        wallet_number=wallet_number,
        pubg_id=pubg_id or wallet_number,
        amount=amount,
        status="pending"
    )
    session.add(withdrawal)
    # Deduct from user balance, increment withdrawn
    user = await get_user(session, user_id)
    if user:
        user.balance = max(0.0, round(float(user.balance) - float(amount), 2))
        user.withdrawn = round(float(user.withdrawn) + float(amount), 2)
    await session.commit()
    await session.refresh(withdrawal)
    return withdrawal


async def get_withdrawal(session: AsyncSession, withdrawal_id: int) -> Withdrawal | None:
    res = await session.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    return res.scalar_one_or_none()


async def mark_withdrawal_paid(session: AsyncSession, withdrawal_id: int, channel_msg_id: int | None = None) -> Withdrawal | None:
    w = await get_withdrawal(session, withdrawal_id)
    if w and w.status == "pending":
        w.status = "paid"
        w.channel_msg_id = channel_msg_id
        w.processed_at = datetime.now(timezone.utc)
        await session.commit()
    return w


async def mark_withdrawal_rejected(session: AsyncSession, withdrawal_id: int) -> Withdrawal | None:
    w = await get_withdrawal(session, withdrawal_id)
    if w and w.status == "pending":
        w.status = "rejected"
        w.processed_at = datetime.now(timezone.utc)
        # Refund to user
        user = await get_user(session, w.user_id)
        if user:
            user.balance = round(float(user.balance) + float(w.amount), 2)
            user.withdrawn = max(0.0, round(float(user.withdrawn) - float(w.amount), 2))
        await session.commit()
    return w


async def get_pending_withdrawals_count(session: AsyncSession) -> int:
    res = await session.execute(select(func.count(Withdrawal.id)).where(Withdrawal.status == "pending"))
    return res.scalar() or 0


# ==============================================================================
# BOT TEXTS & BUTTONS CRUD
# ==============================================================================

async def get_text_or_button(session: AsyncSession, key: str, text_type: str = "text") -> str | None:
    res = await session.execute(
        select(BotText.value).where(BotText.key == key, BotText.type == text_type)
    )
    return res.scalar_one_or_none()


async def set_text_or_button(session: AsyncSession, key: str, value: str, text_type: str = "text"):
    res = await session.execute(
        select(BotText).where(BotText.key == key, BotText.type == text_type)
    )
    item = res.scalar_one_or_none()
    if item:
        item.value = value
    else:
        session.add(BotText(key=key, value=value, type=text_type))
    await session.commit()


async def get_all_texts(session: AsyncSession, text_type: str | None = None) -> dict[str, str]:
    query = select(BotText)
    if text_type:
        query = query.where(BotText.type == text_type)
    res = await session.execute(query)
    return {row.key: row.value for row in res.scalars().all()}
