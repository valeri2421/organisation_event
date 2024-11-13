#Модуль с методами для работы с БД.
import sqlite3 as sq
from datetime import datetime
from openpyxl import load_workbook

db = sq.connect('system_bd.db')
cur = db.cursor()

async def add_administration (user_id, pin):
    cur.execute("UPDATE administration SET user_ID = ? WHERE password = ?",
                (user_id, pin))
    db.commit()

async def add_organizer (user_id, pin):
    cur.execute("UPDATE organizers SET user_ID = ? WHERE password_org = ?",
                (user_id, pin))
    db.commit()

async def add_event(file_path):
# -----добавление мероприятия из екселя в бд-----
    wb = load_workbook(file_path)
    sheet = wb.active
    name = sheet['B3'].value
    type = sheet['B9'].value
    place = sheet['B4'].value
    date_time_start = datetime.strptime(sheet['B5'].value + ' ' + sheet['B6'].value, "%d.%m.%Y %H:%M")
    date_time_end = datetime.strptime(sheet['B7'].value + ' ' + sheet['B8'].value, "%d.%m.%Y %H:%M")
    date = datetime.now()
    if date < date_time_start:
        status = 'process'
    else:
        status = 'end'
    kol_org = 2
    if sheet['B12'].value == 'да' and type == 'гибрид': #Если есть трансляция, то к ним идет еще 1 организатор
        kol_org += 1
    estimate = 'нет'
    # Проверка на наличие мероприятия в БД
    k = cur.execute("""SELECT COUNT(*) FROM events WHERE name = ? AND date_time_start = ?""",
                    (name, date_time_start)).fetchone()[0]
    if k > 0:
        raise Exception('Мероприятие уже было добавлено')

    cur.execute("""INSERT INTO events (name, type, place, date_time_start, date_time_end, status, kol_org, estimate) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, type, place, date_time_start, date_time_end, status, kol_org, estimate))

    db.commit()

