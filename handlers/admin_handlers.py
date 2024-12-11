#хендлеры, обрабатывающие действия админа
from keyboards.keyboard_utils import Admin, Estimate, StatusChange
from bot import bot
from aiogram import F, Router, Dispatcher, types
from aiogram.types import Message, ContentType, FSInputFile, ReplyKeyboardRemove
import sqlite3 as sq
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from methods_db import methods
import json
import os
import re

db = sq.connect('system_bd.db')
cur = db.cursor()

router = Router()
dispatcher = Dispatcher()
UPLOAD_FOLDER = './тз'

with open('./gueries.json') as f:
    queries = json.load(f)

class Review(StatesGroup):
    awaiting_login_administration = State()
    awaiting_pin_administration = State()
    waiting_for_excel = State()
    awaiting_event_id = State()
    awaiting_event_id_for_status = State()
    awaiting_status_change = State()
    awaiting_organizer_selection = State()
    awaiting_event_selection = State()

# Этот хэндлер срабатывает на нажатие кнопки "Администратор"
@router.message(F.text == 'Администратор')
async def administration_login(message: Message, state: FSMContext):
    await message.answer(text='Введите ваш логин')
    await state.set_state(Review.awaiting_login_administration)


@router.message(Review.awaiting_login_administration)
async def administration_login_pin(message: Message, state: FSMContext):
    cur.execute(queries['getAllAdmins'])
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
    cur.execute(queries['getAllAdmins'])
    items = cur.fetchall()
    a = 0
    for el in items:
        if message.text == el[5]:
            methods.add_administration(message.from_user.id, message.text)
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
        methods.add_event(file_path)
        await message.answer(text="Мероприятие добавлено", reply_markup=Admin.admin_kb)
        await state.clear()
    except Exception as e:
        await message.answer(text="Произошла ошибка при добавлении мероприятия: " + str(e),
                             reply_markup=Admin.admin_kb)
        await state.clear()


@router.message(F.text == 'Список текущих мероприятий')
async def show_events(message: Message):
    # Запрос на получение мероприятий из бд
    events = cur.execute(queries['getEventsInProcess']).fetchall()
    if not events:
        await message.answer("На данный момент нет запланированных мероприятий.")
        return

    # Формируем сообщение с информацией о мероприятиях
    response = ""
    for i in range(len(events)):
        org_kol = cur.execute(queries['EventInfo'] % (events[i][0])).fetchall()
        response += (
            f"\nМероприятие №{i+1}\n"
            f"\nID: {events[i][0]}\n"
            f"Название: {events[i][1]}\n"
            f"Тип: {events[i][2]}\n"
            f"Место: {events[i][3]}\n"
            f"Дата и время начала: {events[i][4]}\n"
            f"Дата и время окончания: {events[i][5]}\n"
            f"Статус: {events[i][6]}\n"
            f"Количество организаторов: {events[i][7]}\n"
            f"Назначенное кол-во организаторов: {org_kol[0][0]}\n"
            f"Смета: {events[i][8]}\n" 
            f"{'-' * 30}\n"
        )
    try:
        await message.answer(response)
    except Exception as e:
        await message.answer(text="Произошла ошибка при выводе: " + str(e),
                             reply_markup=Admin.admin_kb)

@router.message(F.text == 'Выйти из системы')
async def end_session1(message: Message):
    methods.delete_admin_id(message.from_user.id)
    await message.answer(text="Вы вышли из системы, нажмите /start для входа", reply_markup=ReplyKeyboardRemove())

async def get_event_list():
    cur.execute(queries["getEventList"])
    events = cur.fetchall()
    return events


@router.message(F.text == 'Проверить наличие сметы')
async def handle_check_budget(message: types.Message, state: FSMContext):
    # Получаем список мероприятий
    events = await get_event_list()

    if not events:
        await message.answer("В базе данных нет мероприятий.")
        return

    # Формируем строку с ID и названием мероприятий
    event_list_str = "Список текущих мероприятий:\n"
    for event in events:
        event_list_str += f"ID: {event[0]}, Название: {event[1]}\n"

    await message.answer(event_list_str)
    await message.answer("Пожалуйста, отправьте ID мероприятия для проверки наличия сметы.")
    await state.set_state(Review.awaiting_event_id)


