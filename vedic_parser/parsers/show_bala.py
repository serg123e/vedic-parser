"""Parser for the `show-bala` fragment: planetary strengths.

Four tables, all of them grids with grouped headers:

1. Shad Bala — the six strengths per planet, each as a percentage of the
   required minimum plus its value in virupas (and rupas for the total).
2. Vimsopaka / Vaiseshikamsa / Vargottama Bala — strength across varga sets.
3. Aspects on planets — a 7×9 matrix of drik bala contributions.
4. Aspects on houses — the same for the twelve houses.

Column groups are declared with ``colspan`` and the data cells span them
unevenly (some strengths come as a pair of numbers, some as one), so the parser
expands both header and row into columns and then aligns them. Tables are
recognised by their shape — how many header rows they have, whether their
column labels are planet codes or house numbers — never by their labels, which
are localised.

``show-shad-bala`` returns only the first table; this parser accepts that too.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from ._html import PLANET_CODES, code_from_class
from ._html import text as _text
from ._html import value as _value

# Column groups of the Shad Bala table, in order. The blank group the site puts
# before Ishta Bala is skipped.
SHAD_BALA_KEYS = (
    "shad_bala",
    "sthana_bala",
    "dig_bala",
    "kala_bala",
    "cheshta_bala",
    "drik_bala",
    "naisargika_bala",
    "yuddha_bala",
    "ishta_bala",
    "kashta_bala",
)

# Column groups of the second table.
VARGA_BALA_KEYS = ("vimsopaka", "vaiseshikamsa", "vargottama")

# Sub-columns are keyed by the varga count the site prints in the label —
# "Shodasha Varga (16)" / "Шодаша Варга (16)" — which does not change with the
# language.
VARGA_SET_KEYS = {16: "shodasha", 10: "dasha", 7: "sapta", 6: "shad"}

PERCENT_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")
NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")


def parse_show_bala(html: str) -> dict[str, Any]:
    """Parse a `show-bala` response into plain data.

    Returns ``{"shad_bala", "varga_bala", "aspects"}``. Parts the response does
    not carry come back empty.
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.select("table.chart-info")
    if not tables:
        raise ValueError("no table.chart-info found; is this a show-bala response?")

    shad_bala: list[dict[str, Any]] = []
    varga_bala: list[dict[str, Any]] = []
    aspects: dict[str, Any] = {}

    for table in tables:
        header, body = _split(table)
        if "aspects-info" in (table.get("class") or []):
            matrix = _parse_matrix(table)
            aspects[matrix.pop("target")] = matrix
        elif len(header) == 1:
            shad_bala = [_parse_shad_bala_row(header[0], row) for row in body]
        elif len(header) >= 2:
            varga_bala = [_parse_varga_bala_row(header[-2], header[-1], row) for row in body]

    return {"shad_bala": shad_bala, "varga_bala": varga_bala, "aspects": aspects}


def _split(table: Tag) -> tuple[list[Tag], list[Tag]]:
    """Split rows into header rows and body rows.

    A body row is one whose first cell is tagged with a planet code; that is
    also what tells a one-header table from a two-header one.
    """
    header, body = [], []
    for row in table.find_all("tr"):
        first = row.find("td")
        if first is not None and code_from_class(first, PLANET_CODES):
            body.append(row)
        elif body:
            body.append(row)  # the "+"/"-" summary rows of a matrix
        else:
            header.append(row)
    return header, body


def _columns(row: Tag, skip_first: bool = True) -> list[tuple[str, int, int]]:
    """Cells of a row as ``(text, start column, span)``, honouring colspan."""
    cells = row.find_all("td")
    if skip_first:
        cells = cells[1:]
    spans, column = [], 0
    for cell in cells:
        span = int(cell.get("colspan") or 1)
        spans.append((_text(cell), column, span))
        column += span
    return spans


def _number(raw: str | None) -> float | int | None:
    """A numeric cell as a number, keeping ints int; anything else is None."""
    if not raw or not NUMBER_RE.match(raw.strip()):
        return None
    value = float(raw)
    return int(value) if value.is_integer() and "." not in raw else value


def _percent(raw: str) -> int | float | None:
    match = PERCENT_RE.search(raw or "")
    if not match:
        return None
    return _number(match.group(1))


