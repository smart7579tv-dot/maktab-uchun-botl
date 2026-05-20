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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

arizalar = {}
ariza_counter = 0

MAKTAB_MALUMOT = (
    "Bizning Maktab Haqida\n\n"
    "Yaypandagi eng sifatli talim maskani!\n\n"
    "Ixtisoslashgan yonalishlar (yuqori sinflar):\n"
    "Tibbiyot\n"
    "Yurisprudensiya\n"
    "Iqtisod\n"
    "IT (Axborot texnologiyalari)\n\n"
    "Aloqa uchun: +998 77 141 20 25"
)

FANLAR_ROYXATI = [
    "Matematika",
    "Kimyo",
    "Biologiya",
    "IT",
    "Ingliz tili",
    "Tarix",
    "Fizika",
    "Ona tili va Adabiyot",
    "Geografiya",
    "Huquq",
    "Iqtisod",
    "Boshqa"
]

class Royxat(StatesGroup):
    ism_familya = State()
    yashash_manzil = State()
    sinf = State()
    jshir = State()
    ota_ona_tel = State()
    fanlar = State()
    oldingi_maktab = State()

def asosiy_menyu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Maktab haqida malumot", callback_data="maktab_malumot")],
        [InlineKeyboardButton(text="Maktab oquvchisiga aylanish", callback_data="royxat_boshlash")]
    ])

def fanlar_klaviatura(tanlangan: list):
    tugmalar = []
    for fan in FANLAR_ROYXATI:
        belgi = "OK " if fan in tanlangan else ""
        tugmalar.append([InlineKeyboardButton(
            text=f"{belgi}{fan}",
            callback_data=f"fan_{fan}"
        )])
    tugmalar.append([InlineKeyboardButton(text="Davom etish", callback_data="fanlar_tayyor")])
    return InlineKeyboardMarkup(inline_keyboard=tugmalar)

def admin_menyu(ariza_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Tasdiqlash", callback_data=f"tasdiq_{ariza_id}"),
            InlineKeyboardButton(text="Rad etish", callback_data=f"rad_{ariza_id}")
        ]
    ])

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    ism = message.from_user.first_name or "Foydalanuvchi"
    await message.answer(
        f"Assalomu alaykum, {ism}!\n\nXush kelibsiz! Quyidagi bolimlardan birini tanlang:",
        reply_markup=asosiy_menyu()
    )

@dp.message(Command("yordam"))
async def yordam(message: types.Message):
    await message.answer(
        "Bot buyruqlari:\n\n"
        "/start - Bosh menyu\n"
        "/yordam - Yordam\n"
        "/bekor - Royxatdan otishni bekor qilish\n\n"
        "Qoshimcha malumot: +998 77 141 20 25"
    )

