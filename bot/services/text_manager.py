from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from bot.core.config import TASHKENT_TZ
from bot.database import crud

class TextService:
    @staticmethod
    async def get_button(session: AsyncSession, key: str) -> str:
        val = await crud.get_text_or_button(session, key, text_type="button")
        if val is not None:
            return val
        return crud.DEFAULT_BUTTONS.get(key, key)

    @staticmethod
    async def get_text(
        session: AsyncSession,
        key: str,
        first: str = "",
        last: str = "",
        user_id: int | str = "",
        username: str = "",
        botname: str = "",
        admin_user: str = "",
        balance: float | str = "0",
        refcount: int | str = "0",
        currency: str = "uc",
        solve: float | str = "0",
        phone: str = "",
        reflink: str = "",
        refpay: float | str = "5",
        amount: float | str = "0",
        wallet: str = "",
        minimum: float | str = "210",
        refid: int | str = "",
        reffirst: str = "",
        reflast: str = "",
        **extra
    ) -> str:
        raw_text = await crud.get_text_or_button(session, key, text_type="text")
        if raw_text is None:
            raw_text = crud.DEFAULT_TEXTS.get(key, "")

        now = datetime.now(TASHKENT_TZ)
        hour = now.strftime("%H:%M")
        date = now.strftime("%d.%m.%Y")

        # Advertising replacement if needed
        adv_text = await crud.get_text_or_button(session, "advertising", text_type="text")
        if adv_text is None:
            adv_text = crud.DEFAULT_TEXTS.get("advertising", f"🤖 <b>Rasmiy botimiz:</b> @{botname}")
        adv_text = adv_text.replace("%botname%", str(botname))

        replacements = {
            "%first%": str(first or ""),
            "%last%": str(last or ""),
            "%id%": str(user_id or ""),
            "%username%": str(username or ""),
            "%botname%": str(botname or ""),
            "%user%": str(admin_user or ""),
            "%balance%": str(balance),
            "%refcount%": str(refcount),
            "%currency%": str(currency),
            "%solve%": str(solve),
            "%hour%": hour,
            "%date%": date,
            "%phone%": str(phone or ""),
            "%reflink%": str(reflink or ""),
            "%refpay%": str(refpay),
            "%amount%": str(amount),
            "%wallet%": str(wallet or ""),
            "%minimum%": str(minimum),
            "%refid%": str(refid or ""),
            "%reffirst%": str(reffirst or ""),
            "%reflast%": str(reflast or ""),
            "%advertising%": adv_text,
        }

        for k, v in replacements.items():
            raw_text = raw_text.replace(k, v)

        return raw_text
