import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import TOKEN
from app.handlers import router
from app.database.models import async_main


async def main():
    logging.basicConfig(level=logging.INFO)

    # Створюємо таблиці (users) з нуля
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Підключаємо router!!!
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