@dp.message(Command("bekor"))
async def bekor(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if holat:
        await state.clear()
        await message.answer(
            "Royxatdan otish bekor qilindi.\n\nBosh menyu: /start",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer("Hozir aktiv jarayon yoq. /start bosing.")

@dp.message(Command("statistika"))
async def statistika(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    jami = len(arizalar)
    tasdiqlangan = sum(1 for a in arizalar.values() if a.get("holat") == "tasdiqlandi")
    rad = sum(1 for a in arizalar.values() if a.get("holat") == "rad")
    kutilmoqda = sum(1 for a in arizalar.values() if a.get("holat") == "kutilmoqda")
    await message.answer(
        f"Statistika:\n\n"
        f"Jami arizalar: {jami}\n"
        f"Tasdiqlangan: {tasdiqlangan}\n"
        f"Rad etilgan: {rad}\n"
        f"Kutilmoqda: {kutilmoqda}"
    )

@dp.message(Command("arizalar"))
async def barcha_arizalar(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_CHAT_ID):
        return
    if not arizalar:
        await message.answer("Hozircha ariza yoq.")
        return
    matn = "Barcha arizalar:\n\n"
    for a in list(arizalar.values())[-10:]:
        holat = "OK" if a["holat"] == "tasdiqlandi" else "X" if a["holat"] == "rad" else "..."
        matn += f"{holat} {a.get('ism_familya')} | {a.get('sinf')}-sinf | {a.get('ota_ona_tel')}\n"
    matn += "\n(Oxirgi 10 ta korsatildi)"
    await message.answer(matn)

@dp.callback_query(F.data == "maktab_malumot")
async def maktab_info(callback: types.CallbackQuery):
    await callback.message.answer(MAKTAB_MALUMOT)
    await callback.answer()

@dp.callback_query(F.data == "royxat_boshlash")
async def royxat_boshlash(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Royxatdan otish boshlandi!\n\n"
        "Istalgan vaqt /bekor yozib toxtatishingiz mumkin.\n\n"
        "1. Ism va familyangizni kiriting:\n"
        "(Masalan: Aliyev Sardor)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.ism_familya)
    await callback.answer()

@dp.message(Royxat.ism_familya)
async def ism_familya_olish(message: types.Message, state: FSMContext):
    await state.update_data(ism_familya=message.text)
    await message.answer(
        "2. Yashash manzilingizni kiriting:\n"
        "(Masalan: Fargona vil., Yaypon tumani)"
    )
    await state.set_state(Royxat.yashash_manzil)

@dp.message(Royxat.yashash_manzil)
async def manzil_olish(message: types.Message, state: FSMContext):
    await state.update_data(yashash_manzil=message.text)
    await message.answer(
        "3. Nechanchi sinfda oqiyapsiz?\n"
        "(Masalan: 5, 6, 7, 8, 9, 10, 11)"
    )
    await state.set_state(Royxat.sinf)

@dp.message(Royxat.sinf)
async def sinf_olish(message: types.Message, state: FSMContext):
    await state.update_data(sinf=message.text)
    await message.answer(
        "4. Metrika yoki pasport JSHIR raqamingizni kiriting:\n"
        "(14 ta raqam)"
    )
    await state.set_state(Royxat.jshir)

@dp.message(Royxat.jshir)
async def jshir_olish(message: types.Message, state: FSMContext):
    await state.update_data(jshir=message.text)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "5. Ota-onangizning telefon raqamini yuboring:\n"
        "(Tugmani bosing yoki qolda kiriting: +998901234567)",
        reply_markup=keyboard
    )
    await state.set_state(Royxat.ota_ona_tel)

@dp.message(Royxat.ota_ona_tel)
async def tel_olish(message: types.Message, state: FSMContext):
    telefon = message.contact.phone_number if message.contact else message.text
    await state.update_data(ota_ona_tel=telefon, tanlangan_fanlar=[])
    await message.answer(
        "6. Qaysi fanlarni oqimoqchisiz?\n\n"
        "Bir yoki bir nechta fanni tanlang, song Davom etish tugmasini bosing:",
        reply_markup=fanlar_klaviatura([])
    )
    await state.set_state(Royxat.fanlar)

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
    await state.update_data(fanlar=", ".join(tanlangan))
    await callback.message.answer(
        "7. Hozir qaysi maktabda oqiyapsiz?\n"
        "(Maktab nomi yoki raqamini kiriting)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Royxat.oldingi_maktab)
    await callback.answer()

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

    await message.answer(
        f"Arizangiz qabul qilindi!\n\n"
        f"Ariza raqami: #{ariza_counter}\n\n"
        f"Ism: {data.get('ism_familya')}\n"
        f"Manzil: {data.get('yashash_manzil')}\n"
        f"Sinf: {data.get('sinf')}\n"
        f"Fanlar: {data.get('fanlar')}\n"
        f"Oldingi maktab: {data.get('oldingi_maktab')}\n\n"
        f"Admin korib chiqadi va tez orada boglanadi.\n"
        f"Savollar: +998 77 141 20 25\n\n"
        f"/start"
    )

    admin_xabar = (
        f"YANGI ARIZA #{ariza_counter}\n"
        f"{datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Ism Familya: {data.get('ism_familya')}\n"
        f"Manzil: {data.get('yashash_manzil')}\n"
        f"Sinf: {data.get('sinf')}\n"
        f"JSHIR: {data.get('jshir')}\n"
        f"Ota-ona tel: {data.get('ota_ona_tel')}\n"
        f"Fanlar: {data.get('fanlar')}\n"
        f"Oldingi maktab: {data.get('oldingi_maktab')}\n"
        f"Telegram ID: {user_id}\n"
        f"Username: @{username or 'yoq'}"
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

@dp.callback_query(F.data.startswith("tasdiq_"))
async def tasdiqlash(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("tasdiq_", "")
    if ariza_id not in arizalar:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return
    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("Bu ariza allaqachon korib chiqilgan!", show_alert=True)
        return
    arizalar[ariza_id]["holat"] = "tasdiqlandi"
    user_id = arizalar[ariza_id]["user_id"]
    await callback.message.edit_text(callback.message.text + "\n\nTASDIQLANDI")
    try:
        await bot.send_message(
            chat_id=user_id,
            text="Tabriklaymiz!\n\nArizangiz tasdiqlandi!\nTez orada siz bilan boglanamiz.\n\n+998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")
    await callback.answer("Tasdiqlandi!")

@dp.callback_query(F.data.startswith("rad_"))
async def rad_etish(callback: types.CallbackQuery):
    ariza_id = callback.data.replace("rad_", "")
    if ariza_id not in arizalar:
        await callback.answer("Ariza topilmadi!", show_alert=True)
        return
    if arizalar[ariza_id]["holat"] != "kutilmoqda":
        await callback.answer("Bu ariza allaqachon korib chiqilgan!", show_alert=True)
        return
    arizalar[ariza_id]["holat"] = "rad"
    user_id = arizalar[ariza_id]["user_id"]
    await callback.message.edit_text(callback.message.text + "\n\nRAD ETILDI")
    try:
        await bot.send_message(
            chat_id=user_id,
            text="Arizangiz korib chiqildi.\n\nAfsuski, hozircha qabul qilinmadi.\nQoshimcha malumot:\n+998 77 141 20 25"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar xato: {e}")
    await callback.answer("Rad etildi!")

@dp.message()
async def notogri_xabar(message: types.Message, state: FSMContext):
    holat = await state.get_state()
    if not holat:
        await message.answer(
            "Iltimos quyidagi tugmalardan foydalaning.",
            reply_markup=asosiy_menyu()
        )

async def main():
    logging.info("Bot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
