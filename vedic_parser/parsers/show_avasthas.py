"""Parser for the `show-avasthas` fragment: the states of the planets.

Three parts in one response:

1. A table of Baladi (by age), Jagradadi (by awakening) and Deeptadi +
   Lajjitadi (by mood) avasthas, one row per planet.
2. A table of Shayanadi (by activity) avasthas, whose strength depends on the
   first syllable of the person's name — so the site prints all five syllable
   groups with the strength each would give.
3. A legend of the Shayanadi states occurring in this chart, with how many
   planets are in each.

Colour classes carry the verdict and line up with the strengths the site
prints: 100% is green, 50% orange, and 25%, 15% or 0% red. They are exposed as
``tone`` without reinterpretation.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from ._html import PLANET_CODES, SIGN_CODES, code_from_class
from ._html import text as _text
from ._html import value as _value

TONES = ("green", "orange", "red")

# "[50% strength]" / "[50% силы]" / "50% strength"
PERCENT_RE = re.compile(r"(\d+)\s*%")
# "Resting [1]" — the state and how many planets are in it.
COUNT_RE = re.compile(r"\[(\d+)\]\s*$")


def parse_show_avasthas(html: str) -> dict[str, Any]:
    """Parse a `show-avasthas` response into plain data.

    Returns ``{"planets", "shayanadi_legend", "shayanadi_note"}``.
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.select("table.chart-info")
    if not tables:
        raise ValueError("no table.chart-info found; is this a show-avasthas response?")

    legend_table = soup.select_one("#shayanadi-info")
    grids = [table for table in tables if table is not legend_table]
    states, shayanadi = (grids + [None, None])[:2]

    planets: dict[str, dict[str, Any]] = {}
    for row in _planet_rows(states):
        planets[row["code"]] = row
    for row in _planet_rows(shayanadi, shayanadi_table=True):
        planets.setdefault(row["code"], {"code": row["code"], "name": row["name"]})
        planets[row["code"]]["shayanadi"] = row["shayanadi"]

    note = soup.select_one("#shayanadi-note")
    return {
        "planets": list(planets.values()),
        "shayanadi_legend": _parse_legend(legend_table),
        "shayanadi_note": _value(note),
    }


def _planet_rows(table: Tag | None, shayanadi_table: bool = False) -> list[dict[str, Any]]:
    if table is None:
        return []
    rows = []
    for row in table.find_all("tr"):
        label = row.find("td")
        code = code_from_class(label, PLANET_CODES)
        if not code:
            continue  # the header row
        cells = row.find_all("td")
        parsed: dict[str, Any] = {"code": code, "name": _value(label)}
        if shayanadi_table:
            parsed["shayanadi"] = _parse_shayanadi(cells, table)
        else:
            parsed["baladi"] = _parse_state(cells[1] if len(cells) > 1 else None)
            parsed["jagradadi"] = _parse_state(cells[2] if len(cells) > 2 else None)
            parsed["deeptadi"] = _parse_moods(
                cells[3] if len(cells) > 3 else None,
                cells[4] if len(cells) > 4 else None,
            )
        rows.append(parsed)
    return rows


def _parse_state(cell: Tag | None) -> dict[str, Any] | None:
    """A state with its strength, e.g. "Young [50% strength]"."""
    if cell is None:
        return None
    span = cell.find("span")
    raw = _text(span if span is not None else cell)
    if not raw:
        return None
    percent = PERCENT_RE.search(raw)
    # The strength sits in a nested <u>; strip it from the state name.
    marker = span.find("u") if span is not None else None
    name = raw.replace(_text(marker), "").strip() if marker is not None else raw
    return {
        "state": name or None,
        "strength_percent": int(percent.group(1)) if percent else None,
        "tone": _tone(span),
    }


def _parse_moods(states: Tag | None, reasons: Tag | None) -> list[dict[str, Any]]:
    """Deeptadi and Lajjitadi avasthas: parallel lists of states and reasons.

    The reason names the planets and signs responsible; those codes stay latin
    in both languages, so they are pulled out of the text by exact match.
    """
    state_spans = states.find_all("span") if states is not None else []
    reason_spans = reasons.find_all("span") if reasons is not None else []

    moods = []
    for index, span in enumerate(state_spans):
        reason = reason_spans[index] if index < len(reason_spans) else None
        tokens = _text(reason).split()
        moods.append(
            {
                "state": _value(span),
                "tone": _tone(span),
                "reason": _value(reason),
                "planets": [token for token in tokens if token in PLANET_CODES],
                "signs": [token for token in tokens if token in SIGN_CODES],
            }
        )
    return moods


def _parse_shayanadi(cells: list[Tag], table: Tag) -> dict[str, Any]:
    """The activity state plus the strength for each syllable group.

    Which group applies depends on the first syllable of the name, so the site
    shows them all; the groups are latin transliteration in both languages.

    The header spans its title across two columns, so it has to be expanded by
    colspan before its labels line up with the data cells.
    """
    labels = _header_columns(table)

    groups = []
    for index in range(3, len(cells)):
        label = labels.get(index, "")
        percent = PERCENT_RE.search(_text(cells[index]))
        groups.append(
            {
                "letters": label.split(),
                "strength_percent": int(percent.group(1)) if percent else None,
                "tone": _tone(cells[index].find("span")),
            }
        )

    state = cells[1] if len(cells) > 1 else None
    effect = cells[2] if len(cells) > 2 else None
    return {
        "state": _value(state),
        "tone": _tone(state.find("span") if state is not None else None),
        "effect": _value(effect),
        "by_letter_group": groups,
    }


def _header_columns(table: Tag) -> dict[int, str]:
    """Header labels by column index, honouring colspan."""
    header = table.find("tr")
    labels: dict[int, str] = {}
    column = 0
    for cell in header.find_all("td") if header else []:
        span = int(cell.get("colspan") or 1)
        labels[column] = _text(cell)
        column += span
    return labels


def _parse_legend(table: Tag | None) -> list[dict[str, Any]]:
    """The Shayanadi states present in this chart, with their planet count."""
    if table is None:
        return []
    legend = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        label = _text(cells[0])
        count = COUNT_RE.search(label)
        legend.append(
            {
                "state": COUNT_RE.sub("", label).strip() or None,
                "count": int(count.group(1)) if count else None,
                "tone": _tone(cells[0].find("span")),
                "description": _value(cells[1]),
            }
        )
    return legend


def _tone(node: Tag | None) -> str | None:
    """The colour class the site put on a verdict: green, orange or red."""
    if node is None:
        return None
    for name in node.get("class", []):
        if name in TONES:
            return name
    return None
