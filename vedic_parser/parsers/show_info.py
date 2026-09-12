"""Parser for the `show-info` fragment: the main planets table + Ashtakavarga.

The same markup appears inside a full analyse.php page (``#natal-info``), so
this parser accepts either the fragment or the whole page.

Everything language-independent is read from classes, hrefs and attributes
rather than from the visible text, so .com (English) and .ru (Russian)
responses parse identically. Label text is still returned as-is under
``name`` keys.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from ..chart import parse_degrees
from ._html import PLANET_CODES, code_from_class, href_group, nakshatra_label, selected_option
from ._html import text as _text
from ._html import value as _value

LORD_HREF_RE = re.compile(r"lord-in\?(\d+)-(\d+)")
IN_HOUSE_HREF_RE = re.compile(r"in-house\?\w+-(\d+)")
IN_SIGN_HREF_RE = re.compile(r"in-sign\?\w+-(\w+)")
NAKSHATRA_HREF_RE = re.compile(r"nakshatra\?(\w+)")

# Column order of the planets table, as documented in docs/recon.md §3.2. The
# Nakshatra column is only present for D1 — every other varga returns 14
# columns — so positions are resolved per table rather than hard-coded.
COLUMNS = (
    "planet",
    "karaka",
    "degrees",
    "rasi",
    "navamsa",
    "nakshatra",
    "relationship",
    "house",
    "lord",
    "fb",
    "nb",
    "shad_bala",
    "bindu",
    "position",
    "planet_war",
)


def parse_show_info(html: str) -> dict[str, Any]:
    """Parse a `show-info` response into plain data.

    Returns ``{"divisional": str|None, "planets": [...], "ashtakavarga": {...}}``.

    ``divisional`` is the varga marked selected in the markup, which is the
    session default and *not* necessarily the one that was requested — the
    site re-selects the option in JavaScript after loading the fragment.
    :func:`vedic_parser.api.show_info` overwrites it with the requested varga.
    The reliable in-band signal is the column count: only D1 carries the
    Nakshatra column.

    Careful with a varga other than D1: ``degrees``, ``house``, ``bindu`` and
    the balas follow the requested varga, but ``rasi`` stays the natal D1 sign
    and ``navamsa`` the D9 sign. So the sign a planet occupies *in that varga*
    is not in this response — take it from ``show-chart`` (for D9 the
    ``navamsa`` column happens to coincide).
    """
    soup = BeautifulSoup(html, "lxml")
    scope = soup.select_one("#natal-info") or soup
    table = scope.select_one("table.chart-info")
    if table is None:
        raise ValueError("no table.chart-info found; is this a show-info response?")

    rows = _data_rows(table)
    columns = _column_index(rows)
    return {
        "divisional": _selected_divisional(scope),
        "planets": [_parse_planet_row(row, columns) for row in rows],
        "ashtakavarga": _parse_ashtakavarga(scope),
    }


# -- planets ---------------------------------------------------------------


def _data_rows(table: Tag) -> list[Tag]:
    """Rows that describe a planet.

    The header row is the one carrying the varga <select>; it lives in a
    <thead> in the AJAX fragment but not in the full page, so it is skipped by
    content rather than by position.
    """
    return [row for row in table.find_all("tr") if not row.find("select")]


def _column_index(rows: list[Tag]) -> dict[str, int]:
    """Map column names to positions for this particular table.

    D1 returns all 15 columns; the other vargas leave the Nakshatra column
    out, shifting everything after it by one.
    """
    widths = {len(row.find_all("td", recursive=False)) for row in rows}
    if len(widths) != 1:
        raise ValueError(f"planet rows disagree on their width: {sorted(widths)}")
    width = widths.pop()
    if width == len(COLUMNS):
        names = COLUMNS
    elif width == len(COLUMNS) - 1:
        names = tuple(name for name in COLUMNS if name != "nakshatra")
    else:
        raise ValueError(f"expected {len(COLUMNS)} or {len(COLUMNS) - 1} columns, got {width}")
    return {name: index for index, name in enumerate(names)}


def _parse_planet_row(row: Tag, columns: dict[str, int]) -> dict[str, Any]:
    cells = row.find_all("td", recursive=False)

    def cell(name: str) -> Tag | None:
        index = columns.get(name)
        return cells[index] if index is not None else None

    label = cells[columns["planet"]]
    name = _text(label)
    degrees = cell("degrees")

    return {
        "code": code_from_class(label.find("a"), PLANET_CODES),
        "name": re.sub(r"\s*\(R\)$", "", name),
        "retrograde": name.endswith("(R)"),
        "karaka": _value(cell("karaka")),
        "degrees": _value(degrees),
        "degrees_decimal": parse_degrees(_text(degrees)),
        "rasi": _parse_rasi(cell("rasi")),
        "navamsa": _value(cell("navamsa")),
        "nakshatra": _parse_nakshatra(cell("nakshatra")),
        "relationship": _value(cell("relationship")),
        "house": _parse_house(cell("house")),
        "lords": _parse_lords(cell("lord")),
        "functional_beneficence": _parse_marker(cell("fb")),
        "natural_beneficence": _parse_marker(cell("nb")),
        "shad_bala": _parse_percent(cell("shad_bala")),
        "bindu": _parse_bindu(cell("bindu")),
        "position": _parse_markers(cell("position")),
        "planetary_war": _value(cell("planet_war")),
    }


def _parse_rasi(cell: Tag | None) -> dict[str, Any] | None:
    """Sign with its two-letter code; ``dignity`` is the cell's tooltip."""
    text = _value(cell)
    if text is None:
        return None
    link = cell.find("a")
    code = href_group(link, IN_SIGN_HREF_RE)
    dignity = (cell.get("title") or "").strip() or None
    return {"code": code, "name": text, "dignity": dignity}


