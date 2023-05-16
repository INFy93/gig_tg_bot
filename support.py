import os

from dotenv import load_dotenv

from aiogram import types
from redminelib import Redmine


load_dotenv()

redmine = Redmine(os.getenv("REDMINE_URL"), key=os.getenv("REDMINE_API"))


async def store_issue_to_redmine(login, phone, problem, message: types.Message):
    issue = redmine.issue.new()
    issue.project_id = 'montazh'
    issue.subject = f'Обращение в техподдержку: {login} ({phone})'
    issue.description = problem
    issue.assigned_to_id = 84  # потом можно сменить
    issue.save()

    await message.answer("Ваше обращение успешно отправлено! Ждите, вам перезвонят (но это не точно...)")


