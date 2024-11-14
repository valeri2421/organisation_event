#хендлеры, обрабатывающие действия организаторов
from aiogram import F, Router, Dispatcher
from aiogram.types import Message
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods
from keyboards.keyboard_utils import Organizer

db = sq.connect('system_bd.db')
cur = db.cursor()

router = Router()
dispatcher = Dispatcher()

class Review(StatesGroup):
    awaiting_login_organizer = State()
    awaiting_pin_organizer = State()




# Этот хэндлер срабатывает на нажатие кнопки "Организатор"
@router.message(F.text == 'Организатор')
async def organizer_login(message: Message, state: FSMContext):
    await message.answer(text='Введите ваш логин')
    await state.set_state(Review.awaiting_login_organizer)


@router.message(Review.awaiting_login_organizer)
async def organizer_login_pin(message: Message, state: FSMContext):
    cur.execute("SELECT * FROM organizers")
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[4]:
            await message.answer(text='Введите пароль')
            await state.set_state(Review.awaiting_pin_organizer)
            a = 1
            break
    if a != 1:
        await message.answer(text='Вы не зарегистрированы. '
                                  'В случае ошибки обратитесь к руководству.')
        await state.clear()

@router.message(Review.awaiting_pin_organizer)
async def employees_login(message: Message, state: FSMContext):
    cur.execute("SELECT * FROM organizers")
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[5]:
            await methods.add_organizer(message.from_user.id, message.text)
            await message.answer(text='Вы успешно вошли в систему в качестве Организатора!',
                                 reply_markup=Organizer.organizer_kb)
            # + клавиатура для сотрудников и меню для сотрудников??
            await state.clear()
            a = 1
            break
    if a != 1:
        await message.answer(text='Пароль неверный, повторите попытку.')
        await state.set_state(Review.awaiting_pin_organizer)

@router.message(F.text == 'Предстоящие мероприятия')
async def show_upcoming_events(message: Message):
    # Запрос мероприятий с датой начала после текущего времени
    cur.execute("""
        SELECT name, type, place, date_time_start, date_time_end, status, kol_org, estimate 
        FROM events 
        WHERE date_time_start >= datetime('now') 
        ORDER BY date_time_start
    """)
    events = cur.fetchall()

    if not events:
        await message.answer("На данный момент нет запланированных мероприятий.")
        return

    # Формируем сообщение с информацией о мероприятиях
    response = "Предстоящие мероприятия:\n"
    for event in events:
        response += (
            f"\nНазвание: {event[0]}\n"
            f"Тип: {event[1]}\n"
            f"Место: {event[2]}\n"
            f"Начало: {event[3]}\n"
            f"Конец: {event[4]}\n"
            f"Статус: {event[5]}\n"
            f"Количество организаторов: {event[6]}\n"
        )

    await message.answer(response)

@router.message(F.text == 'Записаться на мероприятие')
async def register_for_event(message: Message):
    # Запрашиваем список мероприятий, на которые можно записаться
    cur.execute("""
        SELECT e.eventsID, e.name, e.date_time_start, e.kol_org, COUNT(c.id_org) as current_count
        FROM events e
        LEFT JOIN connection_table c ON e.eventsID = c.id_event
        WHERE e.date_time_start >= datetime('now') 
        GROUP BY e.eventsID
        HAVING current_count < e.kol_org
    """)
    events = cur.fetchall()

    if not events:
        await message.answer("На данный момент нет мероприятий, доступных для регистрации.")
        return

    # Формируем сообщение с доступными мероприятиями
    response = "Мероприятия, доступные для записи:\n"
    for event in events:
        response += f"ID: {event[0]}, Название: {event[1]}, Дата начала: {event[2]}\n"
    response += "\nВведите ID мероприятия, на которое хотите записаться."

    # Отправляем сообщение с доступными мероприятиями
    await message.answer(response)

@router.message()
async def handle_event_registration(message: Message):
    try:
        #  ID мероприятия от пользователя
        event_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID мероприятия.")
        return

    #  orgID для текущего пользователя
    cur.execute("SELECT orgID FROM organizers WHERE user_id = ?", (message.from_user.id,))
    result = cur.fetchone()

    if not result:
        await message.answer("Вы не авторизованы как организатор.")
        return

    orgID = result[0]  # извлекаем orgID

    #  проверка, что мероприятие с указанным ID доступно для записи
    cur.execute("""
        SELECT e.kol_org, COUNT(c.id_org) as current_count
        FROM events e
        LEFT JOIN connection_table c ON e.eventsID = c.id_event
        WHERE e.eventsID = ?
        GROUP BY e.eventsID
        HAVING current_count < e.kol_org
    """, (event_id,))
    result = cur.fetchone()

    if not result:
        await message.answer("Мероприятие с указанным ID не найдено или все места уже заняты.")
        return

    # проверка, не записан ли уже организатор на это мероприятие
    cur.execute("SELECT COUNT(*) FROM connection_table WHERE id_event = ? AND id_org = ?", (event_id, orgID))
    already_registered = cur.fetchone()[0]

    if already_registered > 0:
        await message.answer("Вы уже записаны на это мероприятие.")
        return

    # запись организатора на мероприятие
    cur.execute("INSERT INTO connection_table (id_event, id_org) VALUES (?, ?)", (event_id, orgID))
    db.commit()

    await message.answer("Вы успешно записались на мероприятие!")

