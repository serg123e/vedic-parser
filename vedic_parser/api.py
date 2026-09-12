"""One function per site action: fetch and parse in a single call."""

from __future__ import annotations

from typing import Any

from .chart import Chart
from .parsers import parse_show_chart, parse_show_info
from .session import Session


def show_info(
    session: Session,
    chart: Chart,
    divisional: str = "D1",
    from_: str = "",
) -> dict[str, Any]:
    """The main planets table and Ashtakavarga for one divisional chart.

    ``divisional`` is a varga code (``D1``…``D60``). ``from_`` reckons the
    chart from something other than the Ascendant: ``1`` Sun, ``2`` Moon,
    ``AL`` Arudha Lagna; the site expects ``divisional=D1`` in those cases.

    For a varga other than D1 note that ``rasi`` is still the natal D1 sign
    and ``navamsa`` the D9 sign; only ``degrees``, ``house``, ``bindu`` and the
    balas are recomputed. Use :func:`show_chart` for the signs of that varga.
    """
    html = session.action("show-info", chart, divisional=divisional, **{"from": from_})
    info = parse_show_info(html)
    # The response echoes the session's default varga in its <select>, so
    # record what was actually asked for.
    info["divisional"] = divisional
    info["from"] = from_ or None
    return info


def show_chart(
    session: Session,
    chart: Chart,
    divisional: str = "D1",
    style: str = "North",
    type_: str = "",
) -> dict[str, Any]:
    """One divisional chart drawing: the twelve houses with their contents.

    ``style`` is ``North`` or ``South``; both parse to the same shape, so pick
    whichever the site renders faster unless you need the raw markup. ``type_``
    is passed through for the pages that overlay a second chart and is empty
    for a natal chart.
    """
    html = session.action(
        "show-chart", chart, divisional=divisional, style=style, type=type_
    )
    result = parse_show_chart(html)
    result["divisional"] = divisional  # the markup echoes the session default
    return result
