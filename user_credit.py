import os

import requests
from dotenv import load_dotenv

from aiogram import types
from redminelib import Redmine

load_dotenv()


async def open_credit(uid, message: types.Message):
    user_data = {
        'uid': uid,
        'key': os.getenv("FILE_PASS")
    }

    req = requests.post(os.getenv("USER_CREDIT"), data=user_data)

    if req.text != "-1":
        await message.answer(req.text)
    elif req.text == "-1":
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз", callback_data="login"))
        await message.answer("Ошибка параметров", reply_markup=fail_button)
