"""Beräkning av tömningsdagar.

Ren Python utan beroenden till Home Assistant, så att logiken kan testas fristående.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import math
from typing import Any, Iterable, Optional

from .const import (
    CONF_EXCLUDE_DATES,
    CONF_EXTRA_DATES,
    CONF_INTERVAL_WEEKS,
    CONF_REFERENCE_DATE,
    CONF_SEASON_END,
    CONF_SEASON_START,
)

# Hur långt framåt vi letar efter nästa tömning. Räcker även för
# intervall på 52 veckor kombinerat med en kort säsong.
SEARCH_HORIZON = timedelta(days=800)


def parse_date_list(value: Optional[str]) -> frozenset[date]:
    """Tolka en kommaseparerad lista med datum (ÅÅÅÅ-MM-DD)."""
    if not value:
        return frozenset()
    result = set()
    for part in value.replace(";", ",").replace("\n", ",").split(","):
        part = part.strip()
        if part:
            result.add(date.fromisoformat(part))
    return frozenset(result)


def in_season(day: date, start_week: Optional[int], end_week: Optional[int]) -> bool:
    """Om dagen ligger inom säsongen (ISO-veckor, inklusive båda gränserna)."""
    if start_week is None or end_week is None:
        return True
    week = day.isocalendar()[1]
    if start_week <= end_week:
        return start_week <= week <= end_week
    # Säsong som går över årsskiftet, t.ex. v.45-10
    return week >= start_week or week <= end_week


@dataclass(frozen=True)
class BinSchedule:
    """Tömningsschema för ett kärl."""

    reference_date: date
    interval_weeks: int
    season_start: Optional[int] = None
    season_end: Optional[int] = None
    exclude_dates: frozenset[date] = field(default_factory=frozenset)
    extra_dates: frozenset[date] = field(default_factory=frozenset)

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> BinSchedule:
        """Skapa schema från sparad konfiguration."""
        season_start = cfg.get(CONF_SEASON_START)
        season_end = cfg.get(CONF_SEASON_END)
        return cls(
            reference_date=date.fromisoformat(cfg[CONF_REFERENCE_DATE]),
            interval_weeks=int(cfg[CONF_INTERVAL_WEEKS]),
            season_start=int(season_start) if season_start else None,
            season_end=int(season_end) if season_end else None,
            exclude_dates=parse_date_list(cfg.get(CONF_EXCLUDE_DATES)),
            extra_dates=parse_date_list(cfg.get(CONF_EXTRA_DATES)),
        )

    def _regular(self, start: date, end: date) -> Iterable[date]:
        step = self.interval_weeks * 7
        k = math.ceil((start - self.reference_date).days / step)
        day = self.reference_date + timedelta(days=k * step)
        while day <= end:
            if in_season(day, self.season_start, self.season_end):
                yield day
            day += timedelta(days=step)

    def occurrences(self, start: date, end: date) -> list[date]:
        """Alla tömningsdagar mellan start och end (inklusive)."""
        days = {d for d in self._regular(start, end) if d not in self.exclude_dates}
        days.update(d for d in self.extra_dates if start <= d <= end)
        return sorted(days)

    def next_collection(self, today: date) -> Optional[date]:
        """Nästa tömning från och med idag."""
        upcoming = self.upcoming(today, 1)
        return upcoming[0] if upcoming else None

    def upcoming(self, today: date, count: int) -> list[date]:
        """De kommande `count` tömningarna från och med idag."""
        return self.occurrences(today, today + SEARCH_HORIZON)[:count]
