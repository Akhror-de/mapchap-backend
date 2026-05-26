import asyncio
import aiosqlite
import aiohttp
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ---------- Ключи ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8829448048:AAGcsoUwczgffKwZrsoRmq8uZ4v0n72vPHc")
API_URL = os.getenv("API_URL", "https://mapchap-backend.onrender.com/api/add_place")

# ---------- Локализация ----------
LANGUAGES = {
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
    "🇺🇿 O‘zbek": "uz",
    "🇰🇿 Қазақ": "kk",
    "🇰🇬 Кыргызча": "ky",
    "🇹🇯 Тоҷикӣ": "tg"
}

# ---------- Многоязычные стоп-слова ----------
MULTI_LANG_STOP_WORDS = {
    "drugs": {
        "ru": ["наркотик", "спайс", "соль", "мефедрон", "гашиш", "марихуана", "кокаин", "героин", "амфетамин", "лирика", "снотворное", "закладка", "кладмен", "трава", "шишки", "фен", "экстази", "метадон", "опий"],
        "en": ["drugs", "narcotics", "cocaine", "heroin", "weed", "marijuana", "meth", "amphetamine", "ecstasy", "lsd", "opium", "hashish"],
        "uz": ["giyohvand", "narkotik", "kokain", "geroin", "marixuana", "gashish", "opiy", "ekstazi", "metadon", "amfetamin", "spays"],
        "kk": ["есірткі", "наша", "кокаин", "героин", "марихуана", "гашиш", "апиын", "экстази", "метадон", "амфетамин", "спайс"],
        "ky": ["баңгизат", "кокаин", "героин", "марихуана", "гашиш", "опий", "экстази", "метадон", "амфетамин", "спайс", "наша"],
        "tg": ["маводи мухаддир", "кокаин", "героин", "марихуана", "гашиш", "опий", "экстази", "метадон", "амфетамин", "спайс", "нашъа"]
    },
    "weapons": {
        "ru": ["оружие", "автомат", "пистолет", "патрон", "граната", "взрывчатка", "бомба", "ракета", "танк", "пулемет", "снайпер", "калашников"],
        "en": ["weapon", "gun", "rifle", "pistol", "bomb", "explosive", "grenade", "missile", "tank", "sniper", "ak-47"],
        "uz": ["qurol", "avtomat", "to‘pponcha", "granata", "bomba", "raketa", "tank", "snayper", "kalashnikov"],
        "kk": ["қару", "автомат", "тапанша", "граната", "бомба", "зымыран", "танк", "снайпер", "калашников"],
        "ky": ["курал", "автомат", "тапанча", "граната", "бомба", "ракета", "танк", "снайпер", "калашников"],
        "tg": ["силоҳ", "автомат", "таппонча", "граната", "бомба", "ракета", "танк", "снайпер", "калашников"]
    },
    "war_politics": {
        "ru": ["война", "дрон", "беспилотник", "ввс", "пво", "армия", "мобилизация", "повестка", "спецоперация", "сво", "уклонист", "диверсант", "шпион", "терракт", "нацист", "россия", "украина", "минск", "донбасс", "крым", "санкции", "политика"],
        "en": ["war", "drone", "military", "conscription", "special operation", "ukraine", "russia", "nazi", "terrorist", "spy"],
        "uz": ["urush", "dron", "armiya", "mobilizatsiya", "maxsus operatsiya", "ukraina", "rossiya", "natsist", "terrorchi", "josus"],
        "kk": ["соғыс", "дрон", "армия", "мобилизация", "арнайы операция", "украина", "ресей", "нацист", "терроршы", "тыңшы"],
        "ky": ["согуш", "дрон", "армия", "мобилизация", "атайын операция", "украина", "оруссия", "нацист", "террорчу", "тыңчы"],
        "tg": ["ҷанг", "дрон", "армия", "мобилизатсия", "амалиёти махсус", "украина", "россия", "нацист", "террорист", "ҷосус"]
    },
    "adult_content": {
        "ru": ["секс", "порно", "эскорт", "проституция", "интим", "разврат", "гей", "лесбиянки", "транссексуал"],
        "en": ["sex", "porn", "escort", "prostitution", "intimacy", "gay", "lesbian", "transsexual"],
        "uz": ["seks", "porno", "eskort", "fohishalik", "intim", "gomoseksual", "lezbiyanka", "transseksual"],
        "kk": ["секс", "порно", "эскорт", "жезөкшелік", "интим", "гомосексуал", "лезбиянка", "транссексуал"],
        "ky": ["секс", "порно", "эскорт", "сойкулук", "интим", "гомосексуал", "лезбиянка", "транссексуал"],
        "tg": ["секс", "порно", "эскорт", "фоҳишагӣ", "интим", "гомосексуал", "лезбиянка", "транссексуал"]
    },
    "gambling": {
        "ru": ["казино", "ставки", "азартные игры", "букмекер", "тотализатор", "игровые автоматы", "покер", "рулетка"],
        "en": ["casino", "gambling", "betting", "bookmaker", "poker", "roulette", "slot machines"],
        "uz": ["kazino", "qimor", "stavkalar", "bukmeker", "totalizator", "o‘yin avtomatlari", "poker", "ruletka"],
        "kk": ["казино", "құмар ойын", "ставкалар", "букмекер", "тотализатор", "ойын автоматтары", "покер", "рулетка"],
        "ky": ["казино", "кумар оюндары", "ставкалар", "букмекер", "тотализатор", "оюн автоматтары", "покер", "рулетка"],
        "tg": ["казино", "қимор", "ставкаҳо", "букмекер", "тотализатор", "автоматҳои бозӣ", "покер", "рулетка"]
    },
    "financial_fraud": {
        "ru": ["заработок без вложений", "пассивный доход", "матрица", "пирамида", "кэшбэк 100%", "обнал", "отмывание", "криптовалюта без риска", "халява", "бонус за регистрацию", "ставки на спорт договорные"],
        "en": ["pyramid scheme", "no investment income", "passive income scam", "money laundering", "risk free crypto", "free bonus", "fixed matches"],
        "uz": ["piramida sxemasi", "sarmoyasiz daromad", "passiv daromad", "pul yuvish", "xavfsiz kripto", "bepul bonus", "kelishilgan o‘yinlar"],
        "kk": ["пирамидалық схема", "салымсыз табыс", "пассивті кіріс", "ақша жуу", "тәуекелсіз крипто", "тегін бонус", "келісілген ойындар"],
        "ky": ["пирамида схемасы", "салымсыз киреше", "пассивдүү киреше", "акча жуу", "тобокелсиз крипто", "бекер бонус", "келишилген оюндар"],
        "tg": ["схемаи пирамида", "даромади бе сармоя", "даромади пассив", "пулшӯӣ", "криптои бетаваккал", "бонуси ройгон", "бозиҳои созишӣ"]
    }
}

def build_stop_words_dict():
    stop_words_dict = {}
    for category, translations in MULTI_LANG_STOP_WORDS.items():
        for lang, words in translations.items():
            if lang not in stop_words_dict:
                stop_words_dict[lang] = []
            stop_words_dict[lang].extend(words)
    return stop_words_dict

STOP_WORDS_BY_LANG = build_stop_words_dict()

# ---------- Тексты ----------
TEXTS = {
    "choose_language": {
        "ru": "Выберите язык / Choose language:",
        "en": "Choose language:",
        "uz": "Tilni tanlang:",
        "kk": "Тілді таңдаңыз:",
        "ky": "Тилди тандаңыз:",
        "tg": "Забонро интихоб кунед:"
    },
    "start_after_lang": {
        "ru": "👋 Привет! Я бот MapChap.\nДобавь предложение командой /add",
        "en": "👋 Hello! I'm MapChap bot.\nAdd an offer with /add",
        "uz": "👋 Salom! Men MapChap botiman.\nTaklif qo‘shish uchun /add bosing",
        "kk": "👋 Сәлем! Мен MapChap ботымын.\nҰсыныс қосу үшін /add басыңыз",
        "ky": "👋 Салам! Мен MapChap ботмун.\nСунуш кошуу үчүн /add басыңыз",
        "tg": "👋 Салом! Ман MapChap бот.\nБарои илова кардани пешниҳод /add -ро пахш кунед"
    },
    "enter_name": {
        "ru": "Введите название предложения:",
        "en": "Enter the offer name:",
        "uz": "Taklif nomini kiriting:",
        "kk": "Ұсыныстың атауын енгізіңіз:",
        "ky": "Сунуштун атын киргизиңиз:",
        "tg": "Номи пешниҳодро ворид кунед:"
    },
    "enter_description": {
        "ru": "Краткое описание:",
        "en": "Short description:",
        "uz": "Qisqacha tavsif:",
        "kk": "Қысқаша сипаттама:",
        "ky": "Кыскача сүрөттөө:",
        "tg": "Тавсифи кӯтоҳ:"
    },
    "enter_address": {
        "ru": "Введите адрес (улица, дом, город):",
        "en": "Enter address (street, building, city):",
        "uz": "Manzilni kiriting (ko‘cha, uy, shahar):",
        "kk": "Мекенжайды енгізіңіз (көше, үй, қала):",
        "ky": "Дарегиңизди жазыңыз (көчө, үй, шаар):",
        "tg": "Суроғаро ворид кунед (кӯча, хона, шаҳр):"
    },
    "enter_discount": {
        "ru": "Размер скидки или условие:",
        "en": "Discount amount or condition:",
        "uz": "Chegirma miqdori yoki sharti:",
        "kk": "Жеңілдік мөлшері немесе шарты:",
        "ky": "Арзандатуу өлчөмү же шарты:",
        "tg": "Миқдори тахфиф ё шарт:"
    },
    "enter_contact": {
        "ru": "Введите контакт для связи (телефон, @username, ссылка) или нажмите «⏭ Пропустить»:",
        "en": "Enter contact (phone, @username, link) or press '⏭ Skip':",
        "uz": "Aloqa uchun ma'lumot kiriting (telefon, @username, havola) yoki '⏭ O‘tkazib yuborish' tugmasini bosing:",
        "kk": "Байланыс үшін деректер енгізіңіз (телефон, @username, сілтеме) немесе '⏭ Өткізіп жіберу' түймесін басыңыз:",
        "ky": "Байланыш үчүн маалымат жазыңыз (телефон, @username, шилтеме) же '⏭ Өткөрүп жиберүү' баскычын басыңыз:",
        "tg": "Маълумоти тамосро ворид кунед (телефон, @username, истинод) ё тугмаи '⏭ Гузаштан' -ро пахш кунед:"
    },
    "contact_skip_button": {
        "ru": "⏭ Пропустить",
        "en": "⏭ Skip",
        "uz": "⏭ O‘tkazib yuborish",
        "kk": "⏭ Өткізіп жіберу",
        "ky": "⏭ Өткөрүп жиберүү",
        "tg": "⏭ Гузаштан"
    },
    "enter_expiry": {
        "ru": "До какой даты действует предложение? Введи ДД.ММ.ГГГГ ЧЧ:ММ (например, 31.12.2025 23:59)",
        "en": "Until when is the offer valid? Enter DD.MM.YYYY HH:MM (e.g., 31.12.2025 23:59)",
        "uz": "Taklif qachongacha amal qiladi? DD.MM.YYYY HH:MM formatida kiriting (masalan, 31.12.2025 23:59)",
        "kk": "Ұсыныс қай күнге дейін жарамды? DD.MM.YYYY HH:MM форматында енгізіңіз (мысалы, 31.12.2025 23:59)",
        "ky": "Сунуш качанкы чейин жарактуу? DD.MM.YYYY HH:MM форматында жазыңыз (мисалы, 31.12.2025 23:59)",
        "tg": "Пешниҳод то кай сана эътибор дорад? DD.MM.YYYY HH:MM формат ворид кунед (масалан, 31.12.2025 23:59)"
    },
    "wrong_date_format": {
        "ru": "❌ Неверный формат. Введи дату и время как в примере: 31.12.2025 23:59",
        "en": "❌ Wrong format. Enter date and time like in the example: 31.12.2025 23:59",
        "uz": "❌ Noto‘g‘ri format. Sana va vaqtni namunadagidek kiriting: 31.12.2025 23:59",
        "kk": "❌ Қате формат. Күн мен уақытты үлгідегідей енгізіңіз: 31.12.2025 23:59",
        "ky": "❌ Туура эмес формат. Күндү жана убакытты үлгүдөгүдөй жазыңыз: 31.12.2025 23:59",
        "tg": "❌ Формати нодуруст. Сана ва вақтро монанди намуна ворид кунед: 31.12.2025 23:59"
    },
    "choose_category": {
        "ru": "Выберите категорию:",
        "en": "Choose a category:",
        "uz": "Kategoriyani tanlang:",
        "kk": "Санатты таңдаңыз:",
        "ky": "Категорияны тандаңыз:",
        "tg": "Категорияро интихоб кунед:"
    },
    "category_prompt": {
        "ru": "Пожалуйста, выберите категорию кнопкой.",
        "en": "Please choose a category using the button.",
        "uz": "Iltimos, kategoriyani tugma orqali tanlang.",
        "kk": "Өтінемін, санатты түйме арқылы таңдаңыз.",
        "ky": "Сураныч, категорияны баскыч менен тандаңыз.",
        "tg": "Лутфан, категорияро бо тугма интихоб кунед."
    },
    "searching_coords": {
        "ru": "🔍 Ищу координаты...",
        "en": "🔍 Searching for coordinates...",
        "uz": "🔍 Koordinatalarni qidiryapman...",
        "kk": "🔍 Координаттарды іздеу...",
        "ky": "🔍 Координаттарды издеп жатам...",
        "tg": "🔍 Координатаҳоро ҷустуҷӯ мекунам..."
    },
    "coords_not_found": {
        "ru": "❌ Не удалось определить координаты. Проверьте адрес.",
        "en": "❌ Could not determine coordinates. Check the address.",
        "uz": "❌ Koordinatalarni aniqlab bo‘lmadi. Manzilni tekshiring.",
        "kk": "❌ Координаттарды анықтау мүмкін болмады. Мекенжайды тексеріңіз.",
        "ky": "❌ Координаттарды аныктай албадык. Даректи текшериңиз.",
        "tg": "❌ Координатаҳоро муайян карда нашуд. Суроғаро санҷед."
    },
    "offer_added": {
        "ru": "✅ Предложение добавлено! Скоро появится на карте.",
        "en": "✅ Offer added! It will appear on the map soon.",
        "uz": "✅ Taklif qo‘shildi! Tez orada xaritada paydo bo‘ladi.",
        "kk": "✅ Ұсыныс қосылды! Жақында картада пайда болады.",
        "ky": "✅ Сунуш кошулду! Жакында картада пайда болот.",
        "tg": "✅ Пешниҳод илова шуд! Ба наздикӣ дар харита пайдо мешавад."
    },
    "offer_save_error": {
        "ru": "⚠️ Ошибка сохранения. Попробуйте позже.",
        "en": "⚠️ Save error. Try again later.",
        "uz": "⚠️ Saqlashda xatolik. Keyinroq urinib ko‘ring.",
        "kk": "⚠️ Сақтау қатесі. Кейінірек қайталаңыз.",
        "ky": "⚠️ Сактоодо ката. Кийинчерээк кайталаңыз.",
        "tg": "⚠️ Хатои сабт. Баъдтар аз нав кӯшиш кунед."
    },
    "stop_words_warning": {
        "ru": "❌ В тексте есть запрещённые слова. Попробуйте другое.",
        "en": "❌ The text contains forbidden words. Try something else.",
        "uz": "❌ Matnda taqiqlangan so‘zlar bor. Boshqasini kiriting.",
        "kk": "❌ Мәтінде тыйым салынған сөздер бар. Басқасын енгізіңіз.",
        "ky": "❌ Текстте тыюу салынган сөздөр бар. Башкасын жазыңыз.",
        "tg": "❌ Дар матн калимаҳои манъшуда мавҷуданд. Дигареро ворид кунед."
    }
}

