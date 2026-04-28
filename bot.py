import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "ramis_zz").strip().lstrip("@")

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN. Укажите токен в переменных Railway или в .env")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

ANSWERS_PATH = os.path.join(os.getcwd(), "data", "answers.json")

with open(ANSWERS_PATH, "r", encoding="utf-8") as f:
    ANSWERS: Dict[str, str] = json.load(f)

# Структура меню. Если нужно добавить пункт — добавляете название и ID ответа.
TOPICS: Dict[str, Dict[str, int]] = {
    "🌐 Миграционные вопросы": {
        "Гражданство РФ": 1,
        "Виза в РФ": 2,
        "Пребывание иностранцев": 3,
        "Выезд из РФ": 4,
        "Нарушение правил": 5,
        "ВНЖ": 6,
    },
    "📄 Гражданское право": {
        "Имущественные отношения": 7,
        "Договоры": 8,
        "Взыскание долгов": 9,
        "Расторжение договора": 10,
        "Изменение договора": 11,
    },
    "👨‍👩‍👧 Семейное право": {
        "Развод": 12,
        "Раздел имущества": 13,
        "Уменьшение алиментов": 14,
        "Увеличение алиментов": 15,
    },
    "🪖 СВО": {
        "Нет выплат по контракту": 21,
        "Мобилизация": 22,
        "Категория годности ВВК": 23,
        "Увольнение участника СВО": 24,
        "Выплаты за ранение": 25,
        "Отпуск участникам СВО": 26,
        "СВО из мест лишения свободы": 27,
        "Льготы участникам СВО": 28,
    },
    "🧾 Пенсии": {
        "ИПК": 29,
        "Перерасчет пенсии": 30,
        "Досрочная пенсия": 31,
        "Работающий пенсионер": 32,
        "Расчет пенсии": 33,
    },
    "💳 Долги и кредиты": {
        "Коллекторы": 34,
        "Банк подал в суд": 35,
        "Законное списание долгов": 36,
        "Уменьшение долга": 37,
        "Аресты и ограничения": 38,
        "Кредит, который не брали": 39,
    },
    "💼 Трудовые споры": {
        "Незаконное увольнение": 40,
        "Не платят зарплату": 41,
        "Понижение в должности": 42,
        "Восстановление на работе": 43,
        "Спор с работодателем": 44,
        "Отработка перед увольнением": 45,
        "Сверхурочные": 75,
        "Принуждение к увольнению": 76,
        "Дискриминация": 77,
    },
    "🏠 Недвижимость и жильё": {
        "Договор аренды": 46,
        "Оспаривание купли-продажи": 47,
        "Возврат залога": 48,
        "Выселение жильцов": 49,
        "Перепланировка": 50,
    },
    "📜 Наследство": {
        "Вступление в наследство": 51,
        "Оспаривание завещания": 52,
        "Наследство с долгами": 53,
        "Срок вступления": 54,
        "Фактическое принятие": 55,
    },
    "🚗 ДТП и страховые споры": {
        "Страховые выплаты": 56,
        "Что делать при ДТП": 57,
        "Взыскание ущерба": 58,
        "Повредили авто на улице": 59,
        "Навязанные услуги автосалона": 60,
    },
    "🌳 Земельное право": {
        "Аренда земли у государства": 61,
        "Купля-продажа участка": 62,
        "Межевание": 63,
        "Ограничения на участок": 64,
        "Узаконивание участка": 65,
        "Сосед захватил участок": 66,
    },
    "🤝 Социальные вопросы": {
        "Невыплата пособий": 67,
        "Задержка соцвыплат": 68,
        "Оформление инвалидности": 69,
        "Льготы для инвалидов": 70,
        "Трудоустройство инвалидов": 71,
        "Доступная среда": 72,
        "Жилье нуждающимся": 73,
        "Соцобслуживание на дому": 74,
    },
    "🏥 Медицина": {
        "Полис ОМС": 81,
        "Отказ в лечении": 82,
        "Врачебная ошибка": 83,
        "Бесплатные лекарства": 84,
        "Диспансеризация": 85,
    },
    "👶 Декрет и выплаты": {
        "Пособие по беременности и родам": 86,
        "Пособие до 1,5 лет": 87,
        "Единовременное пособие": 88,
        "Материнский капитал": 89,
    },
}


