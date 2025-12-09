import asyncio
import logging
from aiogram import Bot, Dispatcher

from aiohttp import web
from config import TOKEN
from app.handlers import router
from app.database.models import async_main


async def start_web_server():
    async def handle(request):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)

    await runner.setup()

    # Render передає PORT через env
    import os
    port = int(os.environ.get("PORT", 10000))

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Fake web server started on port {port}")


async def main():
    logging.basicConfig(level=logging.INFO)

    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Запускаємо вебсервер + polling паралельно
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
