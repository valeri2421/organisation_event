#Вспомогательные функции/методы, помогающие формировать клавиатуры.

from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                           InlineKeyboardButton,
                           InlineKeyboardMarkup)
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
    button2 = KeyboardButton(text='Редактировать мероприятие')
    button3 = KeyboardButton(text='Назначить организаторов')
    button4 = KeyboardButton(text='Изменить статус мероприятия')
    button5 = KeyboardButton(text='Список текущих мероприятий')
    admin_kb_builder = ReplyKeyboardBuilder()
    # Добавляем кнопки в билдер
    admin_kb_builder.row(button1, button2, button3,
                         button4, button5, width=2)
    # Создаем клавиатуру с кнопками
    admin_kb: ReplyKeyboardMarkup = admin_kb_builder.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )

class Organizer:
    button1 = KeyboardButton(text='Предстоящие мероприятия')
    button2 = KeyboardButton(text='Записаться на мероприятие')
    button3 = KeyboardButton(text='Посмотреть тз')
    button4 = KeyboardButton(text='Составить смету')
    organizer_kb_builder = ReplyKeyboardBuilder()

    organizer_kb_builder.row(button1, button2, button3,
                             button4, width=2)
    # Создаем клавиатуру с кнопками
    organizer_kb: ReplyKeyboardMarkup = organizer_kb_builder.as_markup(
        one_time_keyboard=True,
        resize_keyboard=True
    )

