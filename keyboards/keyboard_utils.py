#Вспомогательные функции/методы, помогающие формировать клавиатуры.

from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup, ReplyKeyboardRemove)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

class User:
    # --------Создаем кнопку входа----------
    button1 = KeyboardButton(text='Администратор')
    button2 = KeyboardButton(text='Организатор')

    enter_reply_builder = ReplyKeyboardBuilder()
    enter_reply_builder.add(button1, button2)

    # Создаем клавиатуру с кнопкой
    enter_reply: ReplyKeyboardMarkup = enter_reply_builder.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
class Admin:
    button1 = KeyboardButton(text='Добавить мероприятие')
    button2 = KeyboardButton(text='Проверить наличие сметы')
    button3 = KeyboardButton(text='Назначить организаторов')
    button4 = KeyboardButton(text='Изменить статус мероприятия')
    button5 = KeyboardButton(text='Список текущих мероприятий')
    button6 = KeyboardButton(text='Выйти из системы')
    admin_kb_builder = ReplyKeyboardBuilder()
    # Добавляем кнопки в билдер
    admin_kb_builder.row(button1, button2, button3,
                         button4, button5, button6, width=2)
    # Создаем клавиатуру с кнопками
    admin_kb: ReplyKeyboardMarkup = admin_kb_builder.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
# кнопки для согласования сметы
class Estimate:
    yes_button = KeyboardButton(text="Да")
    no_button = KeyboardButton(text="Нет")

    estimate_kb_builder = ReplyKeyboardBuilder()
    estimate_kb_builder.row(yes_button, no_button)

    estimate_kb: ReplyKeyboardMarkup = estimate_kb_builder.as_markup(
        resize_keyboard=True
    )
class Organizer:
    button1 = KeyboardButton(text='Предстоящие мероприятия')
    button2 = KeyboardButton(text='Записаться на мероприятие')
    button3 = KeyboardButton(text='Посмотреть тз')
    button4 = KeyboardButton(text='Сметы')
    button5 = KeyboardButton(text='Выйти из системы')
    organizer_kb_builder = ReplyKeyboardBuilder()

    organizer_kb_builder.row(button1, button2, button3,
                             button4, button5, width=2)
    # Создаем клавиатуру с кнопками
    organizer_kb: ReplyKeyboardMarkup = organizer_kb_builder.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
    but1 = KeyboardButton(text='Начать составление сметы')
    but2 = KeyboardButton(text='Выйти в главное меню')
    organizer_kb_but = ReplyKeyboardBuilder()
    organizer_kb_but.row(but1, but2, width=2)
    org_kb_but: ReplyKeyboardMarkup = organizer_kb_but.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )

    sound = KeyboardButton(text='Звуковое оборудование')
    video = KeyboardButton(text='Видео оборудование')
    light = KeyboardButton(text='Световое оборудование')
    swith = KeyboardButton(text='Коммутация и прочее')
    see_estimate = KeyboardButton(text='Показать смету')
    estimate_but_key = ReplyKeyboardBuilder()
    estimate_but_key.row(sound, video, light, swith, but2, see_estimate, width=2)
    estimate_but: ReplyKeyboardMarkup = estimate_but_key.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )

    app_eq = KeyboardButton(text='Добавить оборудование')
    app_people = KeyboardButton(text='Добавить инженеров и дежурных')
    end_app = KeyboardButton(text='Завершить добавление')
    estimate_2 = ReplyKeyboardBuilder()
    estimate_2.row(app_eq, app_people, end_app, width=2)
    estimate_: ReplyKeyboardMarkup = estimate_2.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )