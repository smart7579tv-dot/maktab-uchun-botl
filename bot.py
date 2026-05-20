import asyncio
import logging
import os
from datetime import datetime
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

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Arizalarni xotirada saqlash (bot ishlayotgan vaqtda)
arizalar = {}

# =====================
# MAKTAB MA'LUMOTI
# =====================
MAKTAB_MALUMOT = """
🏫 *Bizning Maktab Haqida*

⭐️ Yaypandagi eng sifatli ta\'lim maskani!

📚 *Ixtisoslashgan yo\'nalishlar (yuqori sinflar):*
🩺 Tibbiyot
⚖️ Yurisprudensiya
💰 Iqtisod
💻 IT (Axborot texnologiyalari)

📞 *Aloqa uchun:* +998 77 141 20 25
"""

# =====================
# STATES
# =====================
class Royxat(StatesGroup):
    ism_familya = State()
    yashash_manzil = State()
    sinf = State()
    jshir = State()
    ota_ona_tel = State()
    oldingi_maktab = State()

# =====================
# MENYULAR
# =====================
def asosiy_menyu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏫 Maktab haqida ma\'lumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="✅ Maktab o\'quvchisiga aylanish", callback_data="royxat_boshlash")]
    ])

def admin_menyu(ariza_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tasdiq_{ariza_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rad_{ariza_id}")
        ]
    ])

# =====================
# /start
# =====================
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum! Xush kelibsiz!\n\nQuyidagi bo\'limlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

