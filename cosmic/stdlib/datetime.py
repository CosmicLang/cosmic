"""Date and time manipulation, formatting, and timer utilities for the Cosmic Standard Library."""
from __future__ import annotations
import time
import datetime as _dt
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class DateTime:
    _dt_obj: _dt.datetime

    @staticmethod
    def now() -> DateTime:
        """Return a DateTime for the current moment."""
        return DateTime(_dt.datetime.now())

    @staticmethod
    def today() -> DateTime:
        """Return a DateTime for today with zeroed time."""
        now = _dt.datetime.now()
        return DateTime(_dt.datetime(now.year, now.month, now.day))

    @staticmethod
    def from_timestamp(ts: float) -> DateTime:
        """Create a DateTime from a Unix timestamp."""
        return DateTime(_dt.datetime.fromtimestamp(ts))

    @staticmethod
    def parse(s: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> DateTime:
        """Parse a datetime string using the given format."""
        return DateTime(_dt.datetime.strptime(s, fmt))

    def format(self, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format the datetime using the given strftime format."""
        return self._dt_obj.strftime(fmt)

    @property
    def year(self) -> int:
        return self._dt_obj.year

    @property
    def month(self) -> int:
        return self._dt_obj.month

    @property
    def day(self) -> int:
        return self._dt_obj.day

    @property
    def hour(self) -> int:
        return self._dt_obj.hour

    @property
    def minute(self) -> int:
        return self._dt_obj.minute

    @property
    def second(self) -> int:
        return self._dt_obj.second

    @property
    def microsecond(self) -> int:
        return self._dt_obj.microsecond

    def weekday(self) -> int:
        """Return the day of the week (0=Monday, 6=Sunday)."""
        return self._dt_obj.weekday()

    def weekday_name(self) -> str:
        """Return the full name of the day of the week."""
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][self.weekday()]

    def is_weekend(self) -> bool:
        """Check if the date falls on a weekend."""
        return self.weekday() >= 5

    def is_leap_year(self) -> bool:
        """Check if the year is a leap year."""
        return _dt.datetime(self.year, 1, 1).year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0)

    def days_in_month(self) -> int:
        """Return the number of days in the current month."""
        if self.month == 12:
            next_month = _dt.datetime(self.year + 1, 1, 1)
        else:
            next_month = _dt.datetime(self.year, self.month + 1, 1)
        return (next_month - _dt.datetime(self.year, self.month, 1)).days

    def add_days(self, days: int) -> DateTime:
        """Return a new DateTime with days added."""
        return DateTime(self._dt_obj + _dt.timedelta(days=days))

    def add_hours(self, hours: int) -> DateTime:
        """Return a new DateTime with hours added."""
        return DateTime(self._dt_obj + _dt.timedelta(hours=hours))

    def add_minutes(self, minutes: int) -> DateTime:
        """Return a new DateTime with minutes added."""
        return DateTime(self._dt_obj + _dt.timedelta(minutes=minutes))

    def add_seconds(self, seconds: int) -> DateTime:
        """Return a new DateTime with seconds added."""
        return DateTime(self._dt_obj + _dt.timedelta(seconds=seconds))

    def diff(self, other: DateTime) -> _dt.timedelta:
        """Return the timedelta between this and another DateTime."""
        return self._dt_obj - other._dt_obj

    def to_iso(self) -> str:
        """Return the ISO 8601 format string."""
        return self._dt_obj.isoformat()

    def to_timestamp(self) -> float:
        """Return the Unix timestamp."""
        return self._dt_obj.timestamp()

    def to_string(self) -> str:
        """Return the datetime as 'YYYY-MM-DD HH:MM:SS' string."""
        return self._dt_obj.strftime('%Y-%m-%d %H:%M:%S')

    def start_of_day(self) -> DateTime:
        """Return a DateTime at the start of the day (midnight)."""
        return DateTime(_dt.datetime(self.year, self.month, self.day))

    def end_of_day(self) -> DateTime:
        """Return a DateTime at the end of the day (23:59:59.999999)."""
        return DateTime(_dt.datetime(self.year, self.month, self.day, 23, 59, 59, 999999))

    def replace(self, year: int | None = None, month: int | None = None,
                day: int | None = None, hour: int | None = None,
                minute: int | None = None, second: int | None = None) -> DateTime:
        """Return a new DateTime with specified fields replaced."""
        return DateTime(self._dt_obj.replace(
            year=year if year is not None else self.year,
            month=month if month is not None else self.month,
            day=day if day is not None else self.day,
            hour=hour if hour is not None else self.hour,
            minute=minute if minute is not None else self.minute,
            second=second if second is not None else self.second,
        ))

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"DateTime({self.to_string()})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DateTime):
            return self._dt_obj == other._dt_obj
        return NotImplemented

    def __lt__(self, other: DateTime) -> bool:
        return self._dt_obj < other._dt_obj

    def __le__(self, other: DateTime) -> bool:
        return self._dt_obj <= other._dt_obj

    def __gt__(self, other: DateTime) -> bool:
        return self._dt_obj > other._dt_obj

    def __ge__(self, other: DateTime) -> bool:
        return self._dt_obj >= other._dt_obj

    def __hash__(self) -> int:
        return hash(self._dt_obj)


@dataclass
class Timer:
    start_time: float = field(default_factory=time.perf_counter)
    _end_time: float | None = None

    def stop(self) -> float:
        """Stop the timer and return elapsed seconds."""
        self._end_time = time.perf_counter()
        return self._end_time - self.start_time

    def elapsed(self) -> float:
        """Return the elapsed time in seconds since the timer started."""
        if self._end_time is not None:
            return self._end_time - self.start_time
        return time.perf_counter() - self.start_time


def sleep(seconds: float) -> None:
    """Sleep for the given number of seconds."""
    time.sleep(seconds)


def timestamp() -> float:
    """Return the current Unix timestamp as a float."""
    return time.time()


def unix_now() -> int:
    """Return the current Unix timestamp as an integer."""
    return int(time.time())