CASE_TEXTS: Dict[str, str] = {
    "case_drugs": (
        "🚔 <b>Меня остановили с наркотиками</b>\n\n"
        "Не давайте объяснений без адвоката. Вы вправе ссылаться на ст. 51 Конституции РФ и не свидетельствовать против себя.\n\n"
        "Не признавайте ничего “на словах”, внимательно проверяйте протокол, место, время, что именно изъято, кто присутствовал.\n\n"
        "⚠️ Важно: квалификация зависит от количества, упаковки, переписки, показаний и других обстоятельств."
    ),
    "case_police": (
        "👮‍♂️ <b>Меня вызывают в полицию</b>\n\n"
        "Сначала уточните, в каком статусе вас вызывают: свидетель, подозреваемый, потерпевший или для дачи объяснений.\n\n"
        "Не стоит идти “просто поговорить” без понимания ситуации. Любые объяснения могут попасть в материалы проверки или дела.\n\n"
        "⚠️ Перед визитом лучше определить позицию и понять, нужен ли адвокат."
    ),
    "case_police_call": (
        "📞 <b>Позвонили из полиции — что делать</b>\n\n"
        "Не сообщайте по телефону лишние данные и не давайте объяснений по существу. Уточните ФИО сотрудника, отдел, причину вызова.\n\n"
        "Попросите направить официальную повестку или сообщение с данными подразделения.\n\n"
        "⚠️ Срочные просьбы “приехать прямо сейчас” часто используются как психологическое давление."
    ),
    "case_search": (
        "🏠 <b>Пришли с обыском</b>\n\n"
        "Попросите предъявить постановление и документы сотрудников. Не препятствуйте, но внимательно фиксируйте происходящее.\n\n"
        "Следите, что именно изымают и где это якобы найдено. В протоколе можно писать замечания.\n\n"
        "⚠️ Нарушения при обыске могут иметь значение для защиты."
    ),
    "case_protocol": (
        "📄 <b>Подписал протокол — теперь переживаю</b>\n\n"
        "Сам факт подписи не всегда означает признание вины, но формулировки в документе могут сильно повлиять на дело.\n\n"
        "Важно понять, что именно подписано: объяснение, протокол, явка с повинной, согласие, расписка или иной документ.\n\n"
        "⚠️ Документ лучше показать юристу, чтобы оценить риски и дальнейшие действия."
    ),
    "case_court": (
        "⚖️ <b>Меня вызывают в суд</b>\n\n"
        "Уточните, в каком качестве вас вызывают и по какому делу. Не стоит идти без подготовки.\n\n"
        "В суде каждое пояснение фиксируется, поэтому важно говорить только по существу и понимать последствия.\n\n"
        "⚠️ До заседания лучше подготовить позицию, документы и возможные ходатайства."
    ),
}

ARTICLE_TEXTS: Dict[str, str] = {
    "uk_105": "105 — Убийство",
    "uk_111": "111 — Умышленное причинение тяжкого вреда здоровью",
    "uk_112": "112 — Умышленное причинение средней тяжести вреда здоровью",
    "uk_115": "115 — Умышленное причинение лёгкого вреда здоровью",
    "uk_116": "116 — Побои",
    "uk_119": "119 — Угроза убийством или причинением тяжкого вреда здоровью",
    "uk_158": "158 — Кража",
    "uk_159": "159 — Мошенничество",
    "uk_160": "160 — Присвоение или растрата",
    "uk_161": "161 — Грабёж",
    "uk_162": "162 — Разбой",
    "uk_163": "163 — Вымогательство",
    "uk_166": "166 — Угон автомобиля",
    "uk_167": "167 — Умышленное уничтожение или повреждение имущества",
    "uk_186": "186 — Изготовление или сбыт поддельных денег",
    "uk_207": "207 — Заведомо ложное сообщение об акте терроризма",
    "uk_213": "213 — Хулиганство",
    "uk_222": "222 — Незаконный оборот оружия",
    "uk_228": "228 — Хранение наркотиков",
    "uk_228_1": "228.1 — Сбыт наркотиков",
    "uk_264": "264 — ДТП с тяжкими последствиями",
    "uk_264_1": "264.1 — Повторное управление в состоянии опьянения",
    "uk_285": "285 — Злоупотребление должностными полномочиями",
    "uk_286": "286 — Превышение должностных полномочий",
    "uk_290": "290 — Получение взятки",
    "uk_291": "291 — Дача взятки",
    "uk_306": "306 — Заведомо ложный донос",
    "uk_307": "307 — Ложные показания",
    "uk_318": "318 — Насилие в отношении представителя власти",
    "uk_319": "319 — Оскорбление представителя власти",
    "uk_327": "327 — Подделка документов",
    "uk_330": "330 — Самоуправство",
}


