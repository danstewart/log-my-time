from dataclasses import dataclass


@dataclass
class TimeStats:
    logged_this_week: str
    logged_today: str
    remaining_this_week: str
    remaining_today: str
    overtime: str
    estimated_finish_time: str