# =====================
# STATISTIKA (faqat admin)
# =====================
@dp.message(Command("statistika"))
async def statistika(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    jami = len(arizalar)
    tasdiqlangan = sum(1 for a in arizalar.values() if a.get("holat") == "tasdiqlandi")
    rad = sum(1 for a in arizalar.values() if a.get("holat") == "rad")
    kutilmoqda = sum(1 for a in arizalar.values() if a.get("holat") == "kutilmoqda")
    await message.answer(
        f"📊 *Statistika:*\n\n"
        f"📋 Jami arizalar: *{jami}*\n"
        f"✅ Tasdiqlangan: *{tasdiqlangan}*\n"
        f"❌ Rad etilgan: *{rad}*\n"
        f"⏳ Kutilmoqda: *{kutilmoqda}*",
        parse_mode="Markdown"
    )

# =====================
# MAKTAB MA'LUMOTI
# =====================
@dp.callback_query(F.data == "maktab_malumot")
async def maktab_info(callback: types.CallbackQuery):
    await callback.message.answer(MAKTAB_MALUMOT, parse_mode="Markdown")
    await callback.answer()

# =====================
# RO'YXAT BOSHLASH
# =====================
@dp.callback_query(F.data == "royxat_boshlash")
async def royxat_boshlash(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 *Ro\'yxatdan o\'tish boshlandi!*\n\n"
        "1️⃣ *Ism va familyangizni* kiriting:\n"
        "_(Masalan: Aliyev Sardor)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.ism_familya)
    await callback.answer()

# =====================
# BOSQICH 1 — ISM FAMILYA
# =====================
@dp.message(Royxat.ism_familya)
async def ism_familya_olish(message: types.Message, state: FSMContext):
    await state.update_data(ism_familya=message.text)
    await message.answer(
        "2️⃣ *Yashash manzilingizni* kiriting:\n"
        "_(Masalan: Farg\'ona vil., Yaypon tumani)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.yashash_manzil)

# =====================
# BOSQICH 2 — MANZIL
# =====================
@dp.message(Royxat.yashash_manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(yashash_manzil=message.text)
    await message.answer(
        "3️⃣ *Nechanchi sinfda o\'qiyapsiz?*\n"
        "_(Masalan: 5, 6, 7, 8, 9, 10, 11)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.sinf)

# =====================
# BOSQICH 3 — SINF
# =====================
@dp.message(Royxat.sinf)
async def sinf_olish(message: types.Message, state: FSMContext):
    await state.update_data(sinf=message.text)
    await message.answer(
        "4️⃣ *Metrika yoki pasport JSHIR raqamingizni* kiriting:\n"
        "_(14 ta raqam)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.jshir)

# =====================
# BOSQICH 4 — JSHIR (tekshiruvsiz, har nima qabul qilsin)
# =====================
@dp.message(Royxat.jshir)
async def jshir_olish(message: types.Message, state: FSMContext):
    await state.update_data(jshir=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "5️⃣ *Ota-onangizning telefon raqamini* yuboring:\n"
        "_(Tugmani bosing yoki qo\'lda kiriting: +998901234567)_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await state.set_state(Royxat.ota_ona_tel)

# =====================
# BOSQICH 5 — TELEFON
# =====================
@dp.message(Royxat.ota_ona_tel)
async def tel_olish(message: types.Message, state: FSMContext):
    telefon = message.contact.phone_number if message.contact else message.text
    await state.update_data(ota_ona_tel=telefon)
    await message.answer(
        "6️⃣ *Hozir qaysi maktabda o\'qiyapsiz?*\n"
        "_(Maktab nomi yoki raqamini kiriting)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.oldingi_maktab)

# =====================
# BOSQICH 6 — OLDINGI MAKTAB + YAKUNLASH
# =====================
@dp.message(Royxat.oldingi_maktab)
async def yakunlash(message: types.Message, state: FSMContext):
    await state.update_data(oldingi_maktab=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or "yoq"

    # Ariza ID yaratish
    ariza_id = f"{user_id}_{int(datetime.now().timestamp())}"

    # Xotirada saqlash
    arizalar[ariza_id] = {
        "user_id": user_id,
        "username": username,
        "holat": "kutilmoqda",
        **data
    }

    # Foydalanuvchiga tasdiqlash
    await message.answer(
        "✅ *Arizangiz qabul qilindi!*\n\n"
        "⏳ Admin ko\'rib chiqadi va tez orada siz bilan bog\'lanadi.\n\n"
        "📞 Savollar uchun: +998 77 141 20 25\n\n"
        "🏠 Bosh menyuga qaytish: /start",
        parse_mode="Markdown"
    )

    # Adminga yuborish
    admin_xabar = (
        f"🔔 *Yangi ariza!*\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"👤 *Ism Familya:* {data.get('ism_familya')}\n"
        f"📍 *Manzil:* {data.get('yashash_manzil')}\n"
        f"🎓 *Sinf:* {data.get('sinf')}\n"
        f"🪪 *JSHIR:* {data.get('jshir')}\n"
        f"📞 *Ota-ona tel:* {data.get('ota_ona_tel')}\n"
        f"🏫 *Oldingi maktab:* {data.get('oldingi_maktab')}\n"
        f"🆔 *Telegram ID:* {user_id}\n"
        f"👤 *Username:* @{username}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_xabar,
            parse_mode="Markdown",
            reply_markup=admin_menyu(ariza_id)
        )
    except Exception as e:
        logging.error(f"Admin xabar xato: {e}")

    await state.clear()

# =====================
# ADMIN TASDIQLASH
# =====================
@dp.callback_query(F.data.startswith("tasdiq_"))
async def tasdiqlash(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("tasdiq_", "")

    if ariza_id in arizalar:
        arizalar[ariza_id]["holat"] = "tasdiqlandi"
        user_id = arizalar[ariza_id]["user_id"]
    else:
        await callback.answer("Ariza topilmadi!")
        return

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ *TASDIQLANDI*",
        parse_mode="Markdown"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 *Tabriklaymiz!*\n\nArizangiz tasdiqlandi!\nTez orada siz bilan bog\'lanamiz.\n\n📞 +998 77 141 20 25",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("✅ Tasdiqlandi!")

# =====================
# ADMIN RAD ETISH
# =====================
@dp.callback_query(F.data.startswith("rad_"))
async def rad_etish(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("rad_", "")

    if ariza_id in arizalar:
        arizalar[ariza_id]["holat"] = "rad"
        user_id = arizalar[ariza_id]["user_id"]
    else:
        await callback.answer("Ariza topilmadi!")
        return

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ *RAD ETILDI*",
        parse_mode="Markdown"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="ℹ️ Arizangiz ko\'rib chiqildi.\n\nAfsuski, hozircha qabul qilinmadi.\nQo\'shimcha ma\'lumot uchun:\n📞 +998 77 141 20 25",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("❌ Rad etildi!")

# =====================
# ISHGA TUSHIRISH
# =====================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