# Функция для извлечения названия мероприятия из имени файла
def extract_event_name_from_filename(filename):
    match = re.match(r"смета_\d{2}\.\d{2}\.\d{4}_(.*)\.xlsx", filename)
    if match:
        return match.group(1).strip()  # Название мероприятия
    return None

@router.message(Review.awaiting_event_id, F.text.isdigit())
async def handle_event_id(message: types.Message, state: FSMContext):
    try:
        event_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID мероприятия.")
        return

    cur.execute(queries["getEventNameById"], (event_id,))
    result = cur.fetchone()

    if result:
        event_name = result[0]
        await message.answer(f"Вы выбрали мероприятие: '{event_name}'. Теперь проверим наличие сметы...")

        file_found = False
        file_path = None

        # Проходим по файлам в папке ./сметы
        for filename in os.listdir('./сметы'):
            # Извлекаем название мероприятия из имени файла
            extracted_name = extract_event_name_from_filename(filename)
            if extracted_name and event_name.lower() in extracted_name.lower():  # Сравниваем названия без учета регистра
                file_found = True
                file_path = os.path.join('./сметы', filename)
                break

        if file_found:
            await message.answer(f"Смета для мероприятия '{event_name}' найдена. Отправляю файл...")

            input_file = FSInputFile(file_path)
            await message.answer_document(input_file)

            # Спрашиваем согласование
            await message.answer("Согласовать смету?", reply_markup=Estimate.estimate_kb)

            # Сохраняем ID мероприятия
            await state.update_data(event_id=event_id)
        else:
            await message.answer(f"Смета для мероприятия '{event_name}' не найдена.")
    else:
        await message.answer("Мероприятие с таким ID не найдено в базе данных. Пожалуйста, проверьте ID и попробуйте снова.")