def article_text(key: str) -> str:
    title = ARTICLE_TEXTS.get(key, "Статья УК РФ")
    return (
        f"📚 <b>{title}</b>\n\n"
        "Это одна из часто встречающихся статей УК РФ. Важно учитывать не только название статьи, "
        "но и обстоятельства: роль человека, доказательства, показания, размер ущерба, последствия и стадию дела.\n\n"
        "⚠️ Даже похожие ситуации могут квалифицироваться по-разному. Ошибка в объяснениях или документах может ухудшить положение.\n\n"
        "✍️ Если ситуация связана с этой статьёй — лучше разобрать факты индивидуально."
    )

USER_MODE: Dict[int, str] = {}
LAST_ACTION: Dict[int, float] = {}
ADMIN_REPLY_TO: Dict[int, int] = {}
FOLLOW_UP_SENT: Dict[int, bool] = {}
DIALOG_HISTORY: Dict[int, list] = {}
CLIENT_INFO: Dict[int, dict] = {}
SHEET_ROWS: Dict[int, int] = {}

USER_MESSAGE_COUNT: Dict[int, int] = {}
USER_MESSAGE_LIMIT: Dict[int, int] = {}
FREE_MESSAGE_LIMIT = 10

def is_admin(message: types.Message) -> bool:
    username = (message.from_user.username or "").lower()
    return username == ADMIN_USERNAME.lower()


def button(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(button("📚 Полезные ответы", "topics"))
    kb.add(button("📝 Задать вопрос", "consult"))
    kb.add(button("🔎 Найти ответ", "search"))
    kb.add(button("⭐ Поддержать проект", "support_project"))
    kb.add(InlineKeyboardButton("ℹ️ Как пользоваться", callback_data="help"))
    return kb


def topics_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)

    for idx, topic in enumerate(TOPICS.keys()):
        kb.insert(button(topic, f"topic:{idx}"))

    kb.add(InlineKeyboardButton("⚖️ Уголовное право", callback_data="law_criminal"))
    kb.add(button("🏠 Главное меню", "main"))

    return kb


def criminal_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🚔 Реальные ситуации", callback_data="cases"))
    kb.add(InlineKeyboardButton("📚 Основные статьи УК РФ", callback_data="articles"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="topics"))
    return kb


def cases_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🚔 Меня остановили с наркотиками", callback_data="case_drugs"))
    kb.add(InlineKeyboardButton("👮‍♂️ Меня вызывают в полицию", callback_data="case_police"))
    kb.add(InlineKeyboardButton("📞 Позвонили из полиции — что делать", callback_data="case_police_call"))
    kb.add(InlineKeyboardButton("🏠 Пришли с обыском", callback_data="case_search"))
    kb.add(InlineKeyboardButton("📄 Подписал протокол — теперь переживаю", callback_data="case_protocol"))
    kb.add(InlineKeyboardButton("⚖️ Меня вызывают в суд", callback_data="case_court"))
    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="law_criminal"))
    return kb


def articles_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)

    for key, title in ARTICLE_TEXTS.items():
        kb.add(InlineKeyboardButton(title, callback_data=key))

    kb.add(InlineKeyboardButton("⬅️ Назад", callback_data="law_criminal"))
    return kb


def subtopics_menu(topic_idx: int) -> InlineKeyboardMarkup:
    topic_name = list(TOPICS.keys())[topic_idx]
    kb = InlineKeyboardMarkup(row_width=2)

    for title, answer_id in TOPICS[topic_name].items():
        if str(answer_id) in ANSWERS:
            kb.insert(button(title, f"answer:{answer_id}"))

    kb.add(button("⬅️ Назад", "topics"), button("🏠 Главное меню", "main"))
    return kb


