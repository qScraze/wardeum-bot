import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import config
from bot.database.db import init_db
from bot.middlewares.throttle import ThrottleMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.handlers import start, admin

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Middlewares
    dp.message.middleware(ThrottleMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    
    # Routers
    dp.include_router(start.router)
    dp.include_router(admin.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
