#Модуль с методами для работы с БД.
import sqlite3 as sq

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



