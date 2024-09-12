import calendar
import datetime
from collections.abc import Iterator
from typing import Optional

FIRST_PUBSTANDARDS = datetime.date(year=2005, month=12, day=14)

# Hiatuses where the Algorithm has been suspended and event numbering stops.
# The end date can be None if the hiatus is ongoing.
# These dates are inclusive
HIATUSES: list[tuple[datetime.date, Optional[datetime.date]]] = [
    # COVID-19 induced. The March 2020 event didn't happen.
    (datetime.date(2020, 2, 14), datetime.date(2024, 8, 31)),
]


def calc_middle_thursday(year, month) -> int:
    """Calculate the day number of the "middle Thursday" of a month.

    There are many ways of calculating the middle Thursday, but this one is ours:
    The Thursday of the week containing the middle day of the month, rounded down.
    """
    _, days_in_month = calendar.monthrange(year, month)
    middle_of_month = days_in_month // 2
    date = datetime.date(year, month, middle_of_month)
    return middle_of_month - (date.weekday() - 3)


def gen_ps_dates(start=None, ignore_hiatuses=False) -> Iterator[datetime.date]:
    """Return an iterator of all Pub Standards dates, starting at the provided date.

    This iterator will not terminate unless we are currently in a hiatus.

    Hiatuses can optionally be ignored, but this is probably not what you want unless
    you're another function in this module.
    """
    if start is None:
        start = FIRST_PUBSTANDARDS

    if start.day > calc_middle_thursday(start.year, start.month):
        # Our start day is after the middle thursday of its month. Roll over to the next month.
        start = datetime.date(
            year=start.year, month=start.month, day=1
        ) + datetime.timedelta(days=31)

    while True:
        middle_thursday = calc_middle_thursday(start.year, start.month)

        date = datetime.date(
            year=start.year,
            month=start.month,
            day=middle_thursday,
        )

        if not ignore_hiatuses:
            for hiatus_start, hiatus_end in HIATUSES:
                if date >= hiatus_start:
                    if not hiatus_end:
                        # We're in a hiatus which has no end date.
                        return
                    if date <= hiatus_end:
                        break
            else:
                yield date
        else:
            yield date

        start = datetime.date(
            year=start.year, month=start.month, day=1
        ) + datetime.timedelta(days=31)


def count_events_in_range(
    start: datetime.date, end: datetime.date, ignore_hiatuses=False
) -> int:
    """Count the number of PS events in a given range."""
    if start > end:
        raise ValueError(f"Start date {start} is after end date {end}")

    count = 0
    for date in gen_ps_dates(start=start, ignore_hiatuses=ignore_hiatuses):
        if date > end:
            break
        count += 1

    return count


def ps_offset_from_date(date: datetime.date) -> int:
    """Get the number of a Pub Standards event held on a given date. Numbering starts at 1.

    ValueError will be raised if the provided date is not a PS date.
    """
    if date < FIRST_PUBSTANDARDS:
        raise ValueError(f"Date {date} is before the Pub Standards era")

    if date.day != calc_middle_thursday(date.year, date.month):
        raise ValueError(f"Date {date} is not a Pub Standards date")

    offset = (
        (date.year - FIRST_PUBSTANDARDS.year) * 12
        + date.month
        - FIRST_PUBSTANDARDS.month
    )

    for hiatus_start, hiatus_end in HIATUSES:
        if date >= hiatus_start:
            if not hiatus_end or date <= hiatus_end:
                raise ValueError(f"Date {date} is during a Pub Standards hiatus")

            if date > hiatus_end:
                offset -= count_events_in_range(
                    hiatus_start, hiatus_end, ignore_hiatuses=True
                )

    return offset + 1


def ps_date_from_offset(integer: int) -> Optional[datetime.date]:
    """Get the date of a Pub Standards event given its number. Numbering starts at 1.

    This function may return None if we are currently in a hiatus and the event number
    is in the future.
    """
    if integer < 1:
        raise ValueError(f"Offset {integer} is less than 1")

    for count, date in enumerate(gen_ps_dates()):
        if count == integer - 1:
            return date

    return None


def next_ps_date():
    """Return the next Pub Standards date after today."""
    now = datetime.date.today()
    return next(gen_ps_dates(start=now))
