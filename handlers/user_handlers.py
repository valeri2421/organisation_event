from keyboards.keyboard_utils import User, Admin, Organizer
from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import sqlite3 as sq


db = sq.connect('system_bd.db')
cur = db.cursor()

router = Router()
dispatcher = Dispatcher()

#обработка команды старт
@router.message(Command(commands='start'))
async def process_start_command(message: Message):
    a = 0
    cur.execute("SELECT * FROM administration WHERE user_id=?",
                (str(message.from_user.id),))
    administration_exists = cur.fetchone() is not None
    if administration_exists:
        await message.answer(text='Вы вошли как администратор.\nЧем я могу вам помочь?',
                             reply_markup=Admin.admin_kb)
        a = 1
    cur.execute("SELECT * FROM organizers WHERE user_id=?",
                (str(message.from_user.id),))
    organizers_exists = cur.fetchone() is not None
    if organizers_exists:
        await message.answer(text='Вы вошли как организатор.\nЧем я могу вам помочь?',
                             reply_markup=Organizer.organizer_kb)
        a = 1
    if a == 0:
        await message.answer(text='Приветствую! Выберите вашу должность',
                             reply_markup=User.enter_reply)
