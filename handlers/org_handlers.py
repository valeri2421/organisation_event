# хендлеры, обрабатывающие действия организаторов
from aiogram import F, Router, Dispatcher
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods
from keyboards.keyboard_utils import Organizer
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

db = sq.connect('system_bd.db')
cur = db.cursor()
name_event = []
router = Router()
dispatcher = Dispatcher()

with open('./gueries.json') as f:
    queries = json.load(f)

class Review(StatesGroup):
    awaiting_login_organizer = State()
    awaiting_pin_organizer = State()
    awaiting_for_number_event = State()
    awaiting_for_number_eq = State()
    awaiting_for_number_people = State()





# Этот хэндлер срабатывает на нажатие кнопки "Организатор"
@router.message(F.text == 'Организатор')
async def organizer_login(message: Message, state: FSMContext):
    await message.answer(text='Введите ваш логин')
    await state.set_state(Review.awaiting_login_organizer)


@router.message(Review.awaiting_login_organizer)
async def organizer_login_pin(message: Message, state: FSMContext):
    cur.execute(queries['getAllOrg'])
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
    cur.execute(queries['getAllOrg'])
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[5]:
            methods.add_organizer(message.from_user.id, message.text)
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
    cur.execute(queries['selectFutureEvents'])
    events = cur.fetchall()

    if not events:
        await message.answer("На данный момент нет запланированных мероприятий.")
        return

    # Формируем сообщение с информацией о мероприятиях
    response = "<b>Предстоящие мероприятия:</b>\n"
    for event in events:
        response += (
            f"\n<b>Название: {event[1]}</b>\n"
            f"Тип: {event[2]}\n"
            f"Место: {event[3]}\n"
            f"Начало: {event[4]}\n"
            f"Конец: {event[5]}\n"
            f"Статус: {event[6]}\n"
            f"Количество организаторов: {event[7]}\n"
        )

    await message.answer(response, reply_markup=Organizer.organizer_kb)

@router.message(F.text == 'Мои мероприятия')
async def show_my_events(message: Message):
    # Запрос мероприятий с датой начала после текущего времени
    cur.execute(queries['selectMyFutureEvents'], (message.from_user.id,))
    events = cur.fetchall()

    if not events:
        await message.answer("На данный момент у вас нет запланированных мероприятий.")
        return

    # Формируем сообщение с информацией о мероприятиях
    response = "<b>Ваши предстоящие мероприятия:</b>\n"
    for event in events:
        response += (
            f"\n<b>Название: {event[1]}</b>\n"
            f"Тип: {event[2]}\n"
            f"Место: {event[3]}\n"
            f"Начало: {event[4]}\n"
            f"Конец: {event[5]}\n"
            f"Статус: {event[6]}\n"
            f"Количество организаторов: {event[7]}\n"
        )

    await message.answer(response, reply_markup=Organizer.organizer_kb)

@router.message(F.text == 'Записаться на мероприятие')
async def registration_on_event(message: Message):
    cur.execute(queries['countOrg'])
    events = cur.fetchall()
    inline_keyboard = InlineKeyboardBuilder()
    # Создаем инлайн клавиатуру
    buttons = []
    for event in events:
        eventsID, name, required_organizers, registered_count = event
        if registered_count < required_organizers:
            buttons.append(InlineKeyboardButton(text=name, callback_data=f'register_{eventsID}_{name}'))

    for button in buttons:
        inline_keyboard.row(button)
    event_keyboard : InlineKeyboardMarkup = inline_keyboard.as_markup(one_time_keyboard=True)
    await message.answer(text='Выберете мероприятие, на которое хотели бы записаться', reply_markup=event_keyboard)
    if len(buttons) == 0:
        await message.answer("На все мероприятия уже записались достаточное количество организаторов.")