# Обработчик ответа на согласование сметы
@router.message(F.text.in_(["Да", "Нет"]))
async def handle_agreement(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data.get('event_id')

    if not event_id:
        await message.answer("Не удалось получить ID мероприятия. Пожалуйста, начните сначала.")
        return

    if message.text == "Да":
        # Обновляем статус сметы в базе данных
        cur.execute(queries["updateEstimateYes"], (event_id,))
        db.commit()
        await message.answer("Смета согласована.")
    else:
        cur.execute(queries["updateEstimateNo"], (event_id,))
        db.commit()
        await message.answer("Смета не согласована.")
    await message.answer("Главное меню:", reply_markup=Admin.admin_kb)

@router.message(F.text == 'Изменить статус мероприятия')
async def handle_change_status(message: types.Message, state: FSMContext):
    cur.execute(queries["getEventsWithStatus"])
    events = cur.fetchall()

    if not events:
        await message.answer("В базе данных нет мероприятий.")
        return

    event_list_str = "Список текущих мероприятий:\n"
    for event in events:
        event_list_str += f"ID: {event[0]}, Название: {event[1]}, Статус: {event[2]}\n"

    await message.answer(event_list_str)
    await message.answer("Пожалуйста, отправьте ID мероприятия, для которого хотите изменить статус.")
    await state.set_state(Review.awaiting_event_id_for_status)

@router.message(Review.awaiting_event_id_for_status, F.text.isdigit())
async def handle_event_id_for_status(message: types.Message, state: FSMContext):
    try:
        event_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID мероприятия.")
        return

    cur.execute(queries["getEventNameById"], (event_id,))
    result = cur.fetchone()

    if result:
        event_name = result[0]
        await state.update_data(event_id=event_id)
        await message.answer(
            f"Вы выбрали мероприятие: '{event_name}'. Выберите новый статус:",
            reply_markup=StatusChange.status_kb
        )
        await state.set_state(Review.awaiting_status_change)  # Переход в состояние изменения статуса
    else:
        await message.answer("Мероприятие с таким ID не найдено в базе данных. Пожалуйста, проверьте ID и попробуйте снова.")

@router.message(Review.awaiting_event_id_for_status, F.text.isdigit())
async def handle_event_id_for_status(message: types.Message, state: FSMContext):
    try:
        event_id = int(message.text)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID мероприятия.")
        return

    cur.execute(queries["getEventNameById"], (event_id,))
    result = cur.fetchone()

    if result:
        event_name = result[0]
        await state.update_data(event_id=event_id)
        await message.answer(
            f"Вы выбрали мероприятие: '{event_name}'. Выберите новый статус:",
            reply_markup=StatusChange.status_kb
        )
        await state.set_state(Review.awaiting_status_change)  # Переход в состояние изменения статуса
    else:
        await message.answer("Мероприятие с таким ID не найдено в базе данных. Пожалуйста, проверьте ID и попробуйте снова.")

@router.message(Review.awaiting_status_change, F.text.in_(["В процессе", "Закончено", "Отменено"]))
async def handle_status_change(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    event_id = user_data.get('event_id')

    if not event_id:
        await message.answer("Не удалось получить ID мероприятия. Пожалуйста, начните сначала.")
        return

    status_map = {
        "В процессе": "process",
        "Закончено": "end",
        "Отменено": "cancelled"
    }
    new_status = status_map[message.text]

    cur.execute(queries["updateEventStatus"], (new_status, event_id))
    db.commit()

    await message.answer(f"Статус мероприятия успешно изменён на '{message.text}'.", reply_markup=Admin.admin_kb)
    await state.clear()


@router.message(F.text == 'Назначить организаторов')
async def start_assign_organizers(message: Message, state: FSMContext):
    # Получаем список мероприятий с недостающими организаторами
    cur.execute(queries["getEventsWithout"])
    events = cur.fetchall()

    if not events:
        await message.answer("На данный момент нет мероприятий, доступных для регистрации.")
        return

    # Формируем сообщение с доступными мероприятиями
    response = "Мероприятия, доступные для записи:\n"
    for event in events:
        response += f"ID: {event[0]}, Название: {event[1]}, Дата начала: {event[2]}\n"

    response += "\nТеперь выберите ID мероприятия, для которого хотите назначить организаторов."

    await message.answer(response)
    await state.set_state(Review.awaiting_event_selection)


@router.message(Review.awaiting_event_selection)
async def handle_event_selection(message: Message, state: FSMContext):
    event_id = message.text

    # Проверка, что введен ID мероприятия
    if not event_id.isdigit():
        await message.answer("Пожалуйста, введите правильный ID мероприятия.")
        return

    event_id = int(event_id)

    # Получаем список организаторов, которые еще не назначены
    cur.execute(queries["getAvailableOrg"], (event_id,))
    available_organizers = cur.fetchall()

    if not available_organizers:
        await message.answer("Нет доступных организаторов для назначения.")
        return

    response = "Доступные организаторы:\n"
    for org in available_organizers:
        response += f"ID: {org[0]},  {org[1]}  {org[2]}\n"

    response += "\nВведите ID организатора, которого хотите назначить."

    await state.update_data(event_id=event_id)
    await message.answer(response)
    await state.set_state(Review.awaiting_organizer_selection)  # Переходим к состоянию выбора организатора


@router.message(Review.awaiting_organizer_selection)
async def handle_organizer_selection(message: Message, state: FSMContext):
    organizer_id = message.text

    # Проверка на корректность ввода ID организатора
    if not organizer_id.isdigit():
        await message.answer("Пожалуйста, введите правильный ID организатора.")
        return

    organizer_id = int(organizer_id)

    # Получаем данные о выбранном организаторе
    cur.execute(queries["getOrgId2"], (organizer_id,))
    organizer = cur.fetchone()

    if not organizer:
        await message.answer("Такого организатора не существует.")
        return

    user_data = await state.get_data()
    event_id = user_data.get("event_id")

    # Добавляем запись в таблицу connection
    cur.execute(queries["insertOrgToEvent"], (event_id, organizer_id))
    db.commit()

    await message.answer(f"Организатор с ID: {organizer_id} успешно назначен на мероприятие с ID: {event_id}.", reply_markup=Admin.admin_kb)
    await state.clear()