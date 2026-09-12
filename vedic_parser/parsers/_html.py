"""Helpers shared by the response parsers."""

from __future__ import annotations

import re

from bs4 import Tag

PLANET_CODES = ("As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke")

SIGN_CODES = (
    "Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi",
)

SIGN_HREF_RE = re.compile(r"sign\?(\w+)")
HOUSE_HREF_RE = re.compile(r"house\?(\d+)")


def text(node: Tag | None) -> str:
    """All text of a node, whitespace-collapsed."""
    return node.get_text(" ", strip=True) if node is not None else ""


def value(node: Tag | None) -> str | None:
    """Node text, with the site's ``-`` and ``&nbsp;`` placeholders as None."""
    stripped = text(node).replace("\xa0", "").strip()
    return None if stripped in ("", "-") else stripped


def attr(node: Tag | None, name: str) -> str | None:
    if node is None:
        return None
    return (node.get(name) or "").strip() or None


def href_group(link: Tag | None, pattern: re.Pattern[str]) -> str | None:
    """First capture group of ``pattern`` matched against the link's href."""
    if link is None:
        return None
    match = pattern.search(link.get("href", ""))
    return match.group(1) if match else None


def code_from_class(node: Tag | None, known: tuple[str, ...] = PLANET_CODES) -> str | None:
    """The first class of ``node`` that is a known code, e.g. ``planet Su`` -> ``Su``."""
    if node is None:
        return None
    for name in node.get("class", []):
        if name in known:
            return name
    return None


def int_or_none(raw: str | None) -> int | None:
    match = re.search(r"-?\d+", raw or "")
    return int(match.group(0)) if match else None


def sign_number(code: str | None) -> int | None:
    """``Cn`` -> 4."""
    if code in SIGN_CODES:
        return SIGN_CODES.index(code) + 1
    return None


def chart_data(scope: Tag) -> dict[str, str | None]:
    """The birth data the site echoes back in ``div.chart-data``."""
    block = scope.select_one(".chart-data")
    fields = ("name", "date", "time", "timezone", "latitude", "longitude")
    if block is None:
        return {field: None for field in fields}
    return {field: value(block.select_one(f".chart-{field}")) for field in fields}


def selected_option(select: Tag | None) -> str | None:
    """Value of the option marked selected.

    The site renders the session default here and re-selects the requested one
    in JavaScript, so treat this as a hint, not as what was asked for.
    """
    if select is None:
        return None
    option = select.select_one("option[selected]")
    return attr(option, "value") if option else None
