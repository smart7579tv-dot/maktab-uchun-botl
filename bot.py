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
import gspread
from google.oauth2.service_account import Credentials
import json

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")  # JSON string
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# =====================
# GOOGLE SHEETS ULANISH
# =====================
def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDENTIALS)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def sheets_ga_saqlash(data: dict, foydalanuvchi_id: int, username: str):
    try:
        sheet = get_sheet()
        # Agar sarlavha yo'q bo'lsa qo'shish
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Sana":
            sheet.insert_row([
                "Sana", "Ism Familya", "Manzil", "Sinf",
                "JSHIR", "Ota-ona tel", "Oldingi maktab",
                "Telegram ID", "Username", "Holat"
            ], 1)
        row = [
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            data.get("ism_familya", ""),
            data.get("yashash_manzil", ""),
            data.get("sinf", ""),
            data.get("jshir", ""),
            data.get("ota_ona_tel", ""),
            data.get("oldingi_maktab", ""),
            str(foydalanuvchi_id),
            f"@{username}" if username else "yoq",
            "Kutilmoqda"
        ]
        sheet.append_row(row)
        # Yangi qo'shilgan qator raqamini qaytarish
        return sheet.row_count
    except Exception as e:
        logging.error(f"Sheets xato: {e}")
        return None

def sheets_holat_yangilash(row_num: int, holat: str):
    try:
        sheet = get_sheet()
        sheet.update_cell(row_num, 10, holat)
    except Exception as e:
        logging.error(f"Sheets holat yangilash xato: {e}")

def statistika_olish():
    try:
        sheet = get_sheet()
        barcha = sheet.get_all_records()
        jami = len(barcha)
        tasdiqlangan = sum(1 for r in barcha if r.get("Holat") == "Tasdiqlandi ✅")
        rad = sum(1 for r in barcha if r.get("Holat") == "Rad etildi ❌")
        kutilmoqda = sum(1 for r in barcha if r.get("Holat") == "Kutilmoqda")
        return jami, tasdiqlangan, rad, kutilmoqda
    except Exception as e:
        logging.error(f"Statistika xato: {e}")
        return 0, 0, 0, 0

# =====================
# MAKTAB MA'LUMOTI
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
        [InlineKeyboardButton(text="🏫 Maktab haqida ma'lumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="✅ Maktab o'quvchisiga aylanish", callback_data="royxat_boshlash")]
    ])

def admin_menyu(row_num: int, user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"tasdiq_{row_num}_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rad_{row_num}_{user_id}")
        ]
    ])

# =====================
# /start
# =====================
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum! Xush kelibsiz!\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

# =====================
# STATISTIKA (faqat admin)
# =====================
@dp.message(Command("statistika"))
async def statistika(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    jami, tasdiqlangan, rad, kutilmoqda = statistika_olish()
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
        "📝 *Ro'yxatdan o'tish boshlandi!*\n\n"
        "1️⃣ Iltimos, *ism va familyangizni* kiriting:\n"
        "_(Masalan: Aliyev Sardor)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.ism_familya)
    await callback.answer()

@dp.message(Royxat.ism_familya)
async def ism_familya_olish(message: types.Message, state: FSMContext):
    await state.update_data(ism_familya=message.text)
    await message.answer(
        "2️⃣ *Yashash manzilingizni* kiriting:\n"
        "_(Masalan: Farg'ona vil., Yaypon tumani)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.yashash_manzil)

@dp.message(Royxat.yashash_manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(yashash_manzil=message.text)
    await message.answer(
        "3️⃣ *Nechanchi sinfda o'qiyapsiz?*\n"
        "_(Masalan: 5, 6, 7, 8, 9, 10, 11)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.sinf)

@dp.message(Royxat.sinf)
async def sinf_olish(message: types.Message, state: FSMContext):
    await state.update_data(sinf=message.text)
    await message.answer(
        "4️⃣ *Metrika yoki pasport JSHIR raqamingizni* kiriting:\n"
        "_(14 ta raqam)_",
        parse_mode="Markdown"
    )
    await state.set_state(Royxat.jshir)

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

@dp.message(Royxat.ota_ona_tel)
async def tel_olish(message: types.Message, state: FSMContext):
    telefon = message.contact.phone_number if message.contact else message.text.strip()
    await state.update_data(ota_ona_tel=telefon)
    await message.answer(
        "6️⃣ *Hozir qaysi maktabda o'qiyapsiz?*\n"
        "_(Maktab nomi yoki raqamini kiriting)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.oldingi_maktab)

@dp.message(Royxat.oldingi_maktab)
async def yakunlash(message: types.Message, state: FSMContext):
    await state.update_data(oldingi_maktab=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or ""

    # Google Sheets ga saqlash
    row_num = sheets_ga_saqlash(data, user_id, username)

    # Foydalanuvchiga xabar
    await message.answer(
        "✅ *Arizangiz qabul qilindi!*\n\n"
        "⏳ Tez orada admin ko'rib chiqadi va siz bilan bog'lanadi.\n\n"
        "🏠 Bosh menyuga qaytish uchun /start bosing.",
        parse_mode="Markdown"
    )

    # Adminga xabar + tugmalar
    admin_xabar = (
        f"🔔 *Yangi ariza!*\n\n"
        f"👤 *Ism Familya:* {data.get('ism_familya')}\n"
        f"📍 *Manzil:* {data.get('yashash_manzil')}\n"
        f"🎓 *Sinf:* {data.get('sinf')}\n"
        f"🪪 *JSHIR:* {data.get('jshir')}\n"
        f"📞 *Ota-ona tel:* {data.get('ota_ona_tel')}\n"
        f"🏫 *Oldingi maktab:* {data.get('oldingi_maktab')}\n"
        f"🆔 *Telegram ID:* {user_id}\n"
        f"👤 *Username:* @{username or 'yoq'}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_xabar,
            parse_mode="Markdown",
            reply_markup=admin_menyu(row_num, user_id) if row_num else None
        )
    except Exception as e:
        logging.error(f"Admin xabar xato: {e}")

    await state.clear()

# =====================
# ADMIN TASDIQLASH / RAD
# =====================
@dp.callback_query(F.data.startswith("tasdiq_"))
async def tasdiqlash(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    row_num = int(parts[1])
    user_id = int(parts[2])

    sheets_holat_yangilash(row_num, "Tasdiqlandi ✅")

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ *Tasdiqlandi!*",
        parse_mode="Markdown"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 *Tabriklaymiz!*\n\nArizangiz tasdiqlandi! Tez orada siz bilan bog'lanamiz.\n\n📞 Savollar uchun: +998 77 141 20 25",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("✅ Tasdiqlandi!")

@dp.callback_query(F.data.startswith("rad_"))
async def rad_etish(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    row_num = int(parts[1])
    user_id = int(parts[2])

    sheets_holat_yangilash(row_num, "Rad etildi ❌")

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ *Rad etildi!*",
        parse_mode="Markdown"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="ℹ️ Arizangiz ko'rib chiqildi.\n\nAfsuski, hozircha qabul qilinmadi. Qo'shimcha ma'lumot uchun:\n📞 +998 77 141 20 25",
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