def answer_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(button("📝 Получить консультацию", "consult"))
    kb.add(button("🏠 Главное меню", "main"))
    return kb


def search_results_menu(results: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    for answer_id, title in results[:8]:
        kb.add(button(f"{answer_id}. {title[:55]}", f"answer:{answer_id}"))
    kb.add(button("🏠 Главное меню", "main"))
    return kb


def normalize_query(text: str) -> str:
    text = text.lower().replace("ё", "е")
    return re.sub(r"[^а-яa-z0-9 ]+", " ", text).strip()


def title_from_text(text: str) -> str:
    line = text.strip().split("\n", 1)[0].strip()
    line = re.sub(r"^\d+\.\s*", "", line)
    return line[:90] or "Ответ"


def prepare_answer(answer_id: int) -> str:
    raw = ANSWERS.get(str(answer_id), "Ответ не найден.").strip()
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    # Telegram limit is 4096; leave room for footer.
    if len(raw) > 3400:
        raw = raw[:3400].rsplit(" ", 1)[0] + "…\n\n<i>Текст сокращен. Для полной оценки ситуации можно направить запрос на консультацию.</i>"
    return (
        f"⚖️ <b>{title_from_text(raw)}</b>\n\n{raw}\n\n"
        "—\n"
        "Если ситуация похожа на вашу — опишите её.\n"
        "Подскажу, что лучше сделать именно в вашем случае."
    )


def is_spam(text: str) -> bool:
    lowered = text.lower()

    # Блокируем ссылки
    if re.search(r"(https?://|www\.|t\.me/)", lowered):
        return True

    # Очень длинные сообщения лучше не принимать
    if len(text) > 3500:
        return True

    # Много одинаковых символов подряд
    if re.search(r"(.)\1{15,}", lowered):
        return True

    # Слишком много цифр подряд — похоже на спам/рекламу
    if re.search(r"\d{25,}", text):
        return True

    return False


def too_fast(user_id: int) -> bool:
    now = time.time()
    last = LAST_ACTION.get(user_id, 0)
    LAST_ACTION[user_id] = now
    return now - last < 2.0


async def notify_admin(message: types.Message) -> None:
    user = message.from_user
    username = f"@{user.username}" if user.username else "без username"

    history = DIALOG_HISTORY.get(user.id, [])
    history_text = "\n\n".join(history[-6:]) if history else "Истории пока нет."

    payload = (
        "📩 <b>Новая заявка</b>\n\n"
        f"👤 Пользователь: {username}\n"
        f"🆔 ID клиента: <code>{user.id}</code>\n\n"
        f"📜 <b>История диалога:</b>\n{history_text}\n\n"
        f"—\n<b>Новое сообщение:</b>\n{message.text}"
    )

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✍️ Ответить клиенту", callback_data=f"admin_reply:{user.id}"))
    kb.add(InlineKeyboardButton("🟡 В работе", callback_data=f"status_work:{user.id}"))
    kb.add(InlineKeyboardButton("✅ Закрыто", callback_data=f"status_closed:{user.id}"))

    try:
        admin_id = int(ADMIN_ID.strip())
        await bot.send_message(admin_id, payload, reply_markup=kb)
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки админу: {e}")


async def send_follow_up(user_id: int):
    await asyncio.sleep(600)

    if FOLLOW_UP_SENT.get(user_id):
        return

    try:
        await bot.send_message(
            user_id,
            "Если ваш вопрос ещё актуален — напишите, помогу разобраться."
        )
        FOLLOW_UP_SENT[user_id] = True
    except Exception:
        pass


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    USER_MODE.pop(message.from_user.id, None)

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=open("assets/start.jpg", "rb"),
        caption=(
            "👋 <b>Адвокат онлайн</b>\n\n"
            "Краткие ответы на юридические вопросы.\n"
            "Если нужен разбор ситуации — задайте вопрос."
        ),
        reply_markup=main_menu()
    )


