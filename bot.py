import asyncio
import logging
import os
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

arizalar = {}
ariza_counter = 0

# ============================================================
# MAKTAB MA'LUMOTI
# ============================================================
MAKTAB_MALUMOT = (
    "🏫 Bizning Maktab Haqida\n\n"
    "⭐️ Yaypandagi eng sifatli ta'lim maskani!\n\n"
    "📚 Ixtisoslashgan yo'nalishlar (yuqori sinflar):\n"
    "🩺 Tibbiyot\n"
    "⚖️ Yurisprudensiya\n"
    "💰 Iqtisod\n"
    "💻 IT (Axborot texnologiyalari)\n\n"
    "📞 Aloqa uchun: +998 77 141 20 25"
)

# ============================================================
# STATES
# ============================================================
class Royxat(StatesGroup):
    ism_familya = State()
    sinf = State()
    yonalish = State()
    manzil = State()
    telefon = State()

# ============================================================
# KLAVIATURALAR
# ============================================================
def asosiy_menyu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏫 Maktab haqida ma'lumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="📝 Ro'yxatdan o'tish", callback_data="royxat_boshlash")]
    ])

def sinf_klaviatura():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎒 Boshlang'ich ta'lim (1-4 sinf)", callback_data="sinf_boshlangich")],
        [
            InlineKeyboardButton(text="1-sinf", callback_data="sinf_1"),
            InlineKeyboardButton(text="2-sinf", callback_data="sinf_2"),
            InlineKeyboardButton(text="3-sinf", callback_data="sinf_3"),
        ],
        [
            InlineKeyboardButton(text="4-sinf", callback_data="sinf_4"),
            InlineKeyboardButton(text="5-sinf", callback_data="sinf_5"),
            InlineKeyboardButton(text="6-sinf", callback_data="sinf_6"),
        ],
        [
            InlineKeyboardButton(text="7-sinf", callback_data="sinf_7"),
            InlineKeyboardButton(text="8-sinf", callback_data="sinf_8"),
            InlineKeyboardButton(text="9-sinf", callback_data="sinf_9"),
        ],
        [
            InlineKeyboardButton(text="10-sinf", callback_data="sinf_10"),
            InlineKeyboardButton(text="11-sinf", callback_data="sinf_11"),
        ],
    ])

def yonalish_klaviatura():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🩺 Tibbiyot", callback_data="yon_tibbiyot")],
        [InlineKeyboardButton(text="⚖️ Yurisprudensiya (Huquqshunoslik)", callback_data="yon_huquq")],
        [InlineKeyboardButton(text="💰 Iqtisod", callback_data="yon_iqtisod")],
        [InlineKeyboardButton(text="💻 IT (Axborot texnologiyalari)", callback_data="yon_it")],
        [InlineKeyboardButton(text="📚 Maxsus tayyorgarlik", callback_data="yon_maxsus")],
    ])

def admin_menyu(ariza_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"tasdiq_{ariza_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rad_{ariza_id}")
        ]
    ])

# ============================================================
# WEB SERVER (24/7 uchun)
# ============================================================
async def health(request):
    return web.Response(text="Bot ishlayapti!", status=200)

async def start_web():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Web server port {PORT} da ishga tushdi")

