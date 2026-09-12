"""Parser for the `show-other` fragment: the "Other" tab.

Five tables in one response, and unlike the rest of the site they carry no
classes, hrefs or tooltips — just text. So rows and columns are identified by
position, and the canonical key lists below are what make the result usable in
either language. The site's own labels are kept alongside as ``name``.

The same markup appears inside a full analyse.php page (``#other``).
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from ..chart import parse_degrees
from ._html import PLANET_CODES, int_or_none, nakshatra_label, selected_option
from ._html import text as _text
from ._html import value as _value

# Rows of the special lagnas / sphutas table, in the order the site prints them.
LAGNA_KEYS = (
    "bhava_lagna",
    "hora_lagna",
    "ghatika_lagna",
    "sri_lagna",
    "indu_lagna",
    "varnada_lagna",
    "paka_lagna",
    "karakamsa_lagna",
    "pranapada",
    "kunda",
    "bhrigu_bindu",
    "bija_sphuta",
    "kshetra_sphuta",
    "yogi_sphuta",
    "avayogi_sphuta",
)

UPAGRAHA_KEYS = (
    "dhuma",
    "vyatipata",
    "parivesha",
    "indrachapa",
    "upaketu",
    "gulika",
    "mandi",
    "kala",
    "mrityu",
    "ardhaprahara",
    "yamagantaka",
)

PANCHANGA_KEYS = ("sunrise", "sunset", "hora", "vara", "tithi", "karana", "yoga")

# The unnamed table of single values: Ayanamsa … Visha Navamsa.
POINT_KEYS = (
    "ayanamsa",
    "sahayogi",
    "badhaka",
    "dagdha_rasi",
    "drekkana_22",
    "navamsa_64",
    "sarpa_drekkana",
    "visha_navamsa",
)

# "29 K. Chaturdashi, Sa" — a value with the planet ruling it appended. The
# suffix only counts as a lord when it really is a planet code, so a name that
# happens to contain a comma stays intact.
WITH_LORD_RE = re.compile(
    r"^(?P<value>.*?)(?:,\s*(?P<lord>" + "|".join(PLANET_CODES) + r")\s*)?$"
)


def parse_show_other(html: str) -> dict[str, Any]:
    """Parse a `show-other` response into plain data.

    Returns ``{"divisional", "lagnas", "panchanga", "upagrahas", "points",
    "chakras"}``.

    Positions are trusted, so a table whose row or column count does not match
    the canonical list keeps its rows but leaves their ``key`` as None rather
    than mislabelling them.
    """
    soup = BeautifulSoup(html, "lxml")
    scope = soup.select_one("#other") or soup
    tables = scope.select("table.chart-info")
    if not tables:
        raise ValueError("no table.chart-info found; is this a show-other response?")

    upagraha_table = scope.select_one("#upagrahas")
    rest = [table for table in tables if table is not upagraha_table]
    # What is left comes in a fixed order: lagnas, panchanga, points, chakras.
    lagnas, panchanga, points, chakras = (rest + [None] * 4)[:4]

    return {
        "divisional": selected_option(scope.select_one("#other-divisional")),
        "lagnas": _parse_points_table(lagnas, LAGNA_KEYS, house=False),
        "panchanga": _parse_row_table(panchanga, PANCHANGA_KEYS, with_lord=True),
        "upagrahas": _parse_points_table(upagraha_table, UPAGRAHA_KEYS, house=True),
        "points": _parse_row_table(points, POINT_KEYS, with_lord=False),
        "chakras": _parse_chakras(chakras),
    }


def _data_rows(table: Tag | None) -> list[Tag]:
    """Rows after the header one."""
    if table is None:
        return []
    return table.find_all("tr")[1:]


def _keys_for(rows: list[Tag], keys: tuple[str, ...]) -> list[str | None]:
    """Canonical keys, or None for every row when the shape is unexpected."""
    if len(rows) == len(keys):
        return list(keys)
    return [None] * len(rows)


def _parse_points_table(
    table: Tag | None, keys: tuple[str, ...], *, house: bool
) -> list[dict[str, Any]]:
    """The lagnas and the upagrahas tables: name, degrees, sign, nakshatra[, house]."""
    rows = _data_rows(table)
    parsed = []
    for key, row in zip(_keys_for(rows, keys), rows):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        degrees = _value(cells[1])
        parsed.append(
            {
                "key": key,
                "name": _value(cells[0]),
                "degrees": degrees,
                "degrees_decimal": parse_degrees(degrees or ""),
                "sign": _value(cells[2]),
                "nakshatra": nakshatra_label(_value(cells[3])),
                **({"house": int_or_none(_text(cells[4])) if len(cells) > 4 else None}
                   if house else {}),
            }
        )
    return parsed


def _parse_row_table(
    table: Tag | None, keys: tuple[str, ...], *, with_lord: bool
) -> dict[str, Any]:
    """A two-row table: labels on top, one value each below.

    Multi-line cells (``<br>``) become lists; a value with a planet appended
    ("Siddhi, Ma") is split into value and lord when ``with_lord`` is set.
    """
    rows = table.find_all("tr") if table is not None else []
    if len(rows) < 2:
        return {}
    labels = [_text(cell) for cell in rows[0].find_all("td")]
    cells = rows[1].find_all("td")
    if len(cells) != len(keys):
        # Unexpected width: fall back to the site's own labels as keys.
        return {label: _cell_values(cell) for label, cell in zip(labels, cells)}

    parsed: dict[str, Any] = {}
    for key, label, cell in zip(keys, labels, cells):
        values = _cell_values(cell)
        if with_lord and isinstance(values, str):
            match = WITH_LORD_RE.match(values)
            value, lord = match.group("value"), match.group("lord")
            parsed[key] = {"value": value.strip(" ,") or None, "lord": lord, "label": label}
        else:
            parsed[key] = {"value": values, "label": label}
    return parsed


def _cell_values(cell: Tag) -> Any:
    """Cell text, as a list when the cell holds several values.

    Two shapes occur: lines separated by ``<br>`` (the same point reckoned from
    the Ascendant and from the Moon), and a comma-separated run of planet
    codes. Anything else stays a plain string.
    """
    lines = [part.strip() for part in cell.decode_contents().split("<br/>")]
    if len(lines) > 1:
        soup = BeautifulSoup("<div>" + "</div><div>".join(lines) + "</div>", "lxml")
        return [_value(div) for div in soup.select("div")]
    raw = _value(cell)
    if raw and "," in raw:
        parts = [part.strip() for part in raw.split(",")]
        if all(part in PLANET_CODES for part in parts):
            return parts
    return raw


def _parse_chakras(table: Tag | None) -> list[dict[str, Any]]:
    """The chakra table. Its first cell packs "number | name" together."""
    chakras = []
    for row in _data_rows(table):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        number, _, name = _text(cells[0]).partition("|")
        chakras.append(
            {
                "number": int_or_none(number),
                "name": name.strip() or None,
                "meaning": _value(cells[1]),
                "element": _value(cells[2]),
                "signs": _split_list(cells[3]),
                "planets": _split_list(cells[4]),
                "in_sign": _split_list(cells[5]),
            }
        )
    return chakras


def _split_list(cell: Tag | None) -> list[str]:
    raw = _value(cell)
    return [part.strip() for part in raw.split(",")] if raw else []
