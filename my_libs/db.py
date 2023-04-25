import datetime
import sqlite3
import os
from array import array

from dotenv import load_dotenv

load_dotenv()


def connect():
    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, tg_id int, uid int, '
                'login varchar(100), login_time timestamp, end_session_time timestamp)')
    conn.commit()
    cur.close()
    conn.close()


def add_user_to_table(tg_id, uid, login):
    tg_id = int(tg_id)
    uid_int = int(uid)

    current_date = datetime.datetime.now()
    end_session_time = current_date + datetime.timedelta(minutes=float(os.getenv('LIFE_SESSION_TIME')))

    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()
    check_q = cur.execute(f'SELECT * from users WHERE tg_id = "{tg_id}"')
    check = check_q.fetchall()
    if len(check) == 0:
        cur.execute('INSERT INTO users (tg_id, uid, login, login_time, end_session_time) VALUES(?, ?, ?, ?, ?)',
                    (tg_id, uid_int, login, current_date, end_session_time))
        conn.commit()
        cur.close()
        conn.close()
    else:
        cur.execute(f'UPDATE users SET end_session_time = "{end_session_time}" WHERE tg_id = "{tg_id}"')
        conn.commit()
        cur.close()
        conn.close()


def check_user(login):
    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()
    cur.execute(f'SELECT * from users WHERE login = "{login}"')
    checking = cur.fetchall()

    cur.close()
    conn.close()
    is_present = len(checking)

    if is_present == 0:
        return False
    else:
        return True


def check_session(tg_id):
    time = datetime.datetime.now()

    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()
    cur.execute(f'SELECT uid, end_session_time from users WHERE tg_id = "{tg_id}"')
    end_session_time = cur.fetchall()
    cur.close()
    conn.close()
    data = []

    for el in end_session_time:
        data.append(el[0])
        data.append(el[1])

    session_time = datetime.datetime.strptime('%s' % data[1], '%Y-%m-%d %H:%M:%S.%f')

    if time > session_time:
        return False
    else:
        return data

