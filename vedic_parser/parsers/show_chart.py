"""Parser for the `show-chart` fragment: one divisional chart drawing.

The site draws the same chart two ways and the markup differs completely:

* North style — ``div.chart-north`` with twelve absolutely positioned
  ``div.house`` blocks. Houses are fixed, so DOM order *is* house order, and
  each block names the sign sitting in it.
* South style — ``table.chart`` with twelve ``td.houses`` cells. Signs are
  fixed, so cell order is sign order, and each cell names the house.

Both are normalised to the same thing: twelve houses, ordered 1..12, each with
its sign, its planets and the planets aspecting it.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from ._html import (
    HOUSE_HREF_RE,
    PLANET_CODES,
    SIGN_HREF_RE,
    attr,
    chart_data,
    code_from_class,
    href_group,
    int_or_none,
    selected_option,
    sign_number,
)
from ._html import text as _text
from ._html import value as _value


def parse_show_chart(html: str) -> dict[str, Any]:
    """Parse a `show-chart` response (either style) into plain data.

    Returns ``{"style", "divisional", "chart", "houses", "planets"}``, where
    ``houses`` is always ordered 1..12 and ``planets`` is the same placement
    data keyed per body, derived from ``houses``.
    """
    soup = BeautifulSoup(html, "lxml")

    north = soup.select_one("div.chart-north")
    south = soup.select_one("table.chart")
    if north is not None:
        style, houses = "north", _parse_north(north)
    elif south is not None:
        style, houses = "south", _parse_south(south)
    else:
        raise ValueError("no chart found; is this a show-chart response?")

    houses.sort(key=lambda house: house["house"])
    return {
        "style": style,
        "divisional": selected_option(soup.select_one("select.divisional")),
        "chart": chart_data(soup),
        "houses": houses,
        "planets": _flatten(houses),
    }


def _parse_north(chart: Tag) -> list[dict[str, Any]]:
    """House blocks in DOM order; the nth block is the nth house."""
    blocks = chart.select("div.house")
    if len(blocks) != 12:
        raise ValueError(f"expected 12 houses in a north chart, got {len(blocks)}")

    houses = []
    for number, block in enumerate(blocks, start=1):
        link = block.select_one(".sign a")
        code = href_group(link, SIGN_HREF_RE)
        houses.append(
            {
                "house": number,
                # The visible label is the sign number; the code and the full
                # name come from the link's href and tooltip.
                "sign": {
                    "number": int_or_none(_text(link)) or sign_number(code),
                    "code": code,
                    "name": attr(link, "title"),
                },
                "planets": _parse_planets(block),
                "aspects": _parse_aspects(block),
            }
        )
    return houses


def _parse_south(chart: Tag) -> list[dict[str, Any]]:
    """Sign cells in drawing order; each names the house it currently holds."""
    cells = chart.select("td.houses")
    if len(cells) != 12:
        raise ValueError(f"expected 12 cells in a south chart, got {len(cells)}")

    houses = []
    for cell in cells:
        sign_link = cell.select_one(".sign a")
        house_link = cell.select_one(".house a")
        code = href_group(sign_link, SIGN_HREF_RE)
        number = int_or_none(href_group(house_link, HOUSE_HREF_RE) or _text(house_link))
        if number is None:
            raise ValueError("a south chart cell carries no house number")
        houses.append(
            {
                "house": number,
                "sign": {
                    "number": sign_number(code),
                    "code": code,
                    # The label is the abbreviation here, the tooltip the name.
                    "name": attr(sign_link, "title"),
                },
                "planets": _parse_planets(cell),
                "aspects": _parse_aspects(cell),
            }
        )
    return houses


def _parse_planets(block: Tag) -> list[dict[str, Any]]:
    """Bodies drawn in this house.

    Degrees are whole degrees only in a chart drawing — ``show-info`` carries
    them to the arc-second. Retrograde is an ``R`` inside a nested div, which
    is present but empty for direct bodies.
    """
    planets = []
    for span in block.select("span.planet"):
        degree = span.select_one(".degree")
        retrograde = span.select_one(".retrograde")
        planets.append(
            {
                "code": code_from_class(span, PLANET_CODES),
                "degree": int_or_none(_text(degree)),
                "degree_label": _value(degree),
                "retrograde": _text(retrograde).upper() == "R",
            }
        )
    return planets


def _parse_aspects(block: Tag) -> list[str]:
    """Planets aspecting this house, as codes.

    North wraps them in ``<u>``, south leaves them as bare text in the div.
    """
    aspects = block.select_one(".aspects")
    return [code for code in _text(aspects).split() if code in PLANET_CODES]


def _flatten(houses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Placements keyed per body, derived from the houses (never re-read)."""
    placements = []
    for house in houses:
        for planet in house["planets"]:
            placements.append(
                {
                    "code": planet["code"],
                    "house": house["house"],
                    "sign": house["sign"]["code"],
                    "sign_number": house["sign"]["number"],
                    "degree": planet["degree"],
                    "retrograde": planet["retrograde"],
                }
            )
    order = {code: index for index, code in enumerate(PLANET_CODES)}
    placements.sort(key=lambda placement: order.get(placement["code"], len(order)))
    return placements
