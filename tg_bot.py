import datetime
import json
import requests
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import hbold, hlink, hunderline, hcode, hspoiler

from config import token
from hepler import correct_date

load_dotenv()

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot, storage=MemoryStorage())


class UserData(StatesGroup):
    login = State()
    password = State()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(types.InlineKeyboardButton("Ввести учетные данные", callback_data="login"))
    await message.answer("Добро пожаловать! Чтобы узнать состояние Вашего счета, нажмите на кнопку ниже.",
                         reply_markup=button)


@dp.callback_query_handler()
async def callback(call):
    if call.data == "login":
        await start_logging_in(call.message)
    if call.data == "hear_my_knowledge":
        await call.message.answer("Обновляю...")
        await get_info(call.message)


@dp.message_handler(commands=["login"], state=None)
async def start_logging_in(message: types.Message):
    await UserData.login.set()
    await message.answer("Введите Ваш логин:")


@dp.message_handler(state=UserData.login)
async def login_user_data(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data["login"] = message.text
    await UserData.next()
    await message.answer("Введите пароль:")


@dp.message_handler(state=UserData.password)
async def get_info(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data["password"] = message.text
    await state.finish()
    await bot.delete_message(message.chat.id, message.message_id)
    login_data = {
        'user': data["login"],
        'password': data["password"]
    }

    req = requests.post(os.getenv('URL'), data=login_data)

    data = req.json()

    if data != 0:
        button = types.InlineKeyboardMarkup()
        button.add(types.InlineKeyboardButton("Пополнить счет", callback_data="i_will_have_mora"))
        button.add(types.InlineKeyboardButton("Открыть обещанный платеж", callback_data="turn_to_oblivion"))
        button.add(types.InlineKeyboardButton("Обновить информацию", callback_data="hear_my_knowledge"))

        if data["credit_date"] == "0000-00-00":
            credit = "не открыт"
        else:
            credit = data["credit_date"]

        await message.answer(
            f'{hbold("Абонент")}: {data["fio"]}\n{hbold("Логин")}: {data["id"]}     {hbold("UID")}: {data["uid"]}\n'
            f'{hbold("Дата окончания")}: {correct_date(data["expire"])}\n'
            f'{hbold("Остаток на счете")}: {data["deposit"]} руб.\n{hbold("Тариф")}: {data["tariff"]}\n'
            f'{hbold("Обещанный платеж")}: {credit}', reply_markup=button)

    else:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз", callback_data="login"))
        await message.answer("Неправильный логин или пароль!", reply_markup=fail_button)


if __name__ == '__main__':
    executor.start_polling(dp)
