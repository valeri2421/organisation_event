#хендлеры, обрабатывающие действия организаторов
from aiogram import F, Router, Dispatcher
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods
from keyboards.keyboard_utils import Organizer

db = sq.connect('system_bd.db')
cur = db.cursor()
name_event = []
router = Router()
dispatcher = Dispatcher()

class Review(StatesGroup):
    awaiting_login_organizer = State()
    awaiting_pin_organizer = State()
    awaiting_for_number_event = State()




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

@router.message(F.text == 'Сметы')
async def add_smeta(message: Message, state: FSMContext):
    await message.answer(text='Выберите номер мероприятия, у которого посмотреть смету')
    cur.execute("""
            SELECT name FROM events""")
    events = cur.fetchall()
    res = ""
    for i in range(len(events)):
        res += f'№{i + 1} ' + events[i][0] + '\n'
    await message.answer(res)
    await state.set_state(Review.awaiting_for_number_event)


@router.message(Review.awaiting_for_number_event)
async def organizer_event_smeta(message: Message, state: FSMContext):
    global name_event
    cur.execute("SELECT * FROM events")
    ev = cur.fetchall()
    st = message.text
    if st.isnumeric():
        if int(st) > 0 and int(st) <= len(ev):
            await message.answer(text='Выбрано мероприятие №%s' % (st))
            await state.clear()
            res, name, data = methods.bd_req(ev, int(st) - 1) # да или нет - есть ли смета
            if res == 'да':
                try:
                    template_path = FSInputFile(f'./сметы/смета_{data[8:10]+"."+data[5:7]+"."+data[:4]}_{name}.xlsx')
                    await message.answer_document(template_path, caption='Смета мероприятия')
                except:
                    await message.answer(text='Файл не найден')
            else:
                file1 = f'./тз/тз_{data[8:10]+"."+data[5:7]+"."+data[:4]}_{name}.xlsx'
                name_event = [name, file1, f'./сметы/смета_{data[8:10]+"."+data[5:7]+"."+data[:4]}_{name}.xlsx']
                file = FSInputFile(file1)
                await message.answer_document(file, caption='Техническое задание на мероприятие')
                await message.answer(text='У данного мероприятия нет сметы. Хотите составить?', reply_markup=Organizer.org_kb_but)
                #await methods.compilation_estimate(name, data[8:10]+"."+data[5:7]+"."+data[:4], message)  #составление сметы
        else:
            await message.answer(text='Вы ввели неверный номер мероприятия')
            await state.clear()
    else:
        await message.answer(text='Вы ввели не номер мероприятия')
        await state.clear()


@router.message(F.text == 'Начать составление сметы')
async def create_estimate(message: Message):
    await message.answer(text="Выбор отдела для сметы", reply_markup=Organizer.estimate_but)

@router.message(F.text == 'Видео оборудование')
async def video_eq(message: Message):
    global name_event
    k = methods.video(name_event)
    if len(k) == 0:
       await message.answer(text='Для этого мероприятия видео оборудование не нужно')
    else:
        await message.answer(text=k)




@router.message(F.text == 'Выйти в главное меню')
async def end_main(message: Message):
    await message.answer(text="Вы вышли в главное меню", reply_markup=Organizer.organizer_kb)



@router.message(F.text == 'Выйти')
async def end_session2(message: Message):
    cur.execute("""UPDATE organizers
            SET user_ID = NULL WHERE orgID = 8""")
    db.commit()
    await message.answer(text="Вы вышли из системы, нажмите /start для входа", reply_markup=ReplyKeyboardRemove())

