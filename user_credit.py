import os

import requests
from dotenv import load_dotenv

from aiogram import types
from redminelib import Redmine

from menus import main_menu

load_dotenv()


async def open_credit(uid, message: types.Message):
    user_data = {
        'uid': uid,
        'key': os.getenv("FILE_PASS")
    }

    req = requests.post(os.getenv("USER_CREDIT"), data=user_data)

    credit_answer = req.json()

    if credit_answer['status'] != -1:
        await message.answer(credit_answer['message'])
    elif credit_answer['status'] == -1:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=main_menu.menu_action_data.new
                                                   (action="here_my_knowledge", uid=uid)))
        await message.answer(credit_answer['message'], reply_markup=fail_button)
