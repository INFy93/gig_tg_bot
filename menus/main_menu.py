import os

import requests
from aiogram.utils.callback_data import CallbackData
from dotenv import load_dotenv

from aiogram import types
from redminelib import Redmine

import tg_bot
from tg_bot import dp
import support
from my_libs import db

menu_action_data = CallbackData('usr_action', 'action', 'uid')


async def show_finance_menu(uid, message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(
        types.InlineKeyboardButton("🔁 Обновить баланс",
                                   callback_data=menu_action_data.new(action="here_my_knowledge", uid=uid)))
    button.add(types.InlineKeyboardButton("💸 Пополнить счет",
                                          url=os.getenv("PAYMENT_LINK")))
    button.add(types.InlineKeyboardButton("🗓 Открыть обещанный платеж",
                                          callback_data=menu_action_data.new(action="turn_to_oblivion",
                                                                             uid=uid)))
    button.add(types.InlineKeyboardButton("⬅️ В главное меню",
                                          callback_data=menu_action_data.new(action="here_my_knowledge",
                                                                             uid=uid)))
    await message.answer("Выберите действие:", reply_markup=button)


async def show_support_menu(uid, login, message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(
        types.InlineKeyboardButton("🚀 Оставить заявку",
                                   callback_data=tg_bot.usr_data.new(login=login, uid=uid)))
    button.add(types.InlineKeyboardButton("🏄🏼‍♂️ Чат с оператором", url=os.getenv("JIVOSITE_LINK")))
    button.add(types.InlineKeyboardButton("⬅️ В главное меню",
                                          callback_data=menu_action_data.new(action="here_my_knowledge",
                                                                             uid=uid)))
    await message.answer("Выберите действие:", reply_markup=button)


@dp.callback_query_handler(menu_action_data.filter())
async def _(query: types.CallbackQuery, callback_data: dict):
    action = callback_data["action"]

    if action == "here_my_knowledge":
        await tg_bot.get_auth_info(query.message, callback_data["uid"])
    elif action == "turn_to_oblivion":
        await tg_bot.loan(query.message, callback_data["uid"])
    elif action == "i_will_have_mora":
        await tg_bot.payment(query.message)

    await query.answer()
