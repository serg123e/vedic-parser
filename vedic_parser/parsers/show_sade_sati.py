"""Parser for the `show-sade-sati` fragment: Saturn's transits over the Moon.

This response is loose markup rather than a table — bold headings, nested divs
and styling — but every date is machine-readable::

    <span class="data" data="23.07.2002 00:00">23 Jul 2002</span>

So dates are read from the ``data`` attributes, never from the rendered text.

The site reports two methods (traditional and Shri H.N. Katwe), each with four
occurrences over a lifetime. An occurrence has one continuous main span plus
the phases inside it (Saturn in the 12th, 1st and 2nd, back and forth as it
turns retrograde), and sometimes stretches outside that span, when Saturn
brushes the sign early or returns to it later.

One quirk forces the approach: the div holding the phases has an unterminated
``style`` attribute, which swallows the first ``<u>`` wrapper in any parser. So
segments are found by walking the date spans themselves, not by relying on the
element that wraps them.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from ._html import iso_moment
from ._html import text as _text
from ._html import value as _value

HOUSE_RE = re.compile(r"(\d+)")


def parse_show_sade_sati(html: str) -> dict[str, Any]:
    """Parse a `show-sade-sati` response into plain data.

    Returns ``{"methods": [...]}``, one entry per calculation method, each with
    its occurrences in chronological order.
    """
    soup = BeautifulSoup(html, "lxml")
    root = soup.body or soup

    methods: list[dict[str, Any]] = []
    for node in root.find_all(recursive=False):
        if node.name == "b":
            methods.append({"title": _value(node), "periods": []})
        elif node.name == "div" and node.select("span.data"):
            if not methods:  # a response that opens with a block
                methods.append({"title": None, "periods": []})
            methods[-1]["periods"].append(_parse_period(node))
    return {"methods": methods}


def _parse_period(block: Tag) -> dict[str, Any]:
    """One occurrence: its main span, and every dated segment in order."""
    title = None
    main: dict[str, Any] | None = None
    segments: list[dict[str, Any]] = []

    for child in block.find_all("div", recursive=False):
        dates = child.select("span.data")
        if not dates:
            title = title or _value(child)
            continue
        inside = bool(child.find("u")) or len(dates) > 2
        for segment in _segments(child):
            if not inside and segment["description"] is None:
                # A range on its own, with no placement text: the main span.
                main = segment
                continue
            segment["within_main"] = inside
            segments.append(segment)

    return {
        "title": title,
        "start": main["start"] if main else None,
        "end": main["end"] if main else None,
        "segments": segments,
    }


def _segments(scope: Tag) -> list[dict[str, Any]]:
    """Every start/end pair under ``scope``, with the text that follows it."""
    dates = scope.select("span.data")
    segments = []
    for index in range(0, len(dates) - 1, 2):
        start, end = dates[index], dates[index + 1]
        description = _description(end)
        segments.append(
            {
                "start": iso_moment(start.get("data")),
                "end": iso_moment(end.get("data")),
                "description": description,
                # "Saturn in 12th in Gemini" — the number survives translation,
                # the rest of the wording does not.
                "house": _house(description),
            }
        )
    return segments


def _description(end: Tag) -> str | None:
    """Text following the closing date, up to the next dated segment."""
    parts = []
    for node in end.next_siblings:
        if isinstance(node, NavigableString):
            parts.append(str(node))
            continue
        if "data" in (node.get("class") or []) or node.select_one("span.data"):
            break
        parts.append(_text(node))
    text = " ".join(part.strip() for part in parts if part.strip())
    return text.strip(" -–—") or None


def _house(description: str | None) -> int | None:
    match = HOUSE_RE.search(description or "")
    return int(match.group(1)) if match else None
