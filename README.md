# UnknownCash (Python + PostgreSQL + Redis)

Ushbu loyiha avval PHP tilida yozilgan (`UnknownCash.php` / `UcBot.php`) PUBG Mobile Unknown Cash (UC) va o'yin valyutalarini referal hamda vazifalar orqali ishlash/yechish botining **Python 3.12+ (Aiogram 3.x, SQLAlchemy 2.0 Async, Redis FSM, PostgreSQL Schema Isolation)** asosidagi to'liq qayta yozilgan mikroxizmat sub-bot loyihasidir.

---

## 🚀 Texnologiyalar Steki
- **Dasturlash tili:** Python 3.12+
- **Telegram Bot Framework:** Aiogram 3.x
- **ORM / Ma'lumotlar bazasi:** SQLAlchemy 2.0 (Async) + `asyncpg` drayveri
- **FSM Storage:** Redis (`RedisStorage` + `DefaultKeyBuilder` schema prefiksi bilan)
- **Konfiguratsiya:** Pydantic v2 & `pydantic-settings`
- **Veb-server (Dual-Mode):** `aiohttp.web` (Webhook) va Polling fallback

---

## 📂 Loyiha Tuzilmasi

```text
uc_bot/
├── bot/
│   ├── core/
│   │   ├── config.py       # Pydantic Settings (.env, DB/Redis aliaslari, multi-tenancy)
│   │   └── loader.py       # Bot, Dispatcher, RedisStorage initsializatsiyasi
│   ├── database/
│   │   ├── base.py         # DeclarativeBase
│   │   ├── models.py       # User, BotSetting, MandatoryChannel, PaymentSystem, Withdrawal, BotText
│   │   ├── session.py      # PostgreSQL Schema Isolation (CREATE SCHEMA, SET search_path)
│   │   └── crud.py         # Asinxron DB CRUD operatsiyalari
│   ├── handlers/
│   │   ├── admin/          # Admin paneli (/panel, sozlamalar, kanallar, xabarnoma, to'lovlar)
│   │   ├── user/           # Foydalanuvchi (/start, hisobim, uc ishlash, yechish, yordam)
│   │   └── common.py       # Umumiy xatoliklar handlerlari
│   ├── keyboards/          # Reply va Inline tugmalar
│   ├── middlewares/        # DbSessionMiddleware, UserTrackerMiddleware (ban, a'zo tekshiruvi)
│   ├── services/           # Matnlar menejeri (dinamik o'zgaruvchilar), Obunani tekshirish
│   └── states/             # FSM States (UserStates, AdminStates)
├── main.py                 # Asosiy ishga tushirish (Readiness Probe, Dual-Mode)
├── requirements.txt        # Kerakli paketlar ro'yxati
├── .env.example            # Sozlamalar namunasi
└── README.md
```

---

## ⚙️ Sozlamalar (.env)

| Parametr | Standart qiymat | Tavsif |
|---|---|---|
| `BOT_TOKEN` | - | Telegram BotFather tokeni |
| `ADMIN_ID` | `0` | Bot egasining asosiy Telegram ID raqami |
| `SUPER_ADMINS` | - | Qo'shimcha adminlar ID ro'yxati (vergul bilan) |
| `BOT_ID` | `1` | Botning platformadagi raqamli ID si |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `postgres` | Baza foydalanuvchisi |
| `DB_PASSWORD`| - | Baza paroli |
| `DB_NAME` | `builder_db` | Baza nomi |
| `DB_SCHEMA` | `uc_bot_{BOT_ID}` | Multi-tenancy PostgreSQL schema nomi |
| `REDIS_HOST`| `localhost` | Redis server host |
| `REDIS_PORT`| `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis baza indeksi |
| `WEBHOOK_URL`| `""` | Webhook URL (bo'sh qoldirilsa Polling ishlaydi) |

---

## 🛠 O'rnatish va Ishga tushirish

1. Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. Muhit parametrlarini sozlash:
```bash
cp .env.example .env
nano .env
```

3. Ishga tushirish:
```bash
python3 main.py
```
Konsolda quyidagi qat'iy satr chiqsa, bot to'liq ishga tushgan hisoblanadi:
`Bot muvaffaqiyatli ishga tushdi: @BotUsername`
