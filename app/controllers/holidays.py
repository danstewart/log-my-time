from datetime import date
from typing import Optional

from app.controllers import settings


def get_holiday_location() -> tuple[str, str]:
    _settings = settings.fetch()
    if location := _settings.holiday_location:
        return tuple(location.split("/", 2))  # type: ignore
    raise ValueError("No `holiday_location` configured")


def get_next_public_holiday() -> Optional[dict]:
    """
    Get the next public holiday
    """
    import datetime

    import holidays

    today = datetime.date.today()
    current_year = today.year
    next_year = current_year + 1

    country, region = get_holiday_location()
    for year in (current_year, next_year):
        h = holidays.country_holidays(country, subdiv=region, years=[year])
        for dt, name in h.items():
            if dt > today:
                return {"name": name, "date": dt}


def get_upcoming_holidays() -> dict[date, str]:
    """
    Get all holidays for the current year and the next year
    Returned as a dict of {date: name}
    """
    import holidays

    today = date.today()
    current_year = today.year
    next_year = current_year + 1

    next_holidays = {}

    country, region = get_holiday_location()
    for year in (current_year, next_year):
        h = holidays.country_holidays(country, subdiv=region, years=[year])
        for dt, name in h.items():
            if dt >= today:
                next_holidays.update({dt: name})

    return dict(sorted(next_holidays.items()))


def get_previous_holidays() -> dict[str, date]:
    """
    Get all passed holidays for the current year and the previous year
    Returned as a dict of {date: name}
    """
    import holidays

    today = date.today()
    current_year = today.year
    last_year = current_year - 1

    previous_holidays = {}

    country, region = get_holiday_location()
    for year in (current_year, last_year):
        h = holidays.country_holidays(country, subdiv=region, years=[year])
        for dt, name in h.items():
            if dt < today:
                previous_holidays.update({dt: name})

    return dict(sorted(previous_holidays.items()))
