import datetime
from dateutil import parser
import config


def is_arrangement_reservable(date_start: str) -> bool:
    """ Validate arrangement is reservable, ARRANGEMENT_DAYS_UNTIL_START is treshold before event start """
    date_today = parser.parse(datetime.datetime.today().strftime('%d-%m-%Y'), dayfirst=True)
    date_start = parser.parse(date_start, dayfirst=True)

    delta = date_start - date_today

    if delta.days < config.ARRANGEMENT_DAYS_UNTIL_START:
        return False
    else:
        return True


def is_tour_guide_available(date_start_occupied: str, date_end_occupied: str, date_start_validate: str, date_end_validate: str) -> bool:
    """ Validate Travel Guide available to for booking during arrangements time span """
    # Date tour guide is occupied
    date_start_occupied = parser.parse(date_start_occupied, dayfirst=True)
    date_end_occupied = parser.parse(date_end_occupied, dayfirst=True)
    # Validation date
    date_start_validate = parser.parse(date_start_validate, dayfirst=True)
    date_end_validate = parser.parse(date_end_validate, dayfirst=True)
    # Validation date difference
    diff = (date_start_validate - date_end_validate).days
    
    # Final logic
    diff_start_start = (date_start_validate - date_start_occupied).days
    diff_start_end = (date_start_validate - date_end_occupied).days

    if diff_start_start > 0 and diff_start_end > 0:
        return True
    elif diff_start_start < 0 and diff_start_end < 0 and (diff_start_start < diff and diff_start_end < diff):
        return True
    else:
        return False

