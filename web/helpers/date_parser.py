import datetime
import config


def is_arrangement_reservable(date_start: datetime.date) -> bool:
    """ Validate arrangement is reservable, ARRANGEMENT_DAYS_UNTIL_START is treshold before event start """
    if not date_start > datetime.date.today() + datetime.timedelta(days=config.ARRANGEMENT_DAYS_UNTIL_START):
        return False
    return True


def is_tour_guide_available(date_start_occupied: str, date_end_occupied: str, date_start_validate: str, date_end_validate: str) -> bool:
    """ Validate Travel Guide available to for booking during arrangements time span """
    # Validation date difference
    diff = (date_start_validate - date_end_validate).days
    
    # Final logic
    diff_start_start = (date_start_validate - date_start_occupied).days
    diff_start_end = (date_start_validate - date_end_occupied).days

    if diff_start_start > 0 and diff_start_end > 0:
        return True
    elif diff_start_start < 0 and diff_start_end < 0 and (diff_start_start < diff and diff_start_end < diff):
        return True
    return False