# Категории с переводами
CATEGORY_TRANSLATIONS = {
    "beauty": {"ru": "Салон красоты", "en": "Beauty salon", "uz": "Go‘zallik saloni", "kk": "Сұлулық салоны", "ky": "Сулуулук салону", "tg": "Салон зебоӣ"},
    "auto": {"ru": "Автоуслуги", "en": "Auto services", "uz": "Avto xizmatlar", "kk": "Авто қызметтер", "ky": "Авто тейлөө", "tg": "Хидматҳои авто"},
    "med": {"ru": "Медцентр", "en": "Medical center", "uz": "Tibbiy markaz", "kk": "Медициналық орталық", "ky": "Медициналык борбор", "tg": "Маркази тиббӣ"},
    "pharmacy": {"ru": "Аптека", "en": "Pharmacy", "uz": "Dorixona", "kk": "Дәріхана", "ky": "Дарыкана", "tg": "Дорухона"},
    "clothes": {"ru": "Магазин одежды", "en": "Clothing store", "uz": "Kiyim do‘koni", "kk": "Киім дүкені", "ky": "Кийим дүкөнү", "tg": "Мағозаи либос"},
    "grocery": {"ru": "Магазин продуктов", "en": "Grocery store", "uz": "Oziq-ovqat do‘koni", "kk": "Азық-түлік дүкені", "ky": "Азык-түлүк дүкөнү", "tg": "Мағозаи озуқа"},
    "electronics": {"ru": "Магазин техники", "en": "Electronics store", "uz": "Elektronika do‘koni", "kk": "Электроника дүкені", "ky": "Электроника дүкөнү", "tg": "Мағозаи техника"},
    "appliances": {"ru": "Магазин бытовой техники", "en": "Home appliances", "uz": "Maishiy texnika do‘koni", "kk": "Тұрмыстық техника дүкені", "ky": "Тиричилик техникасы дүкөнү", "tg": "Мағозаи техникаи рӯзгор"},
    "flowers": {"ru": "Цветочный магазин", "en": "Flower shop", "uz": "Gul do‘koni", "kk": "Гүл дүкені", "ky": "Гүл дүкөнү", "tg": "Мағозаи гул"},
    "restaurant": {"ru": "Ресторан", "en": "Restaurant", "uz": "Restoran", "kk": "Мейрамхана", "ky": "Ресторан", "tg": "Ресторан"},
    "cafe": {"ru": "Кафе", "en": "Cafe", "uz": "Kafe", "kk": "Кафе", "ky": "Кафе", "tg": "Қаҳвахона"}
}

