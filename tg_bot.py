import requests
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.markdown import hbold
from aiogram.utils.callback_data import CallbackData

from config import token
from my_libs import db
from my_libs.hepler import correct_date

load_dotenv()

bot = Bot(token=token, parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot, storage=MemoryStorage())

user_data = CallbackData("usr_d", "tg_id")


class UserData(StatesGroup):
    login = State()
    password = State()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(types.InlineKeyboardButton("Ввести учетные данные", callback_data="login"))
    await message.answer("Добро пожаловать! Чтобы узнать состояние Вашего счета, нажмите на кнопку ниже.",
                         reply_markup=button)


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

    login_req = requests.post(os.getenv('USER_CHECK'), data=login_data)

    if login_req.text == "0":
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз", callback_data="login"))
        await message.answer("Неправильный логин или пароль.", reply_markup=fail_button)
    else:
        await get_auth_info(message, login_req.text)


async def get_auth_info(message: types.Message, uid):
    auth_user_data = {
        'uid': uid,
        'key': os.getenv("FILE_PASS")
    }

    user_req = requests.post(os.getenv('USER_INFO'), data=auth_user_data)

    data = user_req.json()
    print(data)
    if data != 0:
        db.add_user_to_table(message.chat.id, data["uid"], data["id"])
        button = types.InlineKeyboardMarkup()
        button.add(types.InlineKeyboardButton("Пополнить счет", callback_data="i_will_have_mora"))
        button.add(types.InlineKeyboardButton("Открыть обещанный платеж", callback_data="turn_to_oblivion"))
        button.add(
            types.InlineKeyboardButton("Обновить информацию", callback_data="here_my_knowledge"))

        if data["credit_date"] == "0000-00-00":
            credit = "не открыт"
        else:
            credit = data["credit_date"]

        await message.answer(
            f'{hbold("Абонент")}: {data["fio"]}\n{hbold("Логин")}: {data["id"]}     {hbold("UID")}: {data["uid"]}\n'
            f'{hbold("Дата окончания")}: {correct_date(data["expire"])}\n'
            f'{hbold("Остаток на счете")}: {data["deposit"]} руб.\n{hbold("Тариф")}: {data["tariff"]}\n'
            f'{hbold("Обещанный платеж")}: {credit}', reply_markup=button)

    elif data == -1:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз", callback_data="login"))
        await message.answer("Ошибка параметров", reply_markup=fail_button)
    else:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз", callback_data="login"))
        await message.answer("Неправильный логин или пароль.", reply_markup=fail_button)


@dp.callback_query_handler()
async def callback(call):
    if call.data == "login":
        db.connect()
        await start_logging_in(call.message)
    if call.data == "here_my_knowledge":
        is_session = db.check_session(call.message.chat.id)
        if is_session:
            await call.message.answer("Обновляю...")
            print(is_session[0])
            await get_auth_info(call.message, is_session[0])
        else:
            auth_button = types.InlineKeyboardMarkup()
            auth_button.add(types.InlineKeyboardButton("Авторизоваться", callback_data="login"))
            await call.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.", reply_markup=auth_button)


if __name__ == '__main__':
    executor.start_polling(dp)
