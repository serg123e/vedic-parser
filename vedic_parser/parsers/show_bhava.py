"""Parser for the `show-bhava` fragment: the Bhava Chalita houses.

Two parts: a chart drawing in ``#chart-bhava`` — the same markup ``show-chart``
returns, so it is parsed by the same code — and a table of the twelve houses:

    House | Cusp (sign, degrees) | Start (…) | End (…) | Size | Planets

The header groups the sign and the degrees of each boundary under one label
with ``colspan``, so columns are expanded before being read.

Note what is *not* here: the site reports no Bhava Bala anywhere in this
response, only the geometry of the houses and what falls in them.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from ..chart import parse_degrees
from ._html import PLANET_CODES, int_or_none
from ._html import text as _text
from ._html import value as _value
from .show_chart import parse_show_chart

#: Column groups of the house table, in order, after the house number.
BOUNDARY_KEYS = ("cusp", "start", "end")


def parse_show_bhava(html: str) -> dict[str, Any]:
    """Parse a `show-bhava` response into plain data.

    Returns ``{"houses": [...], "chart": {...}}``; ``chart`` is the Bhava
    Chalita drawing in the same shape :func:`parse_show_chart` produces, or
    None when the response carries only the table.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.select_one("table.chart-info")
    if table is None:
        raise ValueError("no table.chart-info found; is this a show-bhava response?")

    drawing = soup.select_one("#chart-bhava")
    return {
        "houses": _parse_houses(table),
        "chart": parse_show_chart(str(drawing)) if drawing is not None else None,
    }


def _parse_houses(table: Tag) -> list[dict[str, Any]]:
    rows = table.find_all("tr")
    houses = []
    for row in rows:
        cells = row.find_all("td")
        number = int_or_none(_text(cells[0])) if cells else None
        if number is None or len(cells) < 9:
            continue  # the header row
        house: dict[str, Any] = {"house": number}
        for index, key in enumerate(BOUNDARY_KEYS):
            house[key] = _boundary(cells[1 + index * 2], cells[2 + index * 2])
        size = _value(cells[7])
        house["size"] = size
        house["size_decimal"] = parse_degrees(size or "")
        # The cell separates several bodies with commas: "Su, Mo, Ma".
        codes = re.split(r"[,\s]+", _text(cells[8]))
        house["planets"] = [code for code in codes if code in PLANET_CODES]
        houses.append(house)
    return houses


def _boundary(sign: Tag, degrees: Tag) -> dict[str, Any]:
    """One boundary of a house: the sign it falls in and how far into it."""
    raw = _value(degrees)
    return {
        "sign": _value(sign),
        "degrees": raw,
        "degrees_decimal": parse_degrees(raw or ""),
    }
