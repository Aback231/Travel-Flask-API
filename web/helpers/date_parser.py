import datetime
from dateutil import parser

def has_arrangement_5_days_to_start(date_start: str) -> bool:
    date_today = parser.parse(datetime.datetime.today().strftime('%m-%d-%Y'))
    date_start = parser.parse(date_start)

    delta = date_start - date_today

    if delta.days < 5:
        return False
    else:
        return True