def _parse_shad_bala_row(header: Tag, row: Tag) -> dict[str, Any]:
    """One planet's row, aligned to the header's column groups."""
    groups = [group for group in _columns(header) if group[0]]
    cells = _columns(row)

    components: dict[str, Any] = {}
    for key, (_, start, span) in zip(SHAD_BALA_KEYS, groups):
        values = [text for text, column, _ in cells if start <= column < start + span]
        components[key] = _component(values)

    label = row.find("td")
    return {
        "code": code_from_class(label, PLANET_CODES),
        "name": _value(label),
        "components": components,
    }


def _component(values: list[str]) -> dict[str, Any]:
    """A strength as the site reports it.

    The six balas come as a percentage of the required minimum plus the value
    in virupas; the total adds rupas; Naisargika, Yuddha, Ishta and Kashta come
    as a bare number.
    """
    numbers = [value for value in values if value not in ("", "-")]
    percent = next((_percent(value) for value in numbers if "%" in value), None)
    plain = [_number(value) for value in numbers if "%" not in value]
    return {
        "percent": percent,
        "virupas": plain[0] if plain else None,
        "rupas": plain[1] if len(plain) > 1 else None,
    }


def _parse_varga_bala_row(groups_row: Tag, labels_row: Tag, row: Tag) -> dict[str, Any]:
    """One planet's row of the Vimsopaka / Vaiseshikamsa / Vargottama table."""
    groups = [group for group in _columns(groups_row) if group[0]]
    labels = _columns(labels_row)
    cells = {column: text for text, column, _ in _columns(row)}

    parsed: dict[str, Any] = {}
    for key, (_, start, span) in zip(VARGA_BALA_KEYS, groups):
        columns = [
            (label, column) for label, column, _ in labels if start <= column < start + span
        ]
        if len(columns) == 1:
            # Vargottama Bala is a single count, not a percentage pair.
            parsed[key] = _number(cells.get(columns[0][1]))
            continue
        sets: dict[str, Any] = {}
        for label, column in columns:
            raw = cells.get(column, "")
            count = _number((re.search(r"\((\d+)\)", label) or [None, None])[1])
            set_key = VARGA_SET_KEYS.get(count, label)
            sets[set_key] = {
                "percent": _percent(raw),
                "value": _number(raw.split("|")[-1].strip()) if "|" in raw else None,
            }
        parsed[key] = sets

    label = row.find("td")
    return {
        "code": code_from_class(label, PLANET_CODES),
        "name": _value(label),
        **parsed,
    }


def _parse_matrix(table: Tag) -> dict[str, Any]:
    """An aspect matrix: rows are aspecting planets, columns their targets.

    Cells hold drik bala virupas. Where the site prints ``+`` or ``-`` instead
    of a number the cell carries no magnitude — those contribute nothing to the
    two summary rows, which add up the aspects cast by the chart's natural
    benefics and malefics respectively.

    Row labels here are the planet codes themselves, and their class is the
    planet's nature in this chart (green benefic, red malefic) — the same
    verdict as the natural beneficence column of ``show-info``.
    """
    rows = table.find_all("tr")
    columns_row = next(
        (row for row in rows if len(row.find_all("td")) > 3 and not row.find("img")), rows[0]
    )
    columns = [_text(cell) for cell in columns_row.find_all("td")[1:]]
    houses = all(column.isdigit() for column in columns)

    grid: dict[str, list[Any]] = {}
    totals: dict[str, list[Any]] = {}
    nature: dict[str, str] = {}
    for row in rows:
        if row is columns_row:
            continue
        cells = row.find_all("td")
        if len(cells) != len(columns) + 1:
            continue
        label = _text(cells[0])
        values = [_cell_value(cell) for cell in cells[1:]]
        if label in PLANET_CODES:
            grid[label] = values
            classes = cells[0].get("class") or []
            if "green" in classes:
                nature[label] = "benefic"
            elif "red" in classes:
                nature[label] = "malefic"
        elif label == "+":
            totals["benefic"] = values
        elif label == "-":
            totals["malefic"] = values

    return {
        "target": "on_houses" if houses else "on_planets",
        "columns": [int(column) for column in columns] if houses else columns,
        "rows": grid,
        "nature": nature,
        "totals": totals,
    }


def _cell_value(cell: Tag) -> Any:
    """A matrix cell: a number where there is one, otherwise the raw symbol."""
    raw = _text(cell)
    number = _number(raw)
    return number if number is not None else (raw or None)