@router.callback_query(lambda callback: 'register_' in callback.data)
async def process_callback_button(callback: CallbackQuery):

    event_id = callback.data.split('_')[1]
    name = callback.data.split('_')[2]
    user_id = callback.from_user.id
    try:
        cur.execute(queries['getOrgId'], (user_id,))
        organizer = cur.fetchone()
        cur.execute(queries['IfAlreadyRegistered'], (event_id, organizer[0]))
        already_registered = cur.fetchone()
        if already_registered[0] == 0:
            if organizer:
                org_id = organizer[0]
                cur.execute(queries['insertOrgToEvent'], (event_id, org_id))
                db.commit()
                await callback.message.edit_reply_markup()
                await callback.message.answer(f"Вы успешно записались на мероприятие: {name}",
                                              reply_markup=Organizer.organizer_kb)
            else:
                await callback.message.edit_reply_markup()
                await callback.message.answer("Вы не являетесь организатором!", reply_markup=Organizer.organizer_kb)
        else:
            await callback.message.edit_reply_markup()
            await callback.message.answer("Вы уже записаны на это мероприятие.", reply_markup=Organizer.organizer_kb)
    except Exception as e:
        await callback.message.answer(f"Произошла ошибка при записи на мероприятие: {e}",
                                      reply_markup=Organizer.organizer_kb)
        await callback.answer()

@router.message(F.text == 'Посмотреть тз')
async def show_tz(message: Message):
    cur.execute(queries['selectFutureEvents'])
    events = cur.fetchall()
    inline_keyboard2 = InlineKeyboardBuilder()
    # Создаем инлайн клавиатуру
    buttons2 = []
    for event in events:
        buttons2.append(InlineKeyboardButton(text=event[1], callback_data=f'showtz_{event[1]}_{event[4][:10]}'))

    for button in buttons2:
        inline_keyboard2.row(button)
    all_event_keyboard: InlineKeyboardMarkup = inline_keyboard2.as_markup(one_time_keyboard=True)
    await message.answer(text='Выберите мероприятие, для которого хотели бы просмотреть тз', reply_markup=all_event_keyboard)

@router.callback_query(lambda callback: 'showtz_' in callback.data)
async def process_button_for_tz(callback: CallbackQuery):
    name = callback.data.split('_')[1]
    date = callback.data.split('_')[2]
    filetz = f'./тз/тз_{date[8:10]+"."+date[5:7]+"."+date[:4]}_{name}.xlsx'
    if filetz:
        file = FSInputFile(filetz)
        await callback.message.edit_reply_markup()
        await callback.message.answer_document(file, caption='Техническое задание на мероприятие.', reply_markup=Organizer.organizer_kb)
    else:
        await callback.message.edit_reply_markup()
        await callback.message.answer("На данное мероприятие еще не загружено техническое задание.", reply_markup=Organizer.organizer_kb)

@router.message(F.text == 'Сметы')
async def add_smeta(message: Message, state: FSMContext):
    await message.answer(text='Выберите номер мероприятия, у которого посмотреть смету')
    cur.execute(queries['nameEvent'])
    events = cur.fetchall()
    res = ""
    for i in range(len(events)):
        res += f'№{i + 1} ' + events[i][0] + '\n'
    await message.answer(res)
    await state.set_state(Review.awaiting_for_number_event)


@router.message(Review.awaiting_for_number_event)
async def organizer_event_smeta(message: Message, state: FSMContext):
    global name_event
    cur.execute(queries['getAllEvents'])
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
                await state.clear()
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
async def video_eq(message: Message, state: FSMContext):
    global name_event
    k = methods.video(name_event)
    if len(k) == 1:
       await message.answer(text='Для этого мероприятия видео оборудование не нужно')
    else:
        await message.answer(text=k[0], reply_markup=Organizer.estimate_)
        name_event.append(k[1])
        name_event.append('video')


@router.message(F.text == 'Звуковое оборудование')
async def video_eq(message: Message, state: FSMContext):
    global name_event
    k = methods.sound(name_event)
    if len(k[0]) == 0:
       await message.answer(text='Для этого мероприятия звуковое оборудование не нужно')
    else:
        await message.answer(text=k[0] + k[2], reply_markup=Organizer.estimate_)
        name_event.append(k[1])
        name_event.append('sound')


@router.message(F.text == 'Световое оборудование')
async def video_eq(message: Message, state: FSMContext):
    global name_event
    k = methods.light(name_event)
    if len(k[0]) == 0:
       await message.answer(text='Для этого мероприятия световое оборудование не нужно')
    else:
        await message.answer(text=k[0], reply_markup=Organizer.estimate_)
        name_event.append(k[1])
        name_event.append('light')