@dp.message_handler(commands=["myid"])
async def myid(message: types.Message):
    await message.answer(f"Ваш Telegram ID: <code>{message.from_user.id}</code>")
    
@dp.message_handler(commands=["testadmin"])
async def testadmin(message: types.Message):
    if not ADMIN_ID:
        await message.answer("❌ ADMIN_ID не задан.")
        return

    try:
        await bot.send_message(int(ADMIN_ID), "✅ Тест админу дошёл")
        await message.answer("✅ Отправлено админу")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message_handler(commands=["reply"])
async def reply_to_user(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID).strip():
        await message.answer("⛔ Команда доступна только администратору.")
        return

    parts = message.text.split(" ", 2)

    if len(parts) < 3:
        await message.answer(
            "Используйте формат:\n"
            "<code>/reply ID_клиента текст ответа</code>"
        )
        return

    client_id = parts[1]
    reply_text = parts[2]

    try:
        await bot.send_message(
            int(client_id),
            f"⚖️ <b>Ответ юриста:</b>\n\n{reply_text}"
        )
        await message.answer("✅ Ответ отправлен клиенту.")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить ответ: {e}")
        
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    data = call.data or ""

    if data == "law_criminal":
        await call.message.answer(
            "⚖️ <b>Уголовное право</b>\n\nВыберите раздел:",
            reply_markup=criminal_menu()
        )
        await call.answer()
        return

    if data == "cases":
        await call.message.answer(
            "🚔 <b>Выберите ситуацию:</b>",
            reply_markup=cases_menu()
        )
        await call.answer()
        return

    if data == "articles":
        await call.message.answer(
            "📚 <b>Основные статьи УК РФ:</b>",
            reply_markup=articles_menu()
        )
        await call.answer()
        return

    if data in CASE_TEXTS:
        await call.message.answer(CASE_TEXTS[data], reply_markup=answer_menu())
        await call.answer()
        return

    if data in ARTICLE_TEXTS:
        await call.message.answer(article_text(data), reply_markup=answer_menu())
        await call.answer()
        return

    if data == "support_project":
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("⭐ 5", callback_data="donate_stars:5"),
            InlineKeyboardButton("⭐ 10", callback_data="donate_stars:10")
        )
        kb.add(
            InlineKeyboardButton("⭐ 20", callback_data="donate_stars:20"),
            InlineKeyboardButton("⭐ 50", callback_data="donate_stars:50")
        )
        kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main"))

        await call.message.answer(
            "⭐ <b>Поддержать проект</b>\n\n"
            "Если бот оказался полезен, можно отблагодарить Stars.\n\n"
            "Выберите удобную сумму:",
            reply_markup=kb
        )
        await call.answer()
        return

    if data.startswith("donate_stars:"):
        amount = int(data.split(":", 1)[1])
        await bot.send_invoice(
            chat_id=call.message.chat.id,
            title="Поддержка проекта",
            description=f"Благодарность за помощь — {amount} Stars",
            payload=f"donation_{amount}_{call.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label="Поддержка проекта", amount=amount)]
        )
        await call.answer()
        return

    if data.startswith("admin_reply:"):
        client_id = int(data.split(":", 1)[1])
        ADMIN_REPLY_TO[call.from_user.id] = client_id

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("❌ Отменить ответ", callback_data="cancel_admin_reply"))

        await call.message.answer(
            "✍️ Напишите текст ответа клиенту одним сообщением.",
            reply_markup=kb
        )
        await call.answer()
        return

    if data == "cancel_admin_reply":
        ADMIN_REPLY_TO.pop(call.from_user.id, None)
        await call.message.answer("❌ Ответ клиенту отменён.")
        await call.answer()
        return

    if data.startswith("status_work:"):
        client_id = int(data.split(":", 1)[1])
        save_dialog_to_sheet(client_id, status="в работе")
        await call.message.answer(f"🟡 Заявка клиента <code>{client_id}</code> взята в работу.")
        await call.answer("Заявка взята в работу")
        return

    if data.startswith("status_closed:"):
        client_id = int(data.split(":", 1)[1])
        save_dialog_to_sheet(client_id, status="закрыта")
        await call.message.answer(f"✅ Заявка клиента <code>{client_id}</code> закрыта.")
        await call.answer("Заявка закрыта")
        return

    if data == "client_done":
        user_id = call.from_user.id
        username = f"@{call.from_user.username}" if call.from_user.username else "без username"

        DIALOG_HISTORY.setdefault(user_id, []).append("Клиент:\nМне всё понятно, спасибо")
        DIALOG_HISTORY[user_id] = DIALOG_HISTORY[user_id][-30:]
        CLIENT_INFO[user_id] = {
            "username": username,
            "name": call.from_user.first_name or ""
        }
        save_dialog_to_sheet(user_id, status="закрыта")

        try:
            admin_id = int(ADMIN_ID.strip())
            await bot.send_message(
                admin_id,
                f"✅ Клиент завершил диалог.\n\n👤 {username}\n🆔 <code>{user_id}</code>\n\nЗаявка закрыта."
            )
        except Exception:
            pass

        USER_MODE[user_id] = "main"

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(InlineKeyboardButton("⭐ Отблагодарить Stars", callback_data="support_project"))
        kb.add(InlineKeyboardButton("🏠 Главное меню", callback_data="main"))

        await call.message.answer(
            "✅ Спасибо за обращение.\n\n"
            "Если бот оказался полезен, можно поддержать проект ⭐",
            reply_markup=kb
        )
        await call.answer()
        return

    if data == "help":
        await call.message.answer(
            "ℹ️ <b>Как пользоваться ботом</b>\n\n"
            "📚 Полезные ответы — выбрать тему и получить краткий ответ.\n"
            "📝 Задать вопрос — написать свою ситуацию одним сообщением.\n"
            "🔎 Найти ответ — поиск по ключевым словам.\n\n"
            "💬 Первичная консультация бесплатная.\n"
            "После лимита можно продолжить через ⭐ Stars.",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    if data == "main":
        await call.message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())
        await call.answer()
        return

    if data == "topics":
        await call.message.answer(
            "📚 <b>Полезные ответы</b>\n\n"
            "Краткие ответы на частые вопросы.\n\n"
            "Выберите тему:",
            reply_markup=topics_menu()
        )
        await call.answer()
        return

    if data.startswith("topic:"):
        idx = int(data.split(":", 1)[1])
        topic_name = list(TOPICS.keys())[idx]
        await call.message.answer(
            f"{topic_name}\n\nВыберите вопрос:",
            reply_markup=subtopics_menu(idx)
        )
        await call.answer()
        return

    if data.startswith("answer:"):
        answer_id = int(data.split(":", 1)[1])
        await call.message.answer(prepare_answer(answer_id), reply_markup=answer_menu())
        await call.answer()
        return

    if data == "search":
        USER_MODE[call.from_user.id] = "search"
        await call.message.answer(
            "🔎 Введите 1–3 ключевых слова. Например: <i>алименты</i>, <i>допрос</i>, <i>пенсия</i>."
        )
        await call.answer()
        return

    if data == "consult":
        USER_MODE[call.from_user.id] = "consult"
        await call.message.answer(
            "📝 <b>Консультация</b>\n\n"
            "Кратко опишите вашу ситуацию одним сообщением.\n\n"
            f"⚠️ Бесплатный лимит: <b>{FREE_MESSAGE_LIMIT} сообщений</b>.\n"
            "После этого можно продолжить консультацию через ⭐ Stars.\n\n"
            "✍️ Напишите ваш вопрос:"
        )
        await call.answer()
        return

    await call.answer()


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    payment = message.successful_payment
    amount = payment.total_amount
    user_id = message.from_user.id

    USER_MESSAGE_LIMIT[user_id] = USER_MESSAGE_LIMIT.get(user_id, FREE_MESSAGE_LIMIT) + amount

    await message.answer(
        "🙏 Спасибо за поддержку!\n\n"
        f"Вам добавлено: {amount} сообщений ⭐\n"
        f"Ваш новый лимит: {USER_MESSAGE_LIMIT[user_id]}"
    )

    try:
        admin_id = int(ADMIN_ID.strip())
        await bot.send_message(
            admin_id,
            f"⭐ Пользователь купил +{amount} сообщений\n\n"
            f"👤 @{message.from_user.username if message.from_user.username else 'без username'}\n"
            f"🆔 <code>{user_id}</code>"
        )
    except Exception:
        pass


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def text_handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in ADMIN_REPLY_TO:
        client_id = ADMIN_REPLY_TO.pop(user_id)
        FOLLOW_UP_SENT[client_id] = True
        try:
            kb = InlineKeyboardMarkup(row_width=1)
            kb.add(InlineKeyboardButton("✍️ Спросить ещё", callback_data="consult"))
            kb.add(InlineKeyboardButton("✅ Мне всё понятно, спасибо", callback_data="client_done"))

            await bot.send_message(
                client_id,
                f"⚖️ <b>Ответ юриста:</b>\n\n{text}",
                reply_markup=kb
            )

            history = DIALOG_HISTORY.get(client_id, [])
            history.append(f"Юрист:\n{text}")
            DIALOG_HISTORY[client_id] = history[-30:]
            save_dialog_to_sheet(client_id, status="отвечено")

            await message.answer("✅ Ответ отправлен клиенту.")
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить ответ: {e}")
        return

    mode = USER_MODE.get(user_id)

    if mode == "consult":
        history = DIALOG_HISTORY.get(user_id, [])
        history.append(f"Клиент:\n{text}")
        DIALOG_HISTORY[user_id] = history[-10:]
        CLIENT_INFO[user_id] = {
            "username": f"@{message.from_user.username}" if message.from_user.username else "без username",
            "name": message.from_user.first_name or ""
        }

        save_dialog_to_sheet(user_id, status="новая")

        await notify_admin(message)

        USER_MODE[user_id] = "main"

        await message.answer(
            "✅ Запрос принят. Мы свяжемся с вами после рассмотрения.\n\n🏠 Главное меню:",
            reply_markup=main_menu()
        )
        return

    if too_fast(user_id):
        await message.answer("⏳ Слишком часто. Повторите через пару секунд.")
        return

    if len(text) < 3:
        await message.answer("Напишите чуть подробнее.")
        return

    if is_spam(text):
        await message.answer("⛔ Сообщение похоже на спам. Ссылки и слишком длинные сообщения не принимаются.")
        return

    # Поиск включается либо кнопкой, либо обычным текстом.
    q = normalize_query(text)
    if len(q) < 3:
        await message.answer("Введите более точный запрос.")
        return

    scored = []
    words = [w for w in q.split() if len(w) >= 3][:5]
    for sid, ans in ANSWERS.items():
        hay = normalize_query(title_from_text(ans) + " " + ans)
        score = 0
        for w in words:
            if w in hay:
                score += 2 if w in normalize_query(title_from_text(ans)) else 1
        if q in hay:
            score += 3
        if score:
            scored.append((score, int(sid), title_from_text(ans)))

    scored.sort(reverse=True)
    results = [(sid, title) for _, sid, title in scored]

    if results:
        await message.answer("🔎 Найдены подходящие материалы:", reply_markup=search_results_menu(results))
    else:
        await message.answer(
            "По этому запросу точного ответа не найдено.\n\n"
            "Можно выбрать раздел вручную или отправить вопрос на консультацию.",
            reply_markup=main_menu(),
        )


def save_dialog_to_sheet(user_id: int, status: str = "новая"):
    if not os.getenv("GOOGLE_CREDENTIALS"):
        return

    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M")
        info = CLIENT_INFO.get(user_id, {})
        username = info.get("username", "без username")
        name = info.get("name", "")
        history = DIALOG_HISTORY.get(user_id, [])
        full_text = "\n\n".join(history) if history else ""

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Заявки бот").sheet1

        rows = sheet.get_all_values()
        row_number = None
        for i, row in enumerate(rows, start=1):
            if len(row) > 1 and str(row[1]).strip() == str(user_id):
                row_number = i
                break

        if row_number:
            sheet.update_cell(row_number, 5, full_text)
            sheet.update_cell(row_number, 6, status)
            sheet.update_cell(row_number, 8, now)
        else:
            sheet.append_row([
                now,
                user_id,
                username,
                name,
                full_text,
                status,
                "telegram_bot",
                now
            ])
    except Exception as e:
        print("❌ Ошибка записи в таблицу:", e)


async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
