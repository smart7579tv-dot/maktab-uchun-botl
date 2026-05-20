import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

logging.basicConfig(level=logging.INFO)

# Atrof-muhit o'zgaruvchilarini olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# =====================
# MAKTAB HAQIDA MA'LUMOT
# =====================
MAKTAB_MALUMOT = """
🏫 *Bizning Maktab Haqida*

⭐️ Yaypandagi eng sifatli ta'lim maskani!

📚 *Ixtisoslashgan yo'nalishlar (yuqori sinflar):*
🩺 Tibbiyot
⚖️ Yurisprudensiya
💰 Iqtisod
💻 IT (Axborot texnologiyalari)

📞 *Aloqa uchun:* +998 77 141 20 25
"""

# =====================
# STATES (ro'yxatdan o'tish bosqichlari)
# =====================
class Royxat(StatesGroup):
    ism_familya = State()
    yashash_manzil = State()
    sinf = State()
    jshir = State()
    ota_ona_tel = State()
    oldingi_maktab = State()

# =====================
# ASOSIY MENYU
# =====================
def asosiy_menyu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏫 Maktab haqida ma'lumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="✅ Maktab o'quvchisiga aylanish", callback_data="royxat_boshlash")]
    ])
    return keyboard

# =====================
# /start KOMANDASI
# =====================
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum! Xush kelibsiz!\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

# =====================
# MAKTAB HAQIDA MA'LUMOT
# =====================
@dp.callback_query(F.data == "maktab_malumot")
async def maktab_info(callback: types.CallbackQuery):
    await callback.message.answer(MAKTAB_MALUMOT, parse_mode="Markdown")
    await callback.answer()

# =====================
# RO'YXATDAN O'TISH BOSHLASH
# =====================
@dp.callback_query(F.data == "royxat_boshlash")
async def royxat_boshlash(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 *Ro'yxatdan o'tish boshlandi!*\n\n"
        "1️⃣ Iltimos, *ism va familyangizni* kiriting:\n"
        "_(Masalan: Aliyev Sardor)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.ism_familya)
    await callback.answer()

# =====================
# ISM FAMILYA
# =====================
@dp.message(Royxat.ism_familya)
async def ism_familya_olish(message: types.Message, state: FSMContext):
    await state.update_data(ism_familya=message.text)
    await message.answer(
        "2️⃣ *Yashash manzilingizni* kiriting:\n"
        "_(Masalan: Toshkent sh., Yunusobod tumani, ...)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.yashash_manzil)

# =====================
# YASHASH MANZIL
# =====================
@dp.message(Royxat.yashash_manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(yashash_manzil=message.text)
    await message.answer(
        "3️⃣ *Nechanchi sinfda o'qiyapsiz?*\n"
        "_(Masalan: 5, 6, 7, 8, 9, 10, 11)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.sinf)

# =====================
# SINF
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
# JSHIR
# =====================
@dp.message(Royxat.jshir)
async def jshir_olish(message: types.Message, state: FSMContext):
    jshir = message.text.strip()
    if not jshir.isdigit() or len(jshir) != 14:
        await message.answer("❌ JSHIR 14 ta raqamdan iborat bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(jshir=jshir)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "5️⃣ *Ota-onangizning telefon raqamini* yuboring:\n"
        "_(Tugmani bosing yoki qo'lda kiriting: +998901234567)_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await state.set_state(Royxat.ota_ona_tel)

# =====================
# OTA-ONA TELEFON
# =====================
@dp.message(Royxat.ota_ona_tel)
async def tel_olish(message: types.Message, state: FSMContext):
    if message.contact:
        telefon = message.contact.phone_number
    else:
        telefon = message.text.strip()
    
    await state.update_data(ota_ona_tel=telefon)
    await message.answer(
        "6️⃣ *Hozir qaysi maktabda o'qiyapsiz?*\n"
        "_(Maktab nomi yoki raqamini kiriting)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.oldingi_maktab)

# =====================
# OLDINGI MAKTAB VA YAKUNLASH
# =====================
@dp.message(Royxat.oldingi_maktab)
async def yakunlash(message: types.Message, state: FSMContext):
    await state.update_data(oldingi_maktab=message.text)
    data = await state.get_data()

    await message.answer(
        "✅ *Ro'yxatdan o'tdingiz!*\n\n"
        "Ma'lumotlaringiz qabul qilindi. Tez orada siz bilan bog'lanamiz!\n\n"
        "🏠 Bosh menyuga qaytish uchun /start bosing.",
        parse_mode="Markdown"
    )

    admin_xabar = (
        f"🔔 *Yangi ariza!*\n\n"
        f"👤 *Ism Familya:* {data.get('ism_familya')}\n"
        f"📍 *Manzil:* {data.get('yashash_manzil')}\n"
        f"🎓 *Sinf:* {data.get('sinf')}\n"
        f"🪪 *JSHIR:* {data.get('jshir')}\n"
        f"📞 *Ota-ona tel:* {data.get('ota_ona_tel')}\n"
        f"🏫 *Oldingi maktab:* {data.get('oldingi_maktab')}\n"
        f"🆔 *Telegram ID:* {message.from_user.id}\n"
        f"👤 *Username:* @{message.from_user.username or 'yoq'}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_xabar,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Admin xabar yuborishda xato: {e}")

    await state.clear()

# =====================
# BOTNI ISHGA TUSHIRISH
# =====================
async def main():
    # Eski xabarlarni o'chirib yuborish (Render qayta yonganda eski so'rovlar tiqilib qolmasligi uchun)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