# ============================================================
# /start
# ============================================================
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    ism = message.from_user.first_name or "Foydalanuvchi"
    await message.answer(
        f"👋 Assalomu alaykum, {ism}!\n\n"
        f"Xush kelibsiz! Quyidagi bo'limlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

@dp.message(Command("bekor"))
async def bekor(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if holat:
        await state.clear()
        await message.answer(
            "❌ Ro'yxatdan o'tish bekor qilindi.\n\n🏠 /start",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("⚠️ Hozir aktiv jarayon yo'q. /start bosing.")

@dp.message(Command("statistika"))
async def statistika(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    jami = len(arizalar)
    qabul = sum(1 for a in arizalar.values() if a.get("holat") == "qabul")
    rad = sum(1 for a in arizalar.values() if a.get("holat") == "rad")
    kutilmoqda = sum(1 for a in arizalar.values() if a.get("holat") == "kutilmoqda")
    await message.answer(
        f"📊 Statistika:\n\n"
        f"📋 Jami arizalar: {jami}\n"
        f"✅ Qabul qilingan: {qabul}\n"
        f"❌ Rad etilgan: {rad}\n"
        f"⏳ Kutilmoqda: {kutilmoqda}"
    )

# ============================================================
# MAKTAB MA'LUMOTI
# ============================================================
@dp.callback_query(F.data == "maktab_malumot")
async def maktab_info(callback: types.CallbackQuery):
    await callback.message.answer(MAKTAB_MALUMOT)
    await callback.answer()

# ============================================================
# RO'YXAT — BOSHLASH
# ============================================================
@dp.callback_query(F.data == "royxat_boshlash")
async def royxat_boshlash(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Royxat.ism_familya)
    await callback.message.answer(
        "📝 Ro'yxatdan o'tish boshlandi!\n\n"
        "Bekor qilish uchun /bekor\n\n"
        "1️⃣ Ism va familyangizni kiriting:\n"
        "(Masalan: Aliyev Sardor)",
        reply_markup=ReplyKeyboardRemove()
    )
    await callback.answer()

# ============================================================
# BOSQICH 1 — ISM FAMILYA
# ============================================================
@dp.message(Royxat.ism_familya)
async def ism_olish(message: types.Message, state: FSMContext):
    await state.update_data(ism_familya=message.text)
    await message.answer(
        f"👤 Ism: {message.text}\n\n"
        f"2️⃣ Qaysi sinfda o'qiyapsiz?",
        reply_markup=sinf_klaviatura()
    )
    await state.set_state(Royxat.sinf)

# ============================================================
# BOSQICH 2 — SINF (inline tugmalar)
# ============================================================
@dp.callback_query(Royxat.sinf, F.data.startswith("sinf_"))
async def sinf_olish(callback: types.CallbackQuery, state: FSMContext):
    sinf_map = {
        "sinf_boshlangich": "Boshlang'ich ta'lim (1-4 sinf)",
        "sinf_1": "1-sinf", "sinf_2": "2-sinf", "sinf_3": "3-sinf",
        "sinf_4": "4-sinf", "sinf_5": "5-sinf", "sinf_6": "6-sinf",
        "sinf_7": "7-sinf", "sinf_8": "8-sinf", "sinf_9": "9-sinf",
        "sinf_10": "10-sinf", "sinf_11": "11-sinf",
    }
    sinf = sinf_map.get(callback.data, callback.data)
    await state.update_data(sinf=sinf)
    await callback.message.edit_text(
        f"🎓 Sinf: {sinf}\n\n"
        f"3️⃣ Yo'nalishni tanlang:",
        reply_markup=yonalish_klaviatura()
    )
    await state.set_state(Royxat.yonalish)
    await callback.answer()

# ============================================================
# BOSQICH 3 — YO'NALISH (inline tugmalar)
# ============================================================
@dp.callback_query(Royxat.yonalish, F.data.startswith("yon_"))
async def yonalish_olish(callback: types.CallbackQuery, state: FSMContext):
    yon_map = {
        "yon_tibbiyot": "🩺 Tibbiyot",
        "yon_huquq": "⚖️ Yurisprudensiya (Huquqshunoslik)",
        "yon_iqtisod": "💰 Iqtisod",
        "yon_it": "💻 IT (Axborot texnologiyalari)",
        "yon_maxsus": "📚 Maxsus tayyorgarlik",
    }
    yonalish = yon_map.get(callback.data, callback.data)
    await state.update_data(yonalish=yonalish)
    await callback.message.edit_text(
        f"📌 Yo'nalish: {yonalish}\n\n"
        f"4️⃣ Yashash manzilingizni kiriting:\n"
        f"(Masalan: Farg'ona vil., Yaypon tumani)"
    )
    await state.set_state(Royxat.manzil)
    await callback.answer()

# ============================================================
# BOSQICH 4 — MANZIL
# ============================================================
@dp.message(Royxat.manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(manzil=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(
            text="📱 Telefon raqamni yuborish",
            request_contact=True
        )]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        f"📍 Manzil: {message.text}\n\n"
        f"5️⃣ Siz bilan bog'lanishimiz uchun\n"
        f"telefon raqamingizni yuboring:",
        reply_markup=keyboard
    )
    await state.set_state(Royxat.telefon)

# ============================================================
# BOSQICH 5 — TELEFON + YAKUNLASH
# ============================================================
@dp.message(Royxat.telefon)
async def telefon_olish(message: types.Message, state: FSMContext):
    global ariza_counter

    telefon = message.contact.phone_number if message.contact else message.text
    await state.update_data(telefon=telefon)
    data = await state.get_data()

    user_id = message.from_user.id
    username = message.from_user.username or ""
    ariza_counter += 1
    ariza_id = f"{user_id}_{int(datetime.now().timestamp())}"

    arizalar[ariza_id] = {
        "raqam": ariza_counter,
        "user_id": user_id,
        "username": username,
        "holat": "kutilmoqda",
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
        **data
    }

    # Foydalanuvchiga xabar
    await message.answer(
        f"✅ Arizangiz qabul qilindi!\n\n"
        f"📋 Ariza #{ariza_counter}\n\n"
        f"👤 Ism: {data.get('ism_familya')}\n"
        f"🎓 Sinf: {data.get('sinf')}\n"
        f"📌 Yo'nalish: {data.get('yonalish')}\n"
        f"📍 Manzil: {data.get('manzil')}\n"
        f"📞 Telefon: {telefon}\n\n"
        f"⏳ Arizangiz ko'rib chiqilmoqda.\n"
        f"E'tiboringiz uchun rahmat! 🙏\n\n"
        f"🏠 Bosh menyu: /start",
        reply_markup=ReplyKeyboardRemove()
    )

    # Adminga yuborish
    admin_xabar = (
        f"🔔 YANGI ARIZA #{ariza_counter}\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"👤 Ism Familya: {data.get('ism_familya')}\n"
        f"🎓 Sinf: {data.get('sinf')}\n"
        f"📌 Yo'nalish: {data.get('yonalish')}\n"
        f"📍 Manzil: {data.get('manzil')}\n"
        f"📞 Telefon: {telefon}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"👤 Username: @{username or 'yoq'}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_xabar,
            reply_markup=admin_menyu(ariza_id)
        )
    except Exception as e:
        logging.error(f"Admin xabar xato: {e}")

    await state.clear()

# ============================================================
# ADMIN — QABUL QILISH
# ============================================================
@dp.callback_query(F.data.startswith("tasdiq_"))
async def tasdiqlash(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("tasdiq_", "")
    if ariza_id not in arizalar:
        await callback.answer("⚠️ Ariza topilmadi!", show_alert=True)
        return
    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("⚠️ Bu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    arizalar[ariza_id]["holat"] = "qabul"
    user_id = arizalar[ariza_id]["user_id"]

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ QABUL QILINDI"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 Tabriklaymiz!\n\n"
                 "✅ Arizangiz qabul qilindi!\n"
                 "Tez orada siz bilan bog'lanamiz.\n\n"
                 "📞 +998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("✅ Qabul qilindi!")

# ============================================================
# ADMIN — RAD ETISH
# ============================================================
@dp.callback_query(F.data.startswith("rad_"))
async def rad_etish(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("rad_", "")
    if ariza_id not in arizalar:
        await callback.answer("⚠️ Ariza topilmadi!", show_alert=True)
        return
    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("⚠️ Bu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    arizalar[ariza_id]["holat"] = "rad"
    user_id = arizalar[ariza_id]["user_id"]

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ RAD ETILDI"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="ℹ️ Hurmatli abituriyent!\n\n"
                 "Arizangiz ko'rib chiqildi.\n"
                 "Afsuski, hozircha qabul qilinmadi.\n\n"
                 "Qo'shimcha ma'lumot uchun:\n"
                 "📞 +998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("❌ Rad etildi!")

# ============================================================
# NOTO'G'RI XABAR
# ============================================================
@dp.message()
async def notogri(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if not holat:
        await message.answer(
            "⚠️ Iltimos quyidagi tugmalardan foydalaning.",
            reply_markup=asosiy_menyu()
        )

# ============================================================
# MAIN
# ============================================================
async def main():
    await start_web()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("✅ Bot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
