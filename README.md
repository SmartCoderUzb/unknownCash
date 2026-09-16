# UnknownCash (PUBG UC Bot) - BuilderBot Sub-Bot

Ushbu loyiha **BuilderBot platformasi** uchun mustaqil sub-bot arxitekturasi va shartnomasi (contract) asosida yaratilgan **PUBG Mobile Unknown Cash (UC)** xarid qilish, referal tizimi orqali UC ishlash va hisobga yechib olish botidir.

---

## 🚀 Texnologiyalar Steki
- **Dasturlash tili:** Python 3.12+
- **Telegram Framework:** Aiogram 3.x
- **Ma'lumotlar bazasi:** PostgreSQL (Async SQLAlchemy 2.0 + `asyncpg` drayveri)
- **Multi-tenancy Isolation:** PostgreSQL Schema (`CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"`, `SET search_path TO "{DB_SCHEMA}"`)
- **FSM Storage:** Redis (`RedisStorage` + `DefaultKeyBuilder(with_bot_id=True, prefix=settings.DB_SCHEMA)`)
- **Dual-Mode Webhook:** `aiohttp.web` (Webhook) va Polling fallback
- **Konfiguratsiya:** Pydantic v2 & `pydantic-settings`

---

## 📂 Papkalar Strukturasi

```text
unknownCash/
├── bot/
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (.env, DB/Redis aliaslari, multi-tenancy)
│   │   └── loader.py           # Bot, Dispatcher, RedisStorage initsializatsiyasi
│   ├── database/
│   │   ├── base.py             # DeclarativeBase
│   │   ├── session.py          # PostgreSQL Schema Isolation (CREATE SCHEMA, search_path)
│   │   ├── crud.py             # Asinxron DB CRUD operatsiyalari
│   │   └── models/             # SQLAlchemy modellari
│   │       ├── user.py         # Foydalanuvchilar (balans, PUBG ID, referallar)
│   │       ├── tariff.py       # UC sotib olish tariflari (UC miqdori va narxi)
│   │       ├── order.py        # UC sotib olish buyurtmalari (chek, holat)
│   │       ├── withdrawal.py   # UC yechib olish arizalari
│   │       ├── channel.py      # Majburiy obuna kanallari
│   │       ├── payment.py      # To'lov tizimlari
│   │       ├── setting.py      # Bot dinamik sozlamalari
│   │       └── text.py         # Bot matnlari va tugmalari
│   ├── handlers/
│   │   ├── admin/              # Admin paneli (/admin)
│   │   │   ├── panel.py        # Asosiy admin menyusi va to'liq statistika
│   │   │   ├── tariffs.py      # UC tariflarini boshqarish (CRUD)
│   │   │   ├── orders.py       # UC xarid arizalarini ko'rib chiqish (Tasdiqlash/Rad)
│   │   │   ├── withdrawals.py  # UC yechib olish arizalarini ko'rib chiqish
│   │   │   ├── channels.py     # Majburiy obuna va Isbot kanal sozlamalari
│   │   │   ├── settings.py     # Referal narxi, minimal yechish, rekvizitlar
│   │   │   ├── users.py        # Foydalanuvchini boshqarish (ban, UC qo'shish/ayirish)
│   │   │   ├── broadcast.py    # Barcha a'zolarga xabarnoma (oddiy, forward, shaxsiy)
│   │   │   └── texts.py        # Bot matnlari va tugmalarini tahrirlash
│   │   ├── user/               # Foydalanuvchi bo'limlari
│   │   │   ├── start.py        # /start, referal tekshiruvi, majburiy obuna
│   │   │   ├── earn.py         # 🎁 UC ishlash (Referal havola va banner)
│   │   │   ├── cabinet.py      # 👤 Hisob (Balans, takliflar, PUBG ID tahriri)
│   │   │   ├── buy.py          # 🛒 UC sotib olish (Tariflar, to'lov cheki yuborish)
│   │   │   ├── withdraw.py     # 💰 UC yechib olish (PUBG ID ga so'rov yuborish)
│   │   │   ├── support.py      # 💬 Yordam (Admin bilan bog'lanish va murojaat)
│   │   │   └── other.py        # ℹ️ Qo'llanma va 🧾 Isbot kanal havolasi
│   │   └── common.py           # Xatoliklarni ushlash handlerlari
│   ├── keyboards/              # Reply va Inline tugmalar
│   │   ├── reply.py            # Asosiy menyu, orqaga, bekor qilish
│   │   └── inline.py           # Tariflar, tasdiqlash, admin boshqaruvi
│   ├── middlewares/
│   │   ├── db.py               # DbSessionMiddleware (har bir update uchun DB sessiya)
│   │   └── user_tracker.py     # UserTrackerMiddleware (avtomatik ro'yxatga olish, ban)
│   ├── services/
│   │   ├── subscription.py     # Majburiy kanallarga obunani tekshirish
│   │   └── text_manager.py     # Dinamik matn shablonlari (%balance%, %pubgid%, va h.k.)
│   └── states/
│       ├── admin_states.py     # Admin paneli FSM holatlari
│       └── user_states.py      # Foydalanuvchi FSM holatlari
├── main.py                     # Kirish nuqtasi (Readiness Probe, Dual-Mode)
├── requirements.txt            # Kerakli kutubxonalar
├── .env.example                # Konfiguratsiya namunasi
└── README.md
```