@router.message(F.text == 'Коммутация и прочее')
async def video_eq(message: Message, state: FSMContext):
    global name_event
    k = methods.other(name_event)
    await message.answer(text=k[0], reply_markup=Organizer.estimate_)
    name_event.append(k[1])
    name_event.append('other')

@router.message(F.text == 'Добавить оборудование')
async def app_eq(message: Message, state: FSMContext):
    await message.answer(text='Напишите номер оборудования, которое нужно добавить в формате: номер, количество', reply_markup=Organizer.estimate_)
    await state.set_state(Review.awaiting_for_number_eq)

@router.message(Review.awaiting_for_number_eq)
async def eq_state(message: Message, state: FSMContext):
    global name_event
    st = message.text
    if name_event[-1] == 'video':
        res = methods.add_eq_otdel('A3', name_event, st)
        if res[1]:
            await message.answer(text='Оборудование добавлено',
                             reply_markup=Organizer.estimate_)

        else:
            await message.answer(text='Оборудование не добавилось',
                                 reply_markup=Organizer.estimate_)
        name_event = res[0]
    elif name_event[-1] == 'sound':
        res = methods.add_eq_otdel('H3', name_event, st)
        if res[1]:
            await message.answer(text='Оборудование добавлено',
                                 reply_markup=Organizer.estimate_)

        else:
            await message.answer(text='Оборудование не добавилось',
                                 reply_markup=Organizer.estimate_)
        name_event = res[0]
    elif name_event[-1] == 'light':
        res = methods.add_eq_otdel('A20', name_event, st)
        if res[1]:
            await message.answer(text='Оборудование добавлено',
                                 reply_markup=Organizer.estimate_)

        else:
            await message.answer(text='Оборудование не добавилось',
                                 reply_markup=Organizer.estimate_)
        name_event = res[0]
    elif name_event[-1] == 'other':
        res = methods.add_eq_otdel('H20', name_event, st)
        if res[1]:
            await message.answer(text='Оборудование добавлено',
                                 reply_markup=Organizer.estimate_)

        else:
            await message.answer(text='Оборудование не добавилось',
                                 reply_markup=Organizer.estimate_)
        name_event = res[0]
    await state.clear()

@router.message(Review.awaiting_for_number_people)
async def people_state(message: Message, state: FSMContext):
    global name_event
    n = message.text
    j = methods.add_people_smeta(n, name_event)
    if j:
        await message.answer(text='Технические специалисты успешно добавлены!', reply_markup=Organizer.estimate_but)
    else:
        await message.answer(text='Произошла ошибка! Технические специалисты не добавлены', reply_markup=Organizer.estimate_but)
    await state.clear()



@router.message(F.text == 'Добавить инженеров')
async def app_eq(message: Message, state: FSMContext):
    t = 'Напишите, сколько человек требуется на мероприятие по тз в формате: кто - количество \n'
    t += 'Список: видеоинженер, художник по свету, звукорежиссер. Например, видеоинженер - 2, звукорежиссер - 2'
    await message.answer(text=t, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Review.awaiting_for_number_people)



@router.message(F.text == 'Показать смету')
async def see_smeta(message: Message):
    global name_event
    j = methods.status_smeta(name_event)
    if j:
        file = FSInputFile(name_event[2])
        await message.answer_document(file, caption='Смета на мероприятие!', reply_markup=Organizer.organizer_kb)
        name_event = []

    else:
        await message.answer(text='Смета не составлена на данное мероприятие', reply_markup=Organizer.estimate_but)

@router.message(F.text == 'Завершить добавление')
async def end_app(message: Message):
    await message.answer(text="Выберите следующий отдел для добавления оборудования", reply_markup=Organizer.estimate_but)


@router.message(F.text == 'Выйти в главное меню')
async def end_main(message: Message):
    await message.answer(text="Вы вышли в главное меню", reply_markup=Organizer.organizer_kb)



@router.message(F.text == 'Выйти из системы')
async def end_session2(message: Message):
    methods.delete_org_id(message.from_user.id)
    await message.answer(text="Вы вышли из системы, нажмите /start для входа", reply_markup=ReplyKeyboardRemove())

