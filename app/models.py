import arrow

from app.lib.database import db, pony


class Time(db.Entity):
    id = pony.PrimaryKey(int, auto=True)
    start = pony.Required(int)
    end = pony.Optional(int)
    note = pony.Optional(str)

    breaks = pony.Set("Break")

    def logged(self):
        """
        Return the total duration of a time entry in seconds
        With any breaks removed
        """
        now = arrow.utcnow().int_timestamp
        to_remove = sum([(_break.end or now) - _break.start for _break in self.breaks])
        end = self.end or now
        duration = end - self.start

        return duration - to_remove

    @classmethod
    def since(cls, timestamp):
        return pony.select(row for row in cls if row.start >= timestamp)


class Break(db.Entity):
    time = pony.Required(Time)
    start = pony.Required(int)
    end = pony.Optional(int)
    note = pony.Optional(str)


class Settings(db.Entity):
    id = pony.PrimaryKey(int, auto=True)
    timezone = pony.Required(str)
    week_start = pony.Required(int)
    hours_per_day = pony.Required(float)
    work_days = pony.Required(
        str
    )  # This is stored as a 7 char string, the day char if the day is a work day and a hyphen if not, eg: MTWTF--

    def work_days_list(self) -> list[str]:
        work_days = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day, day_name in zip(self.work_days, day_names):
            if day != "-":
                work_days.append(day_name)
        return work_days

    def total_work_days(self):
        return sum([1 if day != "-" else 0 for day in self.work_days])