CATEGORY_CODES = {code for code in CATEGORY_TRANSLATIONS}

# ---------- Бот и диспетчер ----------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

user_language = {}

class AddPlace(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_address = State()
    waiting_for_discount = State()
    waiting_for_contact = State()   # новое состояние
    waiting_for_expiry = State()
    waiting_for_category = State()

def get_lang(message: types.Message) -> str:
    return user_language.get(message.from_user.id, "ru")

def t(lang, key):
    return TEXTS.get(key, {}).get(lang, TEXTS[key].get("ru", key))

def has_stop_words(text: str, lang: str = "ru") -> bool:
    text_lower = text.lower()
    langs_to_check = {lang, "ru", "en"}
    for lng in langs_to_check:
        if lng in STOP_WORDS_BY_LANG:
            for word in STOP_WORDS_BY_LANG[lng]:
                if word in text_lower:
                    return True
    return False

# ---------- Клавиатуры ----------
def language_keyboard():
    buttons = [[KeyboardButton(text=lang_name)] for lang_name in LANGUAGES.keys()]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def category_keyboard(lang):
    buttons = []
    for code in CATEGORY_CODES:
        label = CATEGORY_TRANSLATIONS[code].get(lang, CATEGORY_TRANSLATIONS[code]["ru"])
        buttons.append([KeyboardButton(text=label)])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def contact_skip_keyboard(lang):
    skip_text = TEXTS["contact_skip_button"][lang]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=skip_text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ---------- Геокодинг ----------
async def geocode_address(address: str) -> tuple[float, float] | None:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "accept-language": "ru"}
    headers = {"User-Agent": "MapChapBot/1.0 (khabibullaevakhrorjon@gmail.com)"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data:
                        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"Ошибка геокодинга: {e}")
    return None

