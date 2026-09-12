"""Parser for the `show-dasha` fragment: one dasha table.

Each row is a period, and the useful part is in attributes rather than text::

    <tr start="23.11.1978 16:25" end="26.11.1981 11:56">
      <td><span class="Sa">Saturn</span>-<span class="Sa">Saturn</span></td>
      <td>23 Nov 1978</td><td class="hide">16:25</td><td>-</td><td class="hide"></td>
    </tr>

So the boundaries are exact and language-independent, while the visible date
("23 Nov 1978" / "23 ноя 1978") is only a label.

Two families of dasha exist. The planet ones (vimshottari, yogini, ashtottari,
navamsa) wrap each lord in a span whose class is the planet code. The sign ones
(chara_rao, narayana) print plain text — ``Aries-Taurus`` — so only the
localised names are available; use ``show-chart`` if you need to map those
names to sign codes in the current language.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup, Tag

from ._html import PLANET_CODES, code_from_class, int_or_none
from ._html import text as _text
from ._html import value as _value

# The format of the start/end attributes.
BOUNDARY_FORMAT = "%d.%m.%Y %H:%M"

PLANET_DASHAS = ("vimshottari", "yogini", "ashtottari", "navamsa")
SIGN_DASHAS = ("chara_rao", "narayana")


def parse_show_dasha(html: str) -> dict[str, Any]:
    """Parse a `show-dasha` response into plain data.

    Returns ``{"kind", "level", "periods"}``. ``kind`` is ``planet`` when the
    lords came back as codes and ``sign`` when the table only carries names;
    ``level`` is how deep the chain goes (1 maha, 2 antar, 3 pratyantar,
    4 sookshma), taken from the rows themselves.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table")
    if table is None:
        raise ValueError("no table found; is this a show-dasha response?")

    periods = [_parse_period(row) for row in table.find_all("tr")]
    periods = [period for period in periods if period is not None]
    level = max((len(period["labels"]) for period in periods), default=0)
    kind = "planet" if any(period["lords"] for period in periods) else "sign"
    return {"kind": kind, "level": level, "periods": periods}


def _parse_period(row: Tag) -> dict[str, Any] | None:
    cells = row.find_all("td")
    if not cells:
        return None

    lords = [code_from_class(span, PLANET_CODES) for span in cells[0].select("span")]
    labels = [_text(span) for span in cells[0].select("span")]
    if not labels:
        # A sign dasha: no spans, just "Aries-Taurus".
        labels = [part.strip() for part in _text(cells[0]).split("-") if part.strip()]
        lords = []

    return {
        "start": _boundary(row.get("start")),
        "end": _boundary(row.get("end")),
        "lords": [lord for lord in lords if lord],
        "labels": labels,
        # The visible date and time, as the site formatted them.
        "start_label": _value(cells[1]) if len(cells) > 1 else None,
        "start_time": _value(cells[2]) if len(cells) > 2 else None,
        # Age reached at the start of the period; "-" before the birth date.
        "age": int_or_none(_text(cells[3])) if len(cells) > 3 else None,
    }


def _boundary(raw: str | None) -> str | None:
    """``26.11.1981 11:56`` -> ``1981-11-26T11:56``."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), BOUNDARY_FORMAT).isoformat(timespec="minutes")
    except ValueError:
        return None
