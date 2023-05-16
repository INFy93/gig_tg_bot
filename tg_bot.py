import requests
import os

from aiogram.types import message
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.markdown import hbold
from aiogram.utils.callback_data import CallbackData

import support
import user_credit
from my_libs import db
from my_libs.hepler import correct_date

load_dotenv()

bot = Bot(token=os.getenv("TOKEN"), parse_mode=types.ParseMode.HTML)

dp = Dispatcher(bot, storage=MemoryStorage())


class UserData(StatesGroup):
    login = State()
    password = State()


class UserSupportQuery(StatesGroup):
    user_query = State()
    user_phone = State()


usr_data = CallbackData('usr_data', 'login', 'uid')
usr_action_data = CallbackData('usr_action', 'action', 'uid')


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(types.InlineKeyboardButton("Ввести учетные данные", callback_data=usr_action_data.new(action="login", uid=0)))
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
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0)))
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

    if data != 0:
        db.add_user_to_table(message.chat.id, data["uid"], data["id"])
        button = types.InlineKeyboardMarkup()
        button.add(
            types.InlineKeyboardButton("🔁 Обновить баланс",
                                       callback_data=usr_action_data.new(action="here_my_knowledge", uid=data["uid"])))
        button.add(types.InlineKeyboardButton("💸 Пополнить счет",
                                              callback_data=usr_action_data.new(action="i_will_have_mora",
                                                                                uid=data["uid"])))
        button.add(types.InlineKeyboardButton("🗓 Открыть обещанный платеж",
                                              callback_data=usr_action_data.new(action="turn_to_oblivion",
                                                                                uid=data["uid"])))
        button.add(types.InlineKeyboardButton("🚀 Оставить заявку",
                                              callback_data=usr_data.new(login=data["id"], uid=data["uid"])
                                              ))
        button.add(types.InlineKeyboardButton("🏄🏼‍♂️ Чат с оператором", url=os.getenv("JIVOSITE_LINK")))
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
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0)))
        await message.answer("Ошибка параметров", reply_markup=fail_button)
    else:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0)))
        await message.answer("Неправильный логин или пароль.", reply_markup=fail_button)


async def loan(message: types.Message, uid):
    await user_credit.open_credit(uid, message)


async def payment(message: types.Message):
    await message.answer("Функция находится в разработке")


@dp.callback_query_handler(usr_data.filter(), state=None)
async def vote_up_cb_handler(query: types.CallbackQuery, callback_data: dict, state=FSMContext):
    is_session = db.check_session(query.message.chat.id, callback_data["uid"])
    if is_session:
        await UserSupportQuery.user_query.set()
        await query.message.answer("Опишите вашу проблему:")
        async with state.proxy() as data:
            data["login"] = callback_data["login"]
            data["uid"] = is_session[0]
    else:
        auth_button = types.InlineKeyboardMarkup()
        auth_button.add(types.InlineKeyboardButton("Авторизоваться",
                                                   callback_data=usr_action_data.new(action="login", uid=0)))
        await query.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.", reply_markup=auth_button)


@dp.message_handler(state=UserSupportQuery.user_query)
async def set_phone(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data["problem"] = message.text
    await UserSupportQuery.next()
    await message.answer("Введите ваш номер телефона для связи:")
    # await support.store_issue_to_redmine(data["login"], data["problem"], message)


@dp.message_handler(state=UserSupportQuery.user_phone)
async def transfer_data(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        data["phone"] = message.text
    await state.finish()
    await support.store_issue_to_redmine(data["login"], data["phone"], data["problem"], message)


@dp.callback_query_handler(usr_action_data.filter())
async def _(query: types.CallbackQuery, callback_data: dict):
    action = callback_data['action']
    if action == "login":
        db.connect()
        await start_logging_in(query.message)
    elif action == "here_my_knowledge":
        is_session = db.check_session(query.message.chat.id, callback_data["uid"])
        if is_session:
            await query.message.answer("Обновляю...")
            await get_auth_info(query.message, is_session[0])
        else:
            auth_button = types.InlineKeyboardMarkup()
            auth_button.add(types.InlineKeyboardButton("Авторизоваться",
                                                       callback_data=usr_action_data.new(action="login", uid=0)))
            await query.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.", reply_markup=auth_button)
    elif action == "turn_to_oblivion":
        is_session = db.check_session(query.message.chat.id, callback_data["uid"])
        if is_session:
            await loan(query.message, callback_data["uid"])
        else:
            auth_button = types.InlineKeyboardMarkup()
            auth_button.add(types.InlineKeyboardButton("Авторизоваться",
                                                       callback_data=usr_action_data.new(action="login", uid=0)))
            await query.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.",
                                       reply_markup=auth_button)
    elif action == "i_will_have_mora":
        await payment(query.message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