def _parse_nakshatra(cell: Tag | None) -> dict[str, Any] | None:
    parsed = nakshatra_label(_value(cell))
    if parsed is None:
        return None
    return {"code": href_group(cell.find("a"), NAKSHATRA_HREF_RE), **parsed}


def _parse_house(cell: Tag | None) -> int | None:
    if cell is None:
        return None
    house = href_group(cell.find("a"), IN_HOUSE_HREF_RE)
    if house is not None:
        return int(house)
    text = _value(cell)
    return int(text) if text and text.isdigit() else None


def _parse_lords(cell: Tag | None) -> list[dict[str, Any]]:
    """Houses this planet rules, from ``lord-in?<ruled>-<placed>`` hrefs.

    Rahu and Ketu are shown as co-lords ("Co-lord 8th" / "Соупр. 8-го"); the
    distinction is taken from the link text starting with a digit or not,
    which holds in both languages.
    """
    lords = []
    for link in cell.find_all("a") if cell is not None else []:
        match = LORD_HREF_RE.search(link.get("href", ""))
        if not match:
            continue
        text = _text(link)
        lords.append(
            {
                "house": int(match.group(1)),
                "in_house": int(match.group(2)),
                "co_lord": not text[:1].isdigit(),
                "label": text,
            }
        )
    return lords


def _parse_marker(cell: Tag | None) -> dict[str, Any] | None:
    """A single coded marker with its tooltip, e.g. ``B`` / "Benefic. 100%…"."""
    markers = _parse_markers(cell)
    return markers[0] if markers else None


def _parse_markers(cell: Tag | None) -> list[dict[str, Any]]:
    markers = []
    for span in cell.find_all("span") if cell is not None else []:
        code = _text(span)
        if not code or code == "-":
            continue
        markers.append({"code": code, "description": (span.get("title") or "").strip() or None})
    if not markers:
        text = _value(cell)
        if text:
            markers.append({"code": text, "description": None})
    return markers


def _parse_percent(cell: Tag | None) -> int | None:
    text = _value(cell)
    if not text:
        return None
    match = re.search(r"(-?\d+)\s*%", text)
    return int(match.group(1)) if match else None


def _parse_bindu(cell: Tag | None) -> dict[str, int | None]:
    """``26 / 7`` -> Sarvashtakavarga and Bhinnashtakavarga bindus."""
    parts = [part.strip() for part in _text(cell).split("/")]
    values = [int(part) if part.isdigit() else None for part in parts]
    values += [None] * (2 - len(values))
    return {"sav": values[0], "bav": values[1]}


# -- ashtakavarga ----------------------------------------------------------


def _parse_ashtakavarga(scope: Tag) -> dict[str, Any]:
    """The SAV block plus one BAV block per planet.

    Each block is a chart drawing: ``.ashtaka-sign`` is the sign sitting in
    the first house and the non-empty ``.ashtaka-house`` divs hold the bindus
    of houses 1..12 in order.
    """
    result: dict[str, Any] = {"first_house_sign": None, "sav": [], "bav": {}}
    for block in scope.select("div.ashtaka-north, div.ashtaka-south"):
        label_div = block.select_one(".name")
        label = _text(label_div) if label_div else None
        values = [
            int(_text(house))
            for house in block.select(".ashtaka-house")
            if _text(house).isdigit()
        ]
        sign = block.select_one(".ashtaka-sign")
        if sign is not None and result["first_house_sign"] is None and _text(sign).isdigit():
            result["first_house_sign"] = int(_text(sign))
        if label == "SAV":
            result["sav"] = values
        elif label:
            result["bav"][label] = values
    return result


# -- helpers ---------------------------------------------------------------


def _selected_divisional(scope: Tag) -> str | None:
    return selected_option(scope.select_one("#divisional-natal"))
