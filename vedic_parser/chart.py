"""Birth data and the degree format the site uses."""

from __future__ import annotations

import re
from dataclasses import dataclass

# 21°05'41''
DEGREES_RE = re.compile(r"(\d+)°(?:(\d+)')?(?:(\d+)'')?")


@dataclass(frozen=True)
class Chart:
    """Birth data for one chart.

    The site takes it as a pipe-separated string in the `data` parameter of
    every actions.php call, e.g.

        name=Ss|date=07.08.1983|time=23:00:00|timezone=+4|latitude=55.45|longitude=37.37

    Note that coordinates are *not* decimal degrees: 55.45 means 55°45',
    exactly as the site's own form submits them.
    """

    name: str
    date: str  # dd.mm.yyyy
    time: str  # hh:mm:ss
    timezone: str  # hours offset, e.g. "+4", "-5.30"
    latitude: str  # deg.min, negative for South
    longitude: str  # deg.min, negative for West

    def to_data(self) -> str:
        return (
            f"name={self.name}|date={self.date}|time={self.time}"
            f"|timezone={self.timezone}|latitude={self.latitude}|longitude={self.longitude}"
        )

    def to_query(self) -> dict[str, str]:
        """Parameters for the analyse.php / horoscope.php page URLs."""
        return {
            "name": self.name,
            "date": self.date,
            "time": self.time,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
        }


def parse_degrees(text: str) -> float | None:
    """``21°05'41''`` -> ``21.09472``. Returns None for placeholders like ``-``."""
    match = DEGREES_RE.search(text or "")
    if not match:
        return None
    deg, minutes, seconds = (int(g) if g else 0 for g in match.groups())
    return round(deg + minutes / 60 + seconds / 3600, 6)
