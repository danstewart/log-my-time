from typing import Literal, Optional, Self

import arrow
import sqlalchemy as sa
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app import Model, db
from app.types import DayOfWeek0Indexed, TimeInSeconds

UnixTimestamp = int
DurationDays = float

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class BaseModel(Model):  # type: ignore
    __abstract__ = True

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True, autoincrement=True)

    @declared_attr  # type: ignore
    def __tablename__(cls):
        import re

        table_name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()  # type: ignore
        table_name = re.sub(r"__+", "_", table_name)
        return table_name

    @classmethod
    def from_id(cls, id: str) -> Self:
        return db.session.scalars(sa.select(cls).filter_by(id=id)).one()

    @classmethod
    def maybe_from_id(cls, id: str) -> Self | None:
        return db.session.scalars(sa.select(cls).filter_by(id=id)).one_or_none()

    def update(self, **kwargs):
        """
        This function allows calling Model.update(field1=val1, field2=val2, ...)
        The main purpose of this is compatability with VersionAlchemy as Session.execute(update())
        skips the ORM and VersionAlchemy
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def asdict(self, exclude: list | None = None):
        result = {}
        for field in self.fields():
            if exclude and field in exclude:
                continue
            result[field] = getattr(self, field)
        return result

    @classmethod
    def fields(cls):
        """
        Return a list of the columns
        """
        return [col.name for col in cls.__table__.columns]  # type: ignore


class TimeHelperMixin:
    """
    Add some helpers for time based models

    Models must have `start` and `user_id` columns
    """

    start: Mapped[UnixTimestamp] = mapped_column(sa.Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    @classmethod
    def since(cls, timestamp: int):
        """
        Get all records that started on or after the provided timestamp
        """
        from app.controllers.user.util import get_user

        user = get_user()
        return db.session.scalars(sa.select(cls).filter(cls.start >= timestamp, cls.user_id == user.id)).all()

    @classmethod
    def between(cls, start: int, end: int):
        """
        Get all records that started between the provided start and end timestamps
        """
        from app.controllers.user.util import get_user

        user = get_user()
        return db.session.scalars(
            sa.select(cls).filter(cls.start >= start, cls.start <= end, cls.user_id == user.id)
        ).all()


class User(BaseModel):
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    verified: Mapped[Optional[bool]] = mapped_column(sa.Boolean, default=False, nullable=False)
    last_seen_whats_new: Mapped[Optional[int]] = mapped_column(sa.Integer, sa.ForeignKey("whats_new.id"), nullable=True)
    is_admin: Mapped[Optional[bool]] = mapped_column(sa.Boolean)
    last_login_at: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)

    sessions: Mapped[list["LoginSession"]] = relationship(
        "LoginSession", back_populates="user", cascade="all, delete-orphan"
    )
    settings: Mapped["Settings"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    times: Mapped[list["Time"]] = relationship("Time", back_populates="user", cascade="all, delete-orphan")
    leaves: Mapped[list["Leave"]] = relationship("Leave", back_populates="user", cascade="all, delete-orphan")
    slack_tokens: Mapped[list["UserToSlackToken"]] = relationship(
        "UserToSlackToken", back_populates="user", cascade="all, delete-orphan"
    )

    def verify(self):
        """
        Sets `user.verified` to True and commits
        """
        self.verified = True
        db.session.commit()

    def set_password(self, password: str) -> "User":
        """
        Update the given users password
        """
        self.password = PasswordHasher().hash(password)
        db.session.commit()
        return self

    def check_password(self, password: str) -> bool:
        """
        Check if the provided password is correct for a given account
        """
        if not self.password:
            return False

        try:
            PasswordHasher().verify(self.password, password)
        except VerifyMismatchError:
            return False
        return True


class UserToSlackToken(BaseModel):
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)
    slack_token: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    team_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    user: Mapped[User] = relationship("User", viewonly=True, back_populates="slack_tokens")


class LoginSession(BaseModel):
    # Unique session ID, stored in user cookies
    key: Mapped[str] = mapped_column(sa.String(255), unique=True, nullable=False)
    expires: Mapped[UnixTimestamp] = mapped_column(sa.Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    user: Mapped[User] = relationship("User", viewonly=True, back_populates="sessions")

    @property
    def created_at(self) -> arrow.Arrow:
        expires = arrow.get(self.expires)
        return expires.shift(hours=7 * 24 * -1)


class Time(TimeHelperMixin, BaseModel):
    start: Mapped[UnixTimestamp] = mapped_column(sa.Integer, nullable=False)
    end: Mapped[Optional[UnixTimestamp]] = mapped_column(sa.Integer, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    breaks: Mapped[list["Break"]] = relationship(
        "Break", lazy=True, back_populates="time", cascade="all, delete-orphan"
    )
    user: Mapped[User] = relationship("User", viewonly=True, back_populates="times")

    def logged(self):
        """
        Return the total duration of a time entry in seconds
        With any breaks removed
        """
        now = arrow.utcnow().int_timestamp
        to_remove = sum([(_break.end or now) - _break.start for _break in self.breaks], start=0)
        end = self.end or now
        duration = end - self.start

        return duration - to_remove


class Break(BaseModel):
    time_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("time.id"))
    start: Mapped[UnixTimestamp] = mapped_column(sa.Integer)
    end: Mapped[Optional[UnixTimestamp]] = mapped_column(sa.Integer, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    time: Mapped[Time] = relationship("Time", viewonly=True, back_populates="breaks")

    @property
    def duration_pretty(self) -> str:
        minutes = self.duration / 60
        return f"{minutes} minutes" if minutes != 1 else "1 minute"

    @property
    def duration(self) -> TimeInSeconds:
        """
        Return the duration of this break in minutes
        """
        if self.end:
            diff = arrow.get(self.end) - arrow.get(self.start)
        else:
            diff = arrow.now() - arrow.get(self.start)

        duration_in_seconds = int(diff.total_seconds())
        return duration_in_seconds


class Leave(TimeHelperMixin, BaseModel):
    leave_type: Mapped[str] = mapped_column(sa.String(255), nullable=False)  # sick / annual
    start: Mapped[UnixTimestamp] = mapped_column(sa.Integer, nullable=False)
    duration: Mapped[DurationDays] = mapped_column(sa.Float, nullable=False)
    public_holiday: Mapped[Optional[bool]] = mapped_column(sa.Boolean, default=False)
    note: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    user: Mapped[User] = relationship("User", viewonly=True, back_populates="leaves")

    @classmethod
    def since(cls, timestamp):
        from app.controllers.user.util import get_user

        user = get_user()
        return db.session.scalars(sa.select(Leave).filter(Leave.start >= timestamp, Leave.user == user)).all()

    def logged(self) -> int:
        """
        Returns the duration in seconds of this leave entry
        """
        hours_per_day = self.user.settings.hours_per_day
        return int(self.duration * hours_per_day * 60 * 60)


class Settings(BaseModel):
    timezone: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    holiday_location: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)

    # 1 = Monday, 7 = Sunday
    week_start: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    hours_per_day: Mapped[float] = mapped_column(sa.Float, nullable=False)
    work_days: Mapped[str] = mapped_column(
        sa.String(7), nullable=False
    )  # This is stored as a 7 char string, the day char if the day is a work day and a hyphen if not, eg: MTWTF--
    auto_update_slack_status: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True, default=False)
    theme: Mapped[Literal["light", "dark"] | None] = mapped_column(sa.String(20), nullable=True, default=None)

    user_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("user.id"), nullable=False)

    user: Mapped[User] = relationship("User", viewonly=True, back_populates="settings")

    @classmethod
    def default(cls, user_id: int):
        return cls(
            timezone="Europe/London",
            week_start=1,
            hours_per_day=7.5,
            work_days="MTWTF--",
            user_id=user_id,
        )

    @property
    def week_start_0(self):
        return self.week_start - 1

    def work_days_list(self) -> list[str]:
        work_days = []
        for day, day_name in zip(self.work_days, DAYS_OF_WEEK):
            if day != "-":
                work_days.append(day_name)
        return work_days

    def total_work_days(self):
        return sum([1 if day != "-" else 0 for day in self.work_days])

    def is_work_day(self, day: DayOfWeek0Indexed) -> bool:
        """
        Check if the provided day name is a work day
        """
        return DAYS_OF_WEEK[day] in self.work_days_list()


class WhatsNew(BaseModel):
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[int] = mapped_column(sa.Integer, nullable=False)
