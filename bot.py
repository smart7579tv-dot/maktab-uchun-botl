import asyncio
import logging
import os
import json
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

arizalar = {}
ariza_counter = 0

# =====================
# GOOGLE SHEETS
# =====================
def get_sheet():
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).sheet1
    except Exception as e:
        logging.error(f"Google Sheets ulanish xato: {e}")
        return None

def sheets_sarlavha(sheet):
    try:
        if sheet.cell(1, 1).value != "№":
            sheet.insert_row([
                "№", "Sana", "Ism Familya", "Manzil", "Sinf",
                "JSHIR", "Ota-ona tel", "Fanlar", "Oldingi maktab",
                "Telegram ID", "Username", "Holat"
            ], 1)
    except Exception as e:
        logging.error(f"Sarlavha xato: {e}")

def sheets_ga_saqlash(data: dict, user_id: int, username: str, raqam: int):
    try:
        sheet = get_sheet()
        if not sheet:
            return None
        sheets_sarlavha(sheet)
        row = [
            raqam,
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            data.get("ism_familya", ""),
            data.get("yashash_manzil", ""),
            data.get("sinf", ""),
            data.get("jshir", ""),
            data.get("ota_ona_tel", ""),
            data.get("fanlar", ""),
            data.get("oldingi_maktab", ""),
            str(user_id),
            f"@{username}" if username else "yoq",
            "Kutilmoqda"
        ]
        sheet.append_row(row)
        return sheet.row_count
    except Exception as e:
        logging.error(f"Sheets saqlash xato: {e}")
        return None

def sheets_holat_yangilash(row_num: int, holat: str):
    try:
        sheet = get_sheet()
        if sheet:
            sheet.update_cell(row_num, 12, holat)
    except Exception as e:
        logging.error(f"Sheets holat xato: {e}")

# =====================
# MAKTAB MA'LUMOTI
# =====================
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

FANLAR_ROYXATI = [
    "📐 Matematika",
    "⚗️ Kimyo",
    "🧬 Biologiya",
    "💻 IT",
    "🌍 Ingliz tili",
    "📜 Tarix",
    "⚡ Fizika",
    "📖 Ona tili va Adabiyot",
    "🌐 Geografiya",
    "🏛️ Huquq",
    "💰 Iqtisod",
    "🎨 Boshqa"
]

# =====================
# STATES
# =====================
class Royxat(StatesGroup):
    ism_familya = State()
    yashash_manzil = State()
    sinf = State()
    jshir = State()
    ota_ona_tel = State()
    fanlar = State()
    oldingi_maktab = State()

# =====================
# KLAVIATURALAR
# =====================
def asosiy_menyu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏫 Maktab haqida ma'lumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="✅ Maktab o'quvchisiga aylanish", callback_data="royxat_boshlash")]
    ])

