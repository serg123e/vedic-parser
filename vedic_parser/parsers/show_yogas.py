"""Parser for the `show-yogas` fragment: the yogas a chart forms.

The response is a bare run of ``<tr>`` rows with no table around them::

    <tr><td class="nowrap" type="Mahapurusha">Sasa</td>
        <td class="nowrap">Sa</td>
        <td>Wandering leader of free spirit</td>
        <td>Saturn in a kendra in own or exaltation sign</td></tr>

Only the yogas actually present are listed. The category sits in the row's
``type`` attribute but is localised ("Махапуруша"), so it is mapped to a stable
key through :data:`CATEGORY_KEYS`; a category not in that table keeps its label
and gets ``category: None`` rather than a wrong key.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from ._html import PLANET_CODES, attr
from ._html import text as _text
from ._html import value as _value

#: Localised category labels to stable keys. Six categories were seen across
#: four different charts on both domains; anything else maps to None.
CATEGORY_KEYS = {
    "Mahapurusha": "mahapurusha",
    "Махапуруша": "mahapurusha",
    "Solar": "solar",
    "Солнечные": "solar",
    "Lunar": "lunar",
    "Лунные": "lunar",
    "Nabhasa": "nabhasa",
    "Набхаса": "nabhasa",
    "Raja + Dhana": "raja_dhana",
    "Раджа + Дхана": "raja_dhana",
    "Other": "other",
    "Другие": "other",
}

#: The site prints this instead of a planet list when a yoga involves them all.
#: It stays English in the Russian response too.
ALL_PLANETS = "All"


def parse_show_yogas(html: str) -> dict[str, Any]:
    """Parse a `show-yogas` response into plain data.

    Returns ``{"yogas": [...]}`` in the order the site lists them.
    """
    soup = BeautifulSoup(html, "lxml")
    rows = soup.find_all("tr")
    return {"yogas": [yoga for yoga in map(_parse_row, rows) if yoga is not None]}


def _parse_row(row: Tag) -> dict[str, Any] | None:
    cells = row.find_all("td")
    if len(cells) < 4:
        return None

    label = attr(cells[0], "type")
    planets_label = _value(cells[1])
    codes = [code for code in _text(cells[1]).split() if code in PLANET_CODES]

    return {
        "name": _value(cells[0]),
        "category": CATEGORY_KEYS.get(label or ""),
        "category_label": label,
        "planets": codes,
        "planets_label": planets_label,
        "all_planets": planets_label == ALL_PLANETS,
        # Both of these are free text in the site's language.
        "effect": _value(cells[2]),
        "condition": _value(cells[3]),
    }
