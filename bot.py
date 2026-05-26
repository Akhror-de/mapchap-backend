import asyncio
import aiosqlite
import aiohttp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- Ключи (на Render – из переменных окружения) ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8829448048:AAGcsoUwczgffKwZrsoRmq8uZ4v0n72vPHc")
YANDEX_SECRET_KEY = os.getenv("YANDEX_SECRET_KEY", "07b74146-5f5a-46bf-a2b1-cf6d052a41bb")
API_URL = os.getenv("API_URL", "https://mapchap-backend.onrender.com/api/add_place")

# ---------- Стоп-слова ----------
STOP_WORDS = [
    # Запрещёнка и наркотики
    "табак", "эскорт", "наркотик", "спайс", "соль", "мефедрон", "гашиш", "марихуана", "кокаин",
    "героин", "амфетамин", "лирика", "снотворное", "закладка", "кладмен",
    # Война, оружие, политика
    "война", "оружие", "автомат", "пистолет", "патрон", "граната", "взрывчатка", "бомба",
    "дрон", "беспилотник", "ввс", "пво", "ракета", "армия", "мобилизация", "повестка",
    "спецоперация", "сво", "уклонист", "диверсант", "шпион", "терракт", "нацист",
    "россия", "украина", "минск", "донбасс", "крым", "санкции", "политика",
    # Финансовые пирамиды
    "заработок без вложений", "пассивный доход", "матрица", "пирамида", "кэшбэк 100%",
    "обнал", "отмывание", "криптовалюта без риска", "халява", "бонус за регистрацию",
    "ставки на спорт договорные",
]

# ---------- Категории (обновлённые) ----------
CATEGORIES = {
    "Салон красоты": "beauty",
    "Автоуслуги": "auto",
    "Медцентр": "med",
    "Аптека": "pharmacy",
    "Магазин одежды": "clothes",
    "Магазин продуктов": "grocery",
    "Магазин техники": "electronics",
    "Магазин бытовой техники": "appliances",
    "Цветочный магазин": "flowers",
    "Ресторан": "restaurant",
    "Кафе": "cafe"
}

# ---------- Бот и диспетчер ----------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------- Состояния FSM ----------
class AddPlace(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_address = State()
    waiting_for_discount = State()
    waiting_for_category = State()

def has_stop_words(text: str) -> bool:
    text_lower = text.lower()
    return any(word in text_lower for word in STOP_WORDS)

# Клавиатура категорий
cat_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cat)] for cat in CATEGORIES.keys()],
    resize_keyboard=True,
    one_time_keyboard=True
)

# ---------- Геокодинг ----------
async def geocode_address(address: str) -> tuple[float, float] | None:
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": YANDEX_SECRET_KEY,
        "geocode": address,
        "format": "json",
        "results": 1
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    members = data['response']['GeoObjectCollection']['featureMember']
                    if members:
                        pos = members[0]['GeoObject']['Point']['pos']
                        lon, lat = map(float, pos.split())
                        return lat, lon
    except Exception as e:
        print(f"Ошибка геокодинга: {e}")
    return None

# ---------- Отправка в API ----------
async def send_place_to_api(data: dict) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=data) as resp:
                if resp.status == 200:
                    return True
                else:
                    print(f"Ошибка отправки: {resp.status}")
                    return False
        except Exception as e:
            print(f"Ошибка соединения с API: {e}")
            return False

# ---------- Хендлеры ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот MapChap.\n"
        "Здесь предприниматели могут добавить своё выгодное предложение на карту.\n"
        "Используй команду /add, чтобы начать."
    )

@dp.message(Command("add"))
async def add_start(message: types.Message, state: FSMContext):
    await state.set_state(AddPlace.waiting_for_name)
    await message.answer("Введите название предложения (например, «Стрижка со скидкой 30%»):")

@dp.message(AddPlace.waiting_for_name)
async def name_entered(message: types.Message, state: FSMContext):
    if has_stop_words(message.text):
        await message.answer("❌ В названии есть запрещённые слова. Попробуйте другое.")
        return
    await state.update_data(name=message.text)
    await state.set_state(AddPlace.waiting_for_description)
    await message.answer("Краткое описание (что именно, условия):")

@dp.message(AddPlace.waiting_for_description)
async def desc_entered(message: types.Message, state: FSMContext):
    if has_stop_words(message.text):
        await message.answer("❌ В описании есть запрещённые слова. Попробуйте другое.")
        return
    await state.update_data(description=message.text)
    await state.set_state(AddPlace.waiting_for_address)
    await message.answer("Введите адрес (улица, дом, город):")

@dp.message(AddPlace.waiting_for_address)
async def address_entered(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(AddPlace.waiting_for_discount)
    await message.answer("Размер скидки или особое условие (например, «30%» или «второй кофе в подарок»):")

@dp.message(AddPlace.waiting_for_discount)
async def discount_entered(message: types.Message, state: FSMContext):
    await state.update_data(discount=message.text)
    await state.set_state(AddPlace.waiting_for_category)
    await message.answer("Выберите категорию:", reply_markup=cat_kb)

@dp.message(AddPlace.waiting_for_category)
async def category_entered(message: types.Message, state: FSMContext):
    if message.text not in CATEGORIES:
        await message.answer("Пожалуйста, выберите категорию кнопкой ниже.")
        return

    data = await state.get_data()
    await message.answer("🔍 Ищу координаты по адресу...")
    lat, lng = await geocode_address(data['address'])
    if lat is None:
        await message.answer("❌ Не удалось определить координаты. Проверьте адрес и попробуйте снова.")
        return

    place_data = {
        "name": data['name'],
        "description": data['description'],
        "discount": data['discount'],
        "category": CATEGORIES[message.text],
        "lat": lat,
        "lng": lng
    }

    success = await send_place_to_api(place_data)
    if success:
        await message.answer(
            "✅ Предложение добавлено! Скоро оно появится на карте MapChap.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "⚠️ Произошла ошибка при сохранении. Попробуйте позже.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    await state.clear()

# ---------- Запуск ----------
async def start_bot():
    """Запускает поллинг бота (используется из api.py)"""
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
