"""One function per site action: fetch and parse in a single call."""

from __future__ import annotations

from typing import Any

from .chart import Chart
from .parsers import parse_show_info
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
    """
    html = session.action("show-info", chart, divisional=divisional, **{"from": from_})
    info = parse_show_info(html)
    # The response echoes the session's default varga in its <select>, so
    # record what was actually asked for.
    info["divisional"] = divisional
    info["from"] = from_ or None
    return info
