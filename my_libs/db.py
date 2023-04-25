import datetime
import sqlite3
import os

from dotenv import load_dotenv

load_dotenv()


def connect():
    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, uid int, login varchar(100), '
                'password varchar(200), login_time timestamp, end_session_time timestamp)')
    conn.commit()
    cur.close()
    conn.close()


def add_user_to_table(uid, login, password):
    uid_int = int(uid)

    current_date = datetime.datetime.now()
    end_session_time = current_date + datetime.timedelta(minutes=float(os.getenv('LIFE_SESSION_TIME')))

    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()
    cur.execute('INSERT INTO users (uid, login, password, login_time, end_session_time) VALUES(?, ?, ?, ?, ?)',
                (uid_int, login, password,
                 current_date, end_session_time))
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


def check_session(user_id):
    time = datetime.datetime.now()

    conn = sqlite3.connect("users.sqlite")
    cur = conn.cursor()
    cur.execute(f'SELECT end_session_time from users WHERE id = "{user_id}"')
    end_session_time = cur.fetchall()

    cur.close()
    conn.close()

    print(end_session_time)

