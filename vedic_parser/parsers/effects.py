"""Parsers for `get-aspects` and `get-argala`: the two plain-text endpoints.

Unlike everything else on the site these answer with a compact string rather
than HTML, because the page uses them only to recolour a chart it already has::

    get-aspects, sign=1   ->  "Sa|5 8 11"
    get-argala,  sign=1   ->  "2 12 4 10 11 3"

All numbers are absolute sign numbers (Aries = 1), not positions relative to
the sign asked about — checked against several signs.

For `get-argala` the grouping is taken from the site's own rendering code,
which paints some positions green (argala) and others red (virodha argala).
The six numbers are always the classic positions — the 2nd, 4th and 11th from
the sign, and the 12th, 10th and 3rd that obstruct them — but which group they
land in is the site's verdict, not a formula: for the sign **Ketu occupies**
the two groups come back swapped. Checked over all twelve signs of two charts,
where exactly one sign swapped in each, and it was Ketu's both times (Rahu's
sign does not). So read the groups as given rather than deriving them.
"""

from __future__ import annotations

from typing import Any

from ._html import PLANET_CODES

#: Which positions of the answer the site paints green, red, or its second
#: green, per ``type``. Only types 1 and 2 exist; 3 answers HTTP 500.
ARGALA_LAYOUT = {
    1: {"argala": (0, 2, 4), "virodha": (1, 3, 5), "special": ()},
    2: {"argala": (0, 2), "virodha": (1, 3), "special": (4,)},
}


def parse_get_aspects(text: str) -> dict[str, Any]:
    """Parse a `get-aspects` answer: ``"Sa|5 8 11"``.

    ``planets`` are the bodies aspecting the sign that was asked about — the
    same list the chart shows in that house — and ``signs`` are the signs it
    aspects back by rasi drishti.
    """
    planets_part, _, signs_part = (text or "").partition("|")
    return {
        "planets": [code for code in planets_part.split() if code in PLANET_CODES],
        "signs": _numbers(signs_part),
    }


def parse_get_argala(text: str, type: int = 1) -> dict[str, Any]:
    """Parse a `get-argala` answer: ``"2 12 4 10 11 3"``.

    ``type`` is the set the site asked for — 1 for the primary argala and
    virodha argala its chart links use, 2 for the second set. The raw answer is
    kept in ``signs``; ``argala``, ``virodha`` and ``special`` split it the way
    the site colours those positions.
    """
    signs = _numbers(text)
    layout = ARGALA_LAYOUT.get(type, ARGALA_LAYOUT[1])
    return {
        "type": type,
        "signs": signs,
        **{
            group: [signs[index] for index in positions if index < len(signs)]
            for group, positions in layout.items()
        },
    }


def _numbers(text: str) -> list[int]:
    return [int(token) for token in (text or "").split() if token.isdigit()]