def fanlar_klaviatura(tanlangan: list):
    tugmalar = []
    for fan in FANLAR_ROYXATI:
        belgi = "✅ " if fan in tanlangan else ""
        tugmalar.append([InlineKeyboardButton(
            text=f"{belgi}{fan}",
            callback_data=f"fan_{fan}"
        )])
    tugmalar.append([InlineKeyboardButton(text="➡️ Davom etish", callback_data="fanlar_tayyor")])
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

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
    ism = message.from_user.first_name or "Foydalanuvchi"
    await message.answer(
        f"👋 Assalomu alaykum, {ism}!\n\nXush kelibsiz! Quyidagi bo'limlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

# =====================
# YORDAM
# =====================
@dp.message(Command("yordam"))
async def yordam(message: types.Message):
    await message.answer(
        "ℹ️ Bot buyruqlari:\n\n"
        "/start — Bosh menyu\n"
        "/yordam — Yordam\n"
        "/bekor — Ro'yxatdan o'tishni bekor qilish\n\n"
        "📞 Qo'shimcha ma'lumot: +998 77 141 20 25"
    )

# =====================
# BEKOR QILISH
# =====================
@dp.message(Command("bekor"))
async def bekor(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if holat:
        await state.clear()
        await message.answer(
            "❌ Ro'yxatdan o'tish bekor qilindi.\n\n🏠 Bosh menyu: /start",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Hozir aktiv jarayon yo'q. /start bosing.")

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
        f"📊 Statistika:\n\n"
        f"📋 Jami arizalar: {jami}\n"
        f"✅ Tasdiqlangan: {tasdiqlangan}\n"
        f"❌ Rad etilgan: {rad}\n"
        f"⏳ Kutilmoqda: {kutilmoqda}"
    )

# =====================
# BARCHA ARIZALAR (faqat admin)
# =====================
@dp.message(Command("arizalar"))
async def barcha_arizalar(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    if not arizalar:
        await message.answer("Hozircha ariza yo'q.")
        return
    matn = "📋 Barcha arizalar:\n\n"
    for ariza_id, a in list(arizalar.items())[-10:]:
        holat_belgi = "✅" if a["holat"] == "tasdiqlandi" else "❌" if a["holat"] == "rad" else "⏳"
        matn += f"{holat_belgi} {a.get('ism_familya')} | {a.get('sinf')}-sinf | {a.get('ota_ona_tel')}\n"
    matn += "\n(Oxirgi 10 ta ko'rsatildi)"
    await message.answer(matn)

# =====================
# MAKTAB MA'LUMOTI
# =====================
@dp.callback_query(F.data == "maktab_malumot")
async def maktab_info(callback: types.CallbackQuery):
    await callback.message.answer(MAKTAB_MALUMOT)
    await callback.answer()

# =====================
# RO'YXAT — BOSHLASH
# =====================
@dp.callback_query(F.data == "royxat_boshlash")
async def royxat_boshlash(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Ro'yxatdan o'tish boshlandi!\n\n"
        "Istalgan vaqt /bekor yozib to'xtatishingiz mumkin.\n\n"
        "1️⃣ Ism va familyangizni kiriting:\n"
        "(Masalan: Aliyev Sardor)",
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
        "2️⃣ Yashash manzilingizni kiriting:\n"
        "(Masalan: Farg'ona vil., Yaypon tumani)"
    )
    await state.set_state(Royxat.yashash_manzil)

# =====================
# BOSQICH 2 — MANZIL
# =====================
@dp.message(Royxat.yashash_manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(yashash_manzil=message.text)
    await message.answer(
        "3️⃣ Nechanchi sinfda o'qiyapsiz?\n"
        "(Masalan: 5, 6, 7, 8, 9, 10, 11)"
    )
    await state.set_state(Royxat.sinf)

# =====================
# BOSQICH 3 — SINF
# =====================
@dp.message(Royxat.sinf)
async def sinf_olish(message: types.Message, state: FSMContext):
    await state.update_data(sinf=message.text)
    await message.answer(
        "4️⃣ Metrika yoki pasport JSHIR raqamingizni kiriting:\n"
        "(14 ta raqam)"
    )
    await state.set_state(Royxat.jshir)

# =====================
# BOSQICH 4 — JSHIR
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
        "5️⃣ Ota-onangizning telefon raqamini yuboring:\n"
        "(Tugmani bosing yoki qo'lda kiriting: +998901234567)",
        reply_markup=keyboard
    )
    await state.set_state(Royxat.ota_ona_tel)

# =====================
# BOSQICH 5 — TELEFON
# =====================
@dp.message(Royxat.ota_ona_tel)
async def tel_olish(message: types.Message, state: FSMContext):
    telefon = message.contact.phone_number if message.contact else message.text
    await state.update_data(ota_ona_tel=telefon, tanlangan_fanlar=[])
    await message.answer(
        "6️⃣ Qaysi fanlarni o'qimoqchisiz?\n\n"
        "Bir yoki bir nechta fanni tanlang, so'ng 'Davom etish' tugmasini bosing:",
        reply_markup=fanlar_klaviatura([]),
        reply_markup_remove=None
    )
    await state.set_state(Royxat.fanlar)

# =====================
# BOSQICH 6 — FANLAR TANLASH
# =====================
@dp.callback_query(Royxat.fanlar, F.data.startswith("fan_"))
async def fan_tanlash(callback: types.CallbackQuery, state: FSMContext):
    fan = callback.data.replace("fan_", "")
    data = await state.get_data()
    tanlangan = data.get("tanlangan_fanlar", [])

    if fan in tanlangan:
        tanlangan.remove(fan)
    else:
        tanlangan.append(fan)

    await state.update_data(tanlangan_fanlar=tanlangan)
    await callback.message.edit_reply_markup(reply_markup=fanlar_klaviatura(tanlangan))
    await callback.answer()

@dp.callback_query(Royxat.fanlar, F.data == "fanlar_tayyor")
async def fanlar_tayyor(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tanlangan = data.get("tanlangan_fanlar", [])

    if not tanlangan:
        await callback.answer("Kamida 1 ta fan tanlang!", show_alert=True)
        return

    fanlar_matn = ", ".join(tanlangan)
    await state.update_data(fanlar=fanlar_matn)

    await callback.message.answer(
        "7️⃣ Hozir qaysi maktabda o'qiyapsiz?\n"
        "(Maktab nomi yoki raqamini kiriting)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.oldingi_maktab)
    await callback.answer()

# =====================
# BOSQICH 7 — OLDINGI MAKTAB + YAKUNLASH
# =====================
@dp.message(Royxat.oldingi_maktab)
async def yakunlash(message: types.Message, state: FSMContext):
    global ariza_counter
    await state.update_data(oldingi_maktab=message.text)
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

    # Google Sheets ga saqlash
    row_num = sheets_ga_saqlash(data, user_id, username, ariza_counter)

    # Foydalanuvchiga xulosa
    fanlar_matn = data.get("fanlar", "")
    await message.answer(
        f"✅ Arizangiz qabul qilindi!\n\n"
        f"📋 Ariza raqami: #{ariza_counter}\n\n"
        f"👤 Ism: {data.get('ism_familya')}\n"
        f"📍 Manzil: {data.get('yashash_manzil')}\n"
        f"🎓 Sinf: {data.get('sinf')}\n"
        f"📚 Fanlar: {fanlar_matn}\n"
        f"🏫 Oldingi maktab: {data.get('oldingi_maktab')}\n\n"
        f"⏳ Admin ko'rib chiqadi va tez orada bog'lanadi.\n"
        f"📞 Savollar: +998 77 141 20 25\n\n"
        f"🏠 /start"
    )

    # Adminga yuborish
    admin_xabar = (
        f"🔔 YANGI ARIZA #{ariza_counter}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"👤 Ism Familya: {data.get('ism_familya')}\n"
        f"📍 Manzil: {data.get('yashash_manzil')}\n"
        f"🎓 Sinf: {data.get('sinf')}\n"
        f"🪪 JSHIR: {data.get('jshir')}\n"
        f"📞 Ota-ona tel: {data.get('ota_ona_tel')}\n"
        f"📚 Fanlar: {fanlar_matn}\n"
        f"🏫 Oldingi maktab: {data.get('oldingi_maktab')}\n"
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

# =====================
# ADMIN — TASDIQLASH
# =====================
@dp.callback_query(F.data.startswith("tasdiq_"))
async def tasdiqlash(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("tasdiq_", "")

    if ariza_id not in arizalar:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("Bu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    arizalar[ariza_id]["holat"] = "tasdiqlandi"
    user_id = arizalar[ariza_id]["user_id"]
    row_num = arizalar[ariza_id].get("row_num")

    if row_num:
        sheets_holat_yangilash(row_num, "Tasdiqlandi ✅")

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ TASDIQLANDI"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="🎉 Tabriklaymiz!\n\n"
                 "Arizangiz tasdiqlandi!\n"
                 "Tez orada siz bilan bog'lanamiz.\n\n"
                 "📞 +998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("✅ Tasdiqlandi!")

# =====================
# ADMIN — RAD ETISH
# =====================
@dp.callback_query(F.data.startswith("rad_"))
async def rad_etish(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("rad_", "")

    if ariza_id not in arizalar:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return

    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("Bu ariza allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    arizalar[ariza_id]["holat"] = "rad"
    user_id = arizalar[ariza_id]["user_id"]
    row_num = arizalar[ariza_id].get("row_num")

    if row_num:
        sheets_holat_yangilash(row_num, "Rad etildi ❌")

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ RAD ETILDI"
    )

    try:
        await bot.send_message(
            chat_id=user_id,
            text="ℹ️ Arizangiz ko'rib chiqildi.\n\n"
                 "Afsuski, hozircha qabul qilinmadi.\n"
                 "Qo'shimcha ma'lumot uchun:\n"
                 "📞 +998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")

    await callback.answer("❌ Rad etildi!")

# =====================
# NOTO'G'RI XABAR
# =====================
@dp.message()
async def notogri_xabar(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if not holat:
        await message.answer(
            "Iltimos quyidagi tugmalardan foydalaning.",
            reply_markup=asosiy_menyu()
        )

# =====================
# ISHGA TUSHIRISH
# =====================
async def main():
    logging.info("Bot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
