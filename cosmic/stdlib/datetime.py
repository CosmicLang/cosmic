"""Cosmic Standard Library — datetime module."""
from __future__ import annotations
import time
import datetime as _dt
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DateTime:
    _dt_obj: _dt.datetime

    @staticmethod
    def now() -> DateTime:
        return DateTime(_dt.datetime.now())

    @staticmethod
    def today() -> DateTime:
        now = _dt.datetime.now()
        return DateTime(_dt.datetime(now.year, now.month, now.day))

    @staticmethod
    def from_timestamp(ts: float) -> DateTime:
        return DateTime(_dt.datetime.fromtimestamp(ts))

    @staticmethod
    def parse(s: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> DateTime:
        return DateTime(_dt.datetime.strptime(s, fmt))

    def format(self, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
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
        return self._dt_obj.weekday()

    def weekday_name(self) -> str:
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][self.weekday()]

    def is_weekend(self) -> bool:
        return self.weekday() >= 5

    def is_leap_year(self) -> bool:
        return _dt.datetime(self.year, 1, 1).year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0)

    def days_in_month(self) -> int:
        if self.month == 12:
            next_month = _dt.datetime(self.year + 1, 1, 1)
        else:
            next_month = _dt.datetime(self.year, self.month + 1, 1)
        return (next_month - _dt.datetime(self.year, self.month, 1)).days

    def add_days(self, days: int) -> DateTime:
        return DateTime(self._dt_obj + _dt.timedelta(days=days))

    def add_hours(self, hours: int) -> DateTime:
        return DateTime(self._dt_obj + _dt.timedelta(hours=hours))

    def add_minutes(self, minutes: int) -> DateTime:
        return DateTime(self._dt_obj + _dt.timedelta(minutes=minutes))

    def add_seconds(self, seconds: int) -> DateTime:
        return DateTime(self._dt_obj + _dt.timedelta(seconds=seconds))

    def diff(self, other: DateTime) -> _dt.timedelta:
        return self._dt_obj - other._dt_obj

    def to_iso(self) -> str:
        return self._dt_obj.isoformat()

    def to_timestamp(self) -> float:
        return self._dt_obj.timestamp()

    def to_string(self) -> str:
        return self._dt_obj.strftime('%Y-%m-%d %H:%M:%S')

    def start_of_day(self) -> DateTime:
        return DateTime(_dt.datetime(self.year, self.month, self.day))

    def end_of_day(self) -> DateTime:
        return DateTime(_dt.datetime(self.year, self.month, self.day, 23, 59, 59, 999999))

    def replace(self, year: int | None = None, month: int | None = None,
                day: int | None = None, hour: int | None = None,
                minute: int | None = None, second: int | None = None) -> DateTime:
        return DateTime(self._dt_obj.replace(
            year=year or self.year, month=month or self.month,
            day=day or self.day, hour=hour or self.hour,
            minute=minute or self.minute, second=second or self.second,
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


@dataclass(frozen=True)
class Timer:
    start_time: float = 0.0
    end_time: float = 0.0

    def start(self) -> Timer:
        return Timer(start_time=time.perf_counter())

    def stop(self) -> float:
        return time.perf_counter() - self.start_time

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def timestamp() -> float:
    return time.time()


def unix_now() -> int:
    return int(time.time())
