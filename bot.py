import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

import aiohttp

from checkers import ALL_CHECKERS, CheckResult, Status
from utils.db import init_db, get_or_create_user, increment_checks, increment_ai
from utils.ai_generator import generate_usernames

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FREE_CHECKS = int(os.getenv("FREE_CHECKS_PER_DAY", 15))
FREE_AI = int(os.getenv("FREE_AI_GENERATIONS_PER_DAY", 5))
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


def status_emoji(status: Status) -> str:
    return {
        Status.AVAILABLE: "✅",
        Status.TAKEN: "❌",
        Status.INVALID: "⚠️",
        Status.ERROR: "💥",
        Status.UNKNOWN: "❓"
    }.get(status, "❓")


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Проверить ник", callback_data="check")],
        [InlineKeyboardButton(text="🤖 AI сгенерировать", callback_data="ai_gen")],
        [InlineKeyboardButton(text="📊 Мои лимиты", callback_data="limits")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Я <b>Universal Username Checker</b> — проверяю доступность ников на нескольких платформах "
        "и умею генерировать варианты с помощью AI.\n\n"
        "Платформы сейчас:\n"
        "• Telegram\n• Roblox\n• GitHub\n• Steam\n• Minecraft\n\n"
        "Выбери действие:",
        reply_markup=main_keyboard(),
        parse_mode=ParseMode.HTML
    )


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def cmd_help(event: Message | CallbackQuery):
    text = (
        "<b>📖 Как пользоваться</b>\n\n"
        "1. Нажми «Проверить ник» и отправь юзернейм (можно с @)\n"
        "2. Или сразу напиши ник в чат — я проверю\n"
        "3. «AI сгенерировать» — опиши, какой ник хочешь\n\n"
        "<b>Лимиты (бесплатно)</b>\n"
        f"• Проверок в день: {FREE_CHECKS}\n"
        f"• AI-генераций в день: {FREE_AI}\n\n"
        "Бот сделан для удобного поиска свободных ников.\n"
        "Точность Telegram-проверки приблизительная (публичный метод)."
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)


@router.callback_query(F.data == "limits")
async def show_limits(callback: CallbackQuery):
    user = await get_or_create_user(callback.from_user.id, callback.from_user.username)
    premium = "⭐ Premium" if user["is_premium"] else "Бесплатный"

    text = (
        f"<b>📊 Твои лимиты</b>\n\n"
        f"Статус: {premium}\n"
        f"Проверок сегодня: <b>{user['checks_today']}</b> / {FREE_CHECKS}\n"
        f"AI-генераций сегодня: <b>{user['ai_today']}</b> / {FREE_AI}\n\n"
        "Лимиты сбрасываются каждый день в 00:00 UTC."
    )
    await callback.message.edit_text(text, reply_markup=main_keyboard(), parse_mode=ParseMode.HTML)
    await callback.answer()


@router.callback_query(F.data == "check")
async def ask_username(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>Отправь юзернейм</b> для проверки\n\n"
        "Можно с @ или без. Пример: <code>coolname</code> или <code>@coolname</code>",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.callback_query(F.data == "ai_gen")
async def ask_ai_prompt(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 <b>Опиши, какой ник хочешь</b>\n\n"
        "Примеры:\n"
        "• тёмный минималистичный ник 5-7 букв\n"
        "• геймерский для Roblox\n"
        "• брендовый короткий на английском\n"
        "• что-то в стиле cyberpunk\n\n"
        "Просто напиши описание следующим сообщением.",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@router.message(F.text)
async def handle_text(message: Message):
    text = message.text.strip()

    # Игнорируем команды
    if text.startswith("/"):
        return

    user = await get_or_create_user(message.from_user.id, message.from_user.username)

    # Простая эвристика: если сообщение короткое и похоже на ник — проверяем
    # Если длинное / с пробелами — считаем запросом к AI
    is_likely_username = (
        len(text) <= 32
        and " " not in text
        and not any(c in text for c in "!?.,;:()[]{}")
    )

    if is_likely_username:
        await do_check(message, text, user)
    else:
        await do_ai_generate(message, text, user)


async def do_check(message: Message, username: str, user: dict):
    if not user["is_premium"] and user["checks_today"] >= FREE_CHECKS:
        await message.answer(
            f"⏳ Дневной лимит проверок исчерпан ({FREE_CHECKS}).\n"
            "Попробуй завтра или напиши админу за премиумом.",
            reply_markup=main_keyboard()
        )
        return

    wait_msg = await message.answer("⏳ Проверяю на всех платформах...")

    results: list[CheckResult] = []
    async with aiohttp.ClientSession() as session:
        tasks = [checker.check(username, session) for checker in ALL_CHECKERS]
        results = await asyncio.gather(*tasks)

    await increment_checks(message.from_user.id)

    # Формируем ответ
    lines = [f"<b>Результаты для:</b> <code>{username.lstrip('@')}</code>\n"]
    for r in results:
        emoji = status_emoji(r.status)
        line = f"{emoji} <b>{r.platform}</b>: {r.message}"
        if r.url and r.status in (Status.TAKEN, Status.AVAILABLE):
            line += f"\n   🔗 {r.url}"
        lines.append(line)

    lines.append(f"\nПроверок сегодня: {user['checks_today'] + 1}/{FREE_CHECKS}")

    await wait_msg.edit_text("\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await message.answer("Что дальше?", reply_markup=main_keyboard())


async def do_ai_generate(message: Message, prompt: str, user: dict):
    if not user["is_premium"] and user["ai_today"] >= FREE_AI:
        await message.answer(
            f"⏳ Лимит AI-генераций на сегодня исчерпан ({FREE_AI}).",
            reply_markup=main_keyboard()
        )
        return

    wait_msg = await message.answer("🤖 Генерирую варианты...")

    names = await generate_usernames(prompt, count=8)
    await increment_ai(message.from_user.id)

    if not names:
        await wait_msg.edit_text("Не удалось сгенерировать. Попробуй другое описание.")
        return

    text = (
        f"<b>Варианты по запросу:</b> <i>{prompt[:80]}</i>\n\n"
        + "\n".join(f"• <code>{n}</code>" for n in names)
        + "\n\nМожешь сразу отправить любой из них — я проверю доступность."
    )
    await wait_msg.edit_text(text, parse_mode=ParseMode.HTML)
    await message.answer("Выбери ник или напиши новый запрос:", reply_markup=main_keyboard())


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан! Создай .env файл.")

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
