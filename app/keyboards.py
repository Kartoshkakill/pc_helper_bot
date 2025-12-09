
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Головне меню (Reply-клавіатура)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💻 Підібрати комп'ютер")],
        [KeyboardButton(text="ℹ️ Про бота"), KeyboardButton(text="💲 Курс долара")],
        [KeyboardButton(text="👤 Мій профіль")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Оберіть пункт меню…"
)


# Inline-кнопки для вибору призначення ПК
def usage_inline_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="🎮 Ігри", callback_data="usage_games"),
        InlineKeyboardButton(text="📊 Офіс/навчання", callback_data="usage_office"),
        InlineKeyboardButton(text="🎬 Монтаж/дизайн", callback_data="usage_design"),
        InlineKeyboardButton(text="💻 Програмування", callback_data="usage_dev"),
    )
    return kb.adjust(2).as_markup()


# Inline-кнопки після рекомендації
def more_inline_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="🔁 Ще одна рекомендація", callback_data="more_build"),
        InlineKeyboardButton(text="🏠 На головне меню", callback_data="to_main"),
    )
    return kb.adjust(1).as_markup()
