import aiohttp
from aiogram import F, Router
from aiogram.types import (
    Message, CallbackQuery, PreCheckoutQuery,
    LabeledPrice
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from .states import PcWizard, TopUp
from . import keyboards as kb
from .database import requests as rq
from config import USD_RATE_API, PAYMENT_PROVIDER_TOKEN


router = Router()

# ============================================================
#                 ФУНКЦІЯ — КУРС ДОЛАРА
# ============================================================

async def get_usd_uah_rate() -> float | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(USD_RATE_API, timeout=5) as resp:
                data = await resp.json()
                return float(data[0]["rate"])
    except Exception:
        return None


# ============================================================
#                 ЛОГІКА ПІДБОРУ ПК
# ============================================================

def build_pc_recommendation(usage, budget, cpu_pref):
    cpu = "AMD Ryzen" if cpu_pref.lower().startswith("a") else "Intel Core"

    if usage == "games":
        gpu = "RTX 3050–4060"
        ram = "16–32 ГБ"
    elif usage == "office":
        gpu = "Вбудоване відео"
        ram = "8–16 ГБ"
    elif usage == "design":
        gpu = "RTX 4060–4070"
        ram = "32 ГБ"
    else:
        gpu = "будь-яка / iGPU"
        ram = "16–32 ГБ"

    return (
        f"🔥 Рекомендована збірка для твоїх задач:\n\n"
        f"• CPU: {cpu}\n"
        f"• GPU: {gpu}\n"
        f"• RAM: {ram}\n"
        f"• SSD: 1 ТБ NVMe\n\n"
        f"Орієнтовний бюджет: {budget} $"
    )


# ============================================================
#                       КОМАНДА /start
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await rq.get_or_create_user(
        tg_id=message.from_user.id,
        name=message.from_user.full_name
    )

    await message.answer(
        f"Привіт, {user.name}! 👋\n"
        f"Я бот для індивідуального підбору комп'ютера!",
        reply_markup=kb.main_menu
    )


# ============================================================
#                       /help /info
# ============================================================

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/start — перезапустити бота\n"
        "/help — довідка\n"
        "/balance — твій баланс\n"
        "/topup — поповнити баланс\n"
        "/pick_pc — підібрати комп'ютер"
    )


@router.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer(
        "Бот створений для підбору ПК та демонстрації Telegram Payments."
    )


# ============================================================
#                      ПІДБІР ПК
# ============================================================

@router.message(Command("pick_pc"))
@router.message(F.text == "💻 Підібрати комп'ютер")
async def pick_pc(message: Message, state: FSMContext):
    await state.set_state(PcWizard.usage)
    await message.answer("Для чого потрібен ПК?", reply_markup=kb.usage_inline_kb())


@router.callback_query(F.data.startswith("usage_"))
async def choose_usage(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_")[1]
    await state.update_data(usage=code)
    await state.set_state(PcWizard.budget)
    await callback.message.answer("Введіть бюджет у $:")


@router.message(PcWizard.budget)
async def set_budget(message: Message, state: FSMContext):
    try:
        budget = int(message.text)
    except ValueError:
        return await message.answer("Введи число!")

    await state.update_data(budget=budget)
    await state.set_state(PcWizard.cpu)
    await message.answer("Який CPU віддаєш перевагу? (AMD / Intel)")


@router.message(PcWizard.cpu)
async def finish_pc(message: Message, state: FSMContext):
    cpu_pref = message.text.strip()

    data = await state.get_data()
    usage = data["usage"]
    budget = data["budget"]

    rec = build_pc_recommendation(usage, budget, cpu_pref)

    # Зберігаємо у БД
    await rq.update_user_profile(message.from_user.id, usage=usage, budget=budget)

    await message.answer(rec)
    await state.clear()


# ============================================================
#                   Курс долара по кнопці
# ============================================================

@router.message(F.text == "💲 Курс долара")
async def send_rate(message: Message):
    rate = await get_usd_uah_rate()
    if rate:
        await message.answer(f"1$ = {rate:.2f} ₴")
    else:
        await message.answer("API недоступне 😢")


# ============================================================
#                  БАЛАНС + РЕЄСТРАЦІЯ
# ============================================================

@router.message(Command("register"))
async def cmd_register(message: Message):
    user = await rq.get_or_create_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Ти зареєстрований! Баланс: {user.balance} грн")


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = await rq.get_user(message.from_user.id)
    if not user:
        return await message.answer("Спочатку зареєструйся: /register")

    await message.answer(f"💰 Твій баланс: {user.balance} грн")


# ============================================================
#                     ПОПОВНЕННЯ БАЛАНСУ /topup
# ============================================================

@router.message(Command("topup"))
async def cmd_topup(message: Message, state: FSMContext):
    await state.set_state(TopUp.amount)
    await message.answer("Введи суму поповнення (грн):")


@router.message(TopUp.amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введи додатнє число 🙃")

    await state.clear()

    prices = [LabeledPrice(label="Поповнення балансу", amount=amount * 100)]

    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Поповнення балансу",
        description=f"Поповнення на {amount} грн",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="uah",
        prices=prices,
        payload=f"topup:{message.from_user.id}"
    )


# ============================================================
#          Офіційний Telegram pre-checkout (ОБОВʼЯЗКОВО)
# ============================================================

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):
    await pre_checkout_q.bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)


# ============================================================
#         ПІДСУМУВАННЯ ПЛАТЕЖУ — ДОДАЄМО ДО БАЛАНСУ
# ============================================================

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    amount = message.successful_payment.total_amount // 100

    await rq.change_balance(message.from_user.id, amount)

    await message.answer(f"✅ Платіж успішний!\nБаланс поповнено на {amount} грн.")

@router.message(F.text == "ℹ️ Про бота")
async def about_bot(message: Message):
    await message.answer(
        "🤖 *Про бота*\n\n"
        "Цей бот створений для індивідуального підбору комп'ютера, "
        "розрахунку бюджету, перевірки актуального курсу долара та роботи "
        "з внутрішнім балансом користувача.\n\n"
        "🔧 Технології:\n"
        "• Aiogram 3\n"
        "• SQLite (SQLAlchemy)\n"
        "• FSM (Finite State Machine)\n"
        "• Telegram Payments API\n\n"
        "Автор: Mykolka 💪",
        parse_mode="Markdown"
    )

@router.message(F.text == "👤 Мій профіль")
async def my_profile(message: Message):
    user = await rq.get_user(message.from_user.id)

    if not user:
        return await message.answer("Спочатку виконай команду /register")

    await message.answer(
        f"👤 *Твій профіль*\n\n"
        f"Ім'я: {user.name}\n"
        f"ID: {user.tg_id}\n"
        f"Баланс: {user.balance} грн\n"
        f"Призначення ПК: {user.usage if user.usage else 'не вказано'}\n"
        f"Бюджет: {user.budget if user.budget else 'не вказано'} $",
        parse_mode="Markdown"
    )
