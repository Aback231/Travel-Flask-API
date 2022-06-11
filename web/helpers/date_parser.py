import datetime
from dateutil import parser

ARRANGEMENT_DAYS_UNTIL_START = 5


def is_arrangement_reservable(date_start: str) -> bool:
    date_today = parser.parse(datetime.datetime.today().strftime('%m-%d-%Y'))
    date_start = parser.parse(date_start)

    delta = date_start - date_today

    if delta.days < ARRANGEMENT_DAYS_UNTIL_START:
        return False
    else:
        return True