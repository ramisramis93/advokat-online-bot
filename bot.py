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
    "⚖️ Уголовное право": {
        "Задержание": 16,
        "Допрос": 17,
        "Жалоба на полицию": 18,
        "Уголовное дело": 19,
        "Отказ в возбуждении дела": 20,
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

USER_MODE: Dict[int, str] = {}
LAST_ACTION: Dict[int, float] = {}
ADMIN_REPLY_TO: Dict[int, int] = {}
FOLLOW_UP_SENT: Dict[int, bool] = {}
DIALOG_HISTORY: Dict[int, list] = {}
CLIENT_INFO: Dict[int, dict] = {}
SHEET_ROWS: Dict[int, int] = {}

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
    kb.add(InlineKeyboardButton("ℹ️ Как пользоваться", callback_data="help"))
    return kb


def topics_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    for idx, topic in enumerate(TOPICS.keys()):
        kb.insert(button(topic, f"topic:{idx}"))
    kb.add(button("🏠 Главное меню", "main"))
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
    
@dp.message_handler(commands=["sheettest"])
async def sheettest(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID).strip():
        await message.answer("⛔ Команда доступна только администратору.")
        return

    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)

        sheet = client.open("Заявки бот").sheet1

        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        sheet.append_row([
            now,
            message.from_user.id,
            f"@{message.from_user.username}" if message.from_user.username else "без username",
            message.from_user.first_name or "",
            "Тестовая запись из бота",
            "тест",
            "telegram_bot",
            now
        ])

        await message.answer("✅ Тестовая запись добавлена в Google Таблицу.")

    except Exception as e:
        await message.answer(f"❌ Ошибка Google Таблицы:\n<code>{e}</code>")


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
        DIALOG_HISTORY[user_id] = DIALOG_HISTORY[user_id][-10:]
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

        await call.message.answer(
            "✅ Спасибо за обращение.\n\n🏠 Главное меню:",
            reply_markup=main_menu()
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
            "Если потребуется подробный разбор — помогу отдельно.\n\n"
            "📩 После ответа можно задать уточняющий вопрос или завершить диалог.",
            reply_markup=main_menu()
        )
        await call.answer()
        return

    if data == "main":
        await call.message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu())

    elif data == "topics":
        await call.message.answer(
            "📚 <b>Полезные ответы</b>\n\n"
            "Краткие ответы на частые вопросы.\n\n"
            "Выберите тему:",
            reply_markup=topics_menu()
        )

    elif data.startswith("topic:"):
        idx = int(data.split(":", 1)[1])
        topic_name = list(TOPICS.keys())[idx]
        await call.message.answer(
            f"{topic_name}\n\nВыберите вопрос:",
            reply_markup=subtopics_menu(idx)
        )

    elif data.startswith("answer:"):
        answer_id = int(data.split(":", 1)[1])
        await call.message.answer(
            prepare_answer(answer_id),
            reply_markup=answer_menu()
        )

    elif data == "search":
        USER_MODE[call.from_user.id] = "search"
        await call.message.answer(
            "🔎 Введите 1–3 ключевых слова. Например: <i>алименты</i>, <i>допрос</i>, <i>пенсия</i>."
        )

    elif data == "consult":
        USER_MODE[call.from_user.id] = "consult"
        await call.message.answer(
            "📝 Кратко опишите вашу ситуацию одним сообщением.\n\n"
            "Я изучу и дам ответ."
        )

    await call.answer()


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
            DIALOG_HISTORY[client_id] = history[-10:]
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
    # Google Таблица временно отключена, чтобы бот работал стабильно.
    return


async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    
