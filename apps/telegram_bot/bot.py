import asyncio
import logging
import os
import django
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telegram_shop.settings')
django.setup()

from apps.telegram_bot.handlers import start, products, cart

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        # Initialize bot and dispatcher
        self.bot = Bot(token=settings.BOT_TOKEN)

        # Redis storage for FSM
        storage = RedisStorage.from_url(settings.REDIS_URL)
        self.dp = Dispatcher(storage=storage)

        # Include routers
        self.dp.include_router(start.router)
        self.dp.include_router(products.router)
        self.dp.include_router(cart.router)

    async def start_polling(self):
        """Start bot polling"""
        logger.info("Bot started polling...")

        try:
            await self.dp.start_polling(self.bot)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.bot.session.close()


def run_bot():
    """Run the telegram bot"""
    bot = TelegramBot()
    asyncio.run(bot.start_polling())


if __name__ == "__main__":
    run_bot()