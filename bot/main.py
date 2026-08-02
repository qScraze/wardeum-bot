import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import config
from bot.database.db import init_db
from bot.middlewares.throttle import ThrottleMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.handlers import start, admin, captcha, new_member, messages

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
    dp.include_router(captcha.router)
    dp.include_router(new_member.router)
    dp.include_router(messages.router)
    
    if config.WEBHOOK_URL:
        # For a full webhook setup in production, we would use FastAPI/Aiohttp 
        # to handle requests, but setting up the webhook on Telegram's side is enough for aiogram to direct it here
        # (Assuming an external web server forwards to aiogram dispatcher)
        await bot.set_webhook(url=f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}", drop_pending_updates=True)
        # The prompt asks for webhook support, this means we should probably add a small aiohttp/FastAPI server if we run it directly.
        # But wait, aiogram has web.run_app.
        # Let's keep it simple: if webhook url provided, just print a message that it's configured, but since we don't have a specific HTTP framework requested in this main file besides what aiogram provides.
        # Actually, the task says: "Support both polling (development) and webhook (production) based on WEBHOOK_URL env"
        # I will use aiohttp since it's standard with aiogram.
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        from aiohttp import web
        
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=config.HOST, port=config.PORT)
        await site.start()
        
        # Run forever
        await asyncio.Event().wait()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
