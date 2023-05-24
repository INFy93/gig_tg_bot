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
from menus import main_menu
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
usr_action_data = CallbackData('usr_action', 'action', 'uid', 'login')


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    button = types.InlineKeyboardMarkup()
    button.add(
        types.InlineKeyboardButton("Ввести учетные данные", callback_data=usr_action_data.new(action="login", uid=0,
                                                                                              login='')))
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

    login_req = requests.post(os.getenv('USER_AUTH'), data=login_data)

    answer = login_req.json()

    if answer['status'] == 0:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0, login='')))
        await message.answer("Неправильный логин или пароль.", reply_markup=fail_button)
    else:
        await get_auth_info(message, answer['uid'])


async def get_auth_info(message: types.Message, uid):
    auth_user_data = {
        'uid': uid,
        'key': os.getenv("FILE_PASS")
    }

    user_req = requests.post(os.getenv('USER_INFO'), data=auth_user_data)

    user_answer = user_req.json()

    user_data = user_answer['user_info']
    user_status = user_answer['status']

    if user_status != 0:
        db.add_user_to_table(message.chat.id, user_data["uid"], user_data["id"])
        button = types.InlineKeyboardMarkup()
        button.add(types.InlineKeyboardButton("🔁 Финансовые операции",
                                              callback_data=usr_action_data.new(action="finance", uid=user_data["uid"],
                                                                                login='')))
        button.add(types.InlineKeyboardButton("🚀 Техподдержка",
                                              callback_data=usr_action_data.new(action="support",
                                                                                uid=user_data["uid"], login=user_data["id"])))
        if user_data["credit_date"] == "0000-00-00":
            credit = "не открыт"
        else:
            credit = user_data["credit_date"]

        await message.answer(
            f'{hbold("Абонент")}: {user_data["fio"]}\n{hbold("Логин")}: {user_data["id"]}\n'
            f'{hbold("Лицевой счет (UID)")}: {user_data["uid"]}\n'
            f'{hbold("Дата окончания")}: {correct_date(user_data["expire"])}\n'
            f'{hbold("Остаток на счете")}: {user_data["deposit"]} руб.\n{hbold("Тариф")}: {user_data["tariff"]}\n'
            f'{hbold("Обещанный платеж")}: {credit}', reply_markup=button)

    elif user_status == -1:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0, login='')))
        await message.answer("Ошибка параметров", reply_markup=fail_button)
    else:
        fail_button = types.InlineKeyboardMarkup()
        fail_button.add(types.InlineKeyboardButton("Попробовать еще раз",
                                                   callback_data=usr_action_data.new(action="login", uid=0, login='')))
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
                                                   callback_data=usr_action_data.new(action="login", uid=0, login='')))
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
    is_session = ''
    if action != "login":
        is_session = db.check_session(query.message.chat.id, callback_data["uid"])
    if action == "login":
        db.connect()
        await start_logging_in(query.message)
    elif action == "finance":
        if is_session:
            await main_menu.show_finance_menu(callback_data["uid"], query.message)
        else:
            auth_button = types.InlineKeyboardMarkup()
            auth_button.add(types.InlineKeyboardButton("Авторизоваться",
                                                       callback_data=usr_action_data.new(action="login", uid=0,
                                                                                         login='')))
            await query.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.", reply_markup=auth_button)
    elif action == "support":
        if is_session:
            await main_menu.show_support_menu(callback_data["uid"], callback_data["login"], query.message)
        else:
            auth_button = types.InlineKeyboardMarkup()
            auth_button.add(types.InlineKeyboardButton("Авторизоваться",
                                                       callback_data=usr_action_data.new(action="login", uid=0,
                                                                                         login='')))
            await query.message.answer("Ваша сессия истекла! Пожалуйста, авторизуйтесь снова.", reply_markup=auth_button)
    await query.answer()


if __name__ == '__main__':
    from menus import dp
    executor.start_polling(dp, skip_updates=False)
