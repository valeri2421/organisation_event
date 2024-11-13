#хендлеры, обрабатывающие действия админа
from aiogram import F, Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import sqlite3 as sq
from lexicon import LEXICON_RU
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods

db = sq.connect('system_bd.db')
cur = db.cursor()

router = Router()
dispatcher = Dispatcher()

class Review(StatesGroup):
    awaiting_login_administration = State()
    awaiting_pin_administration = State()




# Этот хэндлер срабатывает на нажатие кнопки "Администратор"
@router.message(F.text == 'Администратор')
async def administration_login(message: Message, state: FSMContext):
    await message.answer(text='Введите ваш логин')
    await state.set_state(Review.awaiting_login_administration)


@router.message(Review.awaiting_login_administration)
async def administration_login_pin(message: Message, state: FSMContext):
    cur.execute("SELECT * FROM administration")
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[4]:
            await message.answer(text='Введите пароль')
            await state.set_state(Review.awaiting_pin_administration)
            a = 1
            break
    if a != 1:
        await message.answer(text='Вы не зарегистрированы. '
                                  'В случае ошибки обратитесь к руководству.')
        await state.clear()

@router.message(Review.awaiting_pin_administration)
async def employees_login(message: Message, state: FSMContext):
    cur.execute("SELECT * FROM administration")
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[5]:
            await methods.add_administration(message.from_user.id, message.text)
            await message.answer(text='Вы успешно вошли в систему в качестве Администратора!')
            # + клавиатура для сотрудников и меню для сотрудников??
            await state.clear()
            a = 1
            break
    if a != 1:
        await message.answer(text='Пароль неверный, повторите попытку.')
        await state.set_state(Review.awaiting_pin_administration)



# Этот хэндлер срабатывает на команду /help
@router.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['help'])

@router.message(Command(commands='info'))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['info'])