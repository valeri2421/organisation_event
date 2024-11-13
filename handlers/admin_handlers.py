#хендлеры, обрабатывающие действия админа
from keyboards.keyboard_utils import Admin
from bot import bot
from aiogram import F, Router, Dispatcher
from aiogram.types import Message, ContentType, FSInputFile
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods
import os

db = sq.connect('system_bd.db')
cur = db.cursor()

router = Router()
dispatcher = Dispatcher()
UPLOAD_FOLDER = './тз'


class Review(StatesGroup):
    awaiting_login_administration = State()
    awaiting_pin_administration = State()
    waiting_for_excel = State()




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
            await message.answer(text='Вы успешно вошли в систему в качестве Администратора!',
                                 reply_markup=Admin.admin_kb)
            await state.clear()
            a = 1
            break
    if a != 1:
        await message.answer(text='Пароль неверный, повторите попытку.')
        await state.set_state(Review.awaiting_pin_administration)

# Этот хэндлер срабатывает на нажатие кнопки "Добавить мероприятие"
@router.message(F.text == 'Добавить мероприятие')
async def cmd_add_event(message: Message, state: FSMContext):
    template_path = FSInputFile('тз_дата_название мероприятия.xlsx')
    await message.answer_document(template_path, caption='<b>Пожалуйста, отправьте файл Excel с ТЗ на мероприятие.</b> '
                                                         'Заполните шаблон ниже в соответствии '
                                                         'с требованиями на мероприятие. Название файла должно быть '
                                                         'формата "тз_дата_название мероприятия".')
    await state.set_state(Review.waiting_for_excel)


@router.message(F.content_type == ContentType.DOCUMENT)
async def process_document(message: Message, state: FSMContext):
    # Проверка состояния
    current_state = await state.get_state()
    if current_state != 'Review:waiting_for_excel':
        return

    document = message.document
    file_info = await bot.get_file(document.file_id)
    file_path = os.path.join(UPLOAD_FOLDER, document.file_name)
    await bot.download_file(file_info.file_path, file_path) # Загрузка файла

    try:
        await methods.add_event(file_path)
        await message.answer(text="Мероприятие добавлено", reply_markup=Admin.admin_kb)
        await state.clear()
    except Exception as e:
        await message.answer(text="Произошла ошибка при добавлении мероприятия: " + str(e),
                             reply_markup=Admin.admin_kb)
        await state.clear()