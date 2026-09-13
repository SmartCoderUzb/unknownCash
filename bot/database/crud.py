import logging
from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import (
    User, BotSetting, MandatoryChannel, PaymentSystem, Withdrawal, BotText
)

logger = logging.getLogger("CRUD")

DEFAULT_SETTINGS = {
    "taklif": "5",
    "valyuta": "uc",
    "narx": "210",
    "admin_user": "Kiritilmagan",
    "vazifa": "Kiritilmagan",
    "earn_photo": "https://t.me/BOT_UCHUN_RASMLAR/12"
}

DEFAULT_BUTTONS = {
    "earn": "🎁 Uc ishlash",
    "solve": "💰Ucni yechish",
    "cabinet": "🏦 Hisobim",
    "tolov": "🧾 To'lovlar kanali",
    "support": "💌 Yordam",
    "manual": "📚 Qo'llanma",
    "back": "◀️ Orqaga",
    "getPhone": "☎️ Kontaktni yuborish",
    "check": "🔄 Tekshirish",
    "contiune": "✅ Davom etish",
    "share": "↗️ Ulashish",
    "cancellation": "🚫 Bekor qilish",
    "confirm": "✅ Tasdiqlash",
    "transition": "🤖 Botga o'tish"
}

DEFAULT_TEXTS = {
    "welcome": "🖥 <b>Asosiy menyudasiz.</b>",
    "subChannels": "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi kanallarimizga obuna bo'ling!</b>",
    "tolovtext": "<b>⤵️ Quyidagi kanal orqali to'lovlarni kuzatib boring:</b>",
    "newRef": "📳 <b>Sizda yangi</b> <a href='tg://user?id=%refid%'>taklif</a> <b>mavjud!</b>",
    "checkRef": "✅ <b>Hisobingizga %refpay% %currency% qo'shildi!</b>",
    "backHome": "🖥 <b>Asosiy menyuga qaytdingiz.</b>",
    "textPhone": "📲 <b>Botdan ro'yxatdan o'tish uchun quyidagi tugma orqali telefon raqamingizni yuboring:</b>",
    "conPhone": "<b>✅ Telefon raqamingiz qabul qilindi:</b> %phone%\n\n<i>Botdan foydalanishni boshlash uchun quyidagi tugmani bosing:</i>",
    "noPhone": "<b>Kechirasiz, Botdan faqat O'zbekiston fuqarolari foydalanishi mumkin.</b>",
    "earnRef": "👥️️ <b>Sizning taklif havolangiz:</b>\n\n%reflink%\n\n<i>Yuqoridagi taklif havolangizni do'stlaringizga tarqating va har bir to'liq ro'yxatdan o'tgan taklifingiz uchun %refpay% %currency% hisobingizga qo'shiladi.</i>",
    "cabinet": "🔑 <b>Sizning ID raqamingiz:</b> <pre>%id%</pre>\n\n💸 <b>Asosiy balansingiz:</b> %balance% %currency%\n👤 <b>Takliflaringiz soni:</b> %refcount% ta\n\n💳 <b>Yechib olgan uclaringiz:</b> %solve% %currency%",
    "selectPayType": "👇 <b>Quyidagi to'lov tizimlaridan birini tanlang:</b>",
    "minimum": "⛔ Jarayonni davom ettira olmaysiz!\n\nMinimal yechib olish miqdori: %minimum% %currency%",
    "noChannel": "To'lovlar kanali ulanmagan!",
    "sendCard": "<b>Hamyoningiz raqamini yuboring:</b>",
    "accpeted": "✅ <b>Qabul qilindi!</b>\n\n• <b>To'lov turi:</b> %wallet%\n• <b>Uc miqdori:</b> %amount%\n• <b>Hamyon raqamingiz:</b> %phone%\n\n<b>Ma'lumotlar to'g'ri ekanligiga ishonch hosil qilgan bo'lsangiz, ✅ Tasdiqlash tugmasini bosing!</b>",
    "solveMoney": "<b>Qancha miqdorda uc yechib olmoqchisiz:</b>",
    "solveMinimum": "<b>Minimal yechib olish miqdori:</b> %minimum% %currency%\n\nQayta urinib ko'ring:",
    "lowBalance": "<b>Hisobingizda yetarli mablag' mavjud emas!</b>\n\nQayta urinib ko'ring:",
    "accped": "✅ <b>Qabul qilindi.</b>",
    "canceled": "⛔ <b>Bekor qilindi.</b>",
    "hasBeenPaid": "<b>Hurmatli %first%!\n\nUclaringizni yechib olish haqidagi arizangiz qabul qilindi.</b>",
    "wasNotPaid": "<b>Hurmatli %first%!\n\nUclaringizni yechib olish haqidagi arizangiz qabul qilinmadi.</b>",
    "block": "<b>Hurmatli %first%!\n\nUclaringizni yechib olish haqidagi arizangiz qabul qilinmadi va botdan blocklandingiz.</b>",
    "BeenPaid": "✅ <a href='tg://user?id=%id%'>%first%</a> <b>foydalanuvchi uci to'lab berildi.</b>\n\n• <b>Uc miqdori:</b> %amount%\n• <b>Hamyon raqami:</b> %phone%\n\n%advertising%",
    "sendSuppMsg": "📝 <b>Murojaat matnini yuboring:</b>",
    "SuppSend": "✅ <b>Murojaatingiz yuborildi.</b>\n\nTez orada javob qaytaramiz!",
    "advertising": "🤖 <b>Rasmiy botimiz:</b> @%botname%",
    "manuals": (
        "<b>Savol: 🎁Qanday qilib tekin uc olishim mumkin ❓\n\n"
        "Javob: Botimiz orqali odam taklif qilib uc olsangiz boʻladi✅\n\n\n"
        "Savol: Nega menga uc qoʻshilmayabdi taklif qildimku ❓\n\n"
        "Javob: Taklif qilgan foydalanuvchi botimizdan toʻliq roʻyxatdan oʻtsa albatta sizga uc qoʻshiladi✅\n\n\n"
        "Savol: Nega meni hisobim minus boʻldi ❓\n\n\n"
        "Javob: Taklif qilgan doʻstlaringiz hamkor kanallardan tark etgani uchun sizdan minus boʻldi✅\n\n"
        "⚠️ Eslatma: doʻstlaringiz kanaldan tark etsa sizdan uc yechib olinadi ❗</b>"
    )
}

DEFAULT_PAYMENT_SYSTEMS = ["PUBG Mobile ID", "Payme", "Click", "Uzum Bank"]


async def init_default_settings(session: AsyncSession):
    """Standart sozlamalar va matnlarni bazaga initsializatsiya qiladi."""
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
    amount: float
) -> Withdrawal:
    withdrawal = Withdrawal(
        user_id=user_id,
        payment_system=payment_system,
        wallet_number=wallet_number,
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