---

## ⚙️ .ENV Shartnomasi va Konfiguratsiya

BuilderBot platformasi tomonidan uzatiladigan barcha o'zgaruvchilar to'liq qo'llab-quvvatlanadi:

```dotenv
# 1. BOT & ADMIN MA'LUMOTLARI
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=6401724005
SUPER_ADMINS=6401724005,1934146361
BOT_ID=1
BOT_USERNAME=UnknownCashBot

# 2. POSTGRESQL DATABASE (Multi-tenancy Schema Isolation)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=parol
DB_NAME=builder_db
DB_SCHEMA=unknowncash_bot_1
# Yoki to'g'ridan-to'g'ri DSN:
DATABASE_URL=postgresql+asyncpg://postgres:parol@localhost:5432/builder_db

# 3. REDIS FSM STORAGE
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 4. DUAL-MODE WEBHOOK
WEBHOOK_URL=
WEBHOOK_HOST=
WEBHOOK_PATH=/webhook/bot/1
WEBAPP_HOST=127.0.0.1
WEBAPP_PORT=10001
```

---

## 🎮 Botning Asosiy Funksiyalari

1. **🎁 UC ishlash (Referal tizimi):**
   - Har bir taklif qilingan do'st uchun foydalanuvchiga belgilangan miqdorda UC beriladi.
   - Do'sti homiy kanallarga a'zo bo'lgach mukofot o'tkaziladi (nakrutkaga qarshi bir martalik tekshiruv).
   - Ulashish tugmasi orqali do'stlarga telegramda darhol uzatish mumkin.

2. **👤 Hisob (Shaxsiy kabinet):**
   - Balansdagi UC miqdori, taklif qilingan do'stlar soni va yechib olingan jami UC ko'rsatiladi.
   - PUBG Mobile ID raqamini kiritish va o'zgartirish imkoniyati mavjud.

3. **🛒 UC sotib olish:**
   - Admin kiritgan barcha faol UC tariflari (masalan: 30 UC - 6,000 so'm, 60 UC - 11,000 so'm, va h.k.) ro'yxati chiqadi.
   - Foydalanuvchi akkaunt PUBG ID sini kiritadi (yoki saqlangan ID sini tanlaydi).
   - Admin rekvizitlariga to'lov qilib, chekni (skrinshot) botga yuboradi.
   - Buyurtma adminga rasmi va ma'lumotlari bilan boradi. Admin tasdiqlasa, UC yuboriladi va isbot kanalga e'lon joylanadi.

4. **💰 UC yechib olish:**
   - Foydalanuvchi hisobida minimal yechish miqdori (standart 60 UC) bo'lganda, PUBG ID ga ariza yuborishi mumkin.
   - Ariza adminga boradi. Admin "To'landi" tugmasini bossa, isbot kanalga to'lov posti chiqadi va foydalanuvchiga xabar boradi.

5. **📢 Majburiy obuna va 🧾 Isbot kanal:**
   - Homiy kanallarga obuna tekshiruvi. A'zo bo'lmaguncha botdan foydalana olmaydi (adminlar bundan mustasno).
   - To'langan UC lar va operatsiyalar isbot kanaliga avtomatik yuboriladi.

6. **🗄 Admin Panel (`/admin`):**
   - **Statistika:** Jami foydalanuvchilar, kutilayotgan arizalar, tariflar soni, server yuklanishi.
   - **UC Tariflari:** Yangi UC paketlari va so'mdagi narxlarni kiritish, o'chirish.
   - **Arizalarni boshqarish:** Xarid va Yechish arizalarini bir tugma bilan tasdiqlash yoki rad etish.
   - **Kanallar:** Majburiy obuna kanallarini qo'shish/o'chirish va Isbot kanalini sozlash.
   - **Sozlamalar:** Referal narxi, minimal yechish miqdori, to'lov rekvizitlari, admin username.
   - **Foydalanuvchi nazorati:** ID bo'yicha qidirish, banlash, hisobiga UC qo'shish yoki ayirish.
   - **Xabarnoma (Rassilka):** Barcha foydalanuvchilarga oddiy, forward yoki bitta shaxsga xabar yuborish.
   - **Dizayn va Matnlar:** Botning istalgan matni va tugma nomlarini botning o'zidan o'zgartirish.

---

## 🚀 Ishga Tushirish

```bash
# 1. Virtual muhit va kutubxonalar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Ishga tushirish
python3 main.py
```

Ishga tushganda konsolda quyidagi satr paydo bo'ladi:
```text
Bot muvaffaqiyatli ishga tushdi: @BotUsername
```
Platforma aynan shu satr orqali bot 100% tayyorligini (Readiness Probe) aniqlaydi.
