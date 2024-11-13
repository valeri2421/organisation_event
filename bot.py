import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import Config, load_config
from aiogram.client.bot import DefaultBotProperties
from handlers import user_handlers, other_handlers, admin_handlers, org_handlers
from keyboards.set_menu import set_main_menu


# Инициализация логгера
logger = logging.getLogger(__name__)
config: Config = load_config()
bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# Функция конфигурирования и запуска бота
async def main():
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    await set_main_menu(bot)

    # Регистрация роутеров в диспетчере
    dp.include_router(org_handlers.router)
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(other_handlers.router)
    # Пропуск накопившихся апдейтов и запуск polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