async def send_place_to_api(data: dict) -> bool:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=data) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"Ошибка соединения с API: {e}")
            return False

# ---------- Хендлеры ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(TEXTS["choose_language"]["ru"], reply_markup=language_keyboard())

@dp.message(lambda msg: msg.text in LANGUAGES)
async def language_chosen(message: types.Message, state: FSMContext):
    lang = LANGUAGES[message.text]
    user_language[message.from_user.id] = lang
    await message.answer(t(lang, "start_after_lang"), reply_markup=types.ReplyKeyboardRemove())
    await message.answer("Используйте /add")

@dp.message(Command("add"))
async def add_start(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    await state.set_state(AddPlace.waiting_for_name)
    await message.answer(t(lang, "enter_name"))

@dp.message(AddPlace.waiting_for_name)
async def name_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    if has_stop_words(message.text, lang):
        await message.answer(t(lang, "stop_words_warning"))
        return
    await state.update_data(name=message.text)
    await state.set_state(AddPlace.waiting_for_description)
    await message.answer(t(lang, "enter_description"))

@dp.message(AddPlace.waiting_for_description)
async def desc_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    if has_stop_words(message.text, lang):
        await message.answer(t(lang, "stop_words_warning"))
        return
    await state.update_data(description=message.text)
    await state.set_state(AddPlace.waiting_for_address)
    await message.answer(t(lang, "enter_address"))

@dp.message(AddPlace.waiting_for_address)
async def address_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    await state.update_data(address=message.text)
    await state.set_state(AddPlace.waiting_for_discount)
    await message.answer(t(lang, "enter_discount"))

@dp.message(AddPlace.waiting_for_discount)
async def discount_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    await state.update_data(discount=message.text)
    await state.set_state(AddPlace.waiting_for_contact)
    await message.answer(t(lang, "enter_contact"), reply_markup=contact_skip_keyboard(lang))

@dp.message(AddPlace.waiting_for_contact)
async def contact_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    skip_text = TEXTS["contact_skip_button"][lang]
    if message.text == skip_text:
        contact = None
    else:
        contact = message.text.strip()
    await state.update_data(contact=contact)
    await state.set_state(AddPlace.waiting_for_expiry)
    await message.answer(t(lang, "enter_expiry"), reply_markup=types.ReplyKeyboardRemove())

@dp.message(AddPlace.waiting_for_expiry)
async def expiry_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    try:
        expiry = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        expiry_iso = expiry.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        await message.answer(t(lang, "wrong_date_format"))
        return
    await state.update_data(expiry=expiry_iso)
    await state.set_state(AddPlace.waiting_for_category)
    await message.answer(t(lang, "choose_category"), reply_markup=category_keyboard(lang))

@dp.message(AddPlace.waiting_for_category)
async def category_entered(message: types.Message, state: FSMContext):
    lang = get_lang(message)
    cat_code = None
    for code in CATEGORY_CODES:
        if CATEGORY_TRANSLATIONS[code].get(lang) == message.text:
            cat_code = code
            break
    if cat_code is None:
        await message.answer(t(lang, "category_prompt"))
        return

    data = await state.get_data()
    await message.answer(t(lang, "searching_coords"))
    lat, lng = await geocode_address(data['address'])
    if lat is None:
        await message.answer(t(lang, "coords_not_found"))
        return

    place_data = {
        "name": data['name'],
        "description": data['description'],
        "discount": data['discount'],
        "contact": data.get('contact'),  # может быть None
        "expiry": data['expiry'],
        "category": cat_code,
        "lat": lat,
        "lng": lng
    }

    success = await send_place_to_api(place_data)
    if success:
        await message.answer(t(lang, "offer_added"), reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer(t(lang, "offer_save_error"), reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

async def start_bot():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())
