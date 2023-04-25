import datetime


def correct_date(date):
    if date == "0000-00-00":
        return "нет"

    month_names_array = [
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря'
    ]

    converted_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    converted_month = converted_date.month
    converted_day = converted_date.day
    converted_year = converted_date.year

    output = f'{converted_day} {month_names_array[converted_month - 1]} {converted_year}'

    return output
