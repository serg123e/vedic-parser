"""One function per site action: fetch and parse in a single call."""

from __future__ import annotations

from typing import Any

from datetime import datetime

from .chart import Chart
from .parsers import (
    parse_show_bala,
    parse_show_chart,
    parse_show_dasha,
    parse_show_info,
    parse_show_other,
)
from .session import Session

#: The dasha systems the site offers, as the ``dasha`` parameter spells them.
DASHAS = (
    "vimshottari",
    "yogini",
    "ashtottari",
    "chara_rao",
    "narayana",
    "navamsa",
)


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


def show_other(session: Session, chart: Chart, divisional: str = "D1") -> dict[str, Any]:
    """The "Other" tab: special lagnas and sphutas, panchanga, upagrahas,
    single points (ayanamsa, badhaka, dagdha rasi, …) and the chakras.

    Only the parts that depend on a varga follow ``divisional``; the panchanga
    and the ayanamsa are properties of the moment, not of a chart.
    """
    html = session.action("show-other", chart, divisional=divisional)
    result = parse_show_other(html)
    result["divisional"] = divisional
    return result


def show_dasha(
    session: Session,
    chart: Chart,
    dasha: str = "vimshottari",
    level: int = 2,
    divisional: str = "D1",
    cycle: int = 0,
    current: str | datetime | None = None,
    search: str = "",
) -> dict[str, Any]:
    """One dasha table: every period with its exact boundaries.

    ``dasha`` is one of :data:`DASHAS`. ``level`` is the depth of the chain —
    1 maha, 2 antar, 3 pratyantar, 4 sookshma; each level multiplies the number
    of rows, so level 3 of vimshottari is already ~700 periods. ``current``
    picks which stretch of the sequence to return (default: now) and ``cycle``
    steps whole cycles away from it, matching the arrows in the site's own UI.
    """
    if dasha not in DASHAS:
        raise ValueError(f"dasha must be one of {DASHAS}, got {dasha!r}")
    html = session.action(
        "show-dasha",
        chart,
        dasha=dasha,
        level=str(level),
        divisional=divisional,
        cycle=str(cycle),
        current=_moment(current),
        search=search,
    )
    result = parse_show_dasha(html)
    result["dasha"] = dasha
    result["divisional"] = divisional
    return result


def _moment(value: str | datetime | None) -> str:
    """Format a moment the way the site's own JavaScript does (unpadded)."""
    if isinstance(value, str):
        return value
    moment = value or datetime.now()
    return (
        f"{moment.day}.{moment.month}.{moment.year} {moment.hour}:{moment.minute}"
    )


def show_bala(
    session: Session, chart: Chart, divisional: str = "D1", full: bool = True
) -> dict[str, Any]:
    """Planetary strengths: Shad Bala with its components, varga strengths and
    the two aspect matrices.

    ``full`` picks the endpoint: ``show-bala`` returns all four tables, while
    ``show-shad-bala`` returns the Shad Bala one alone (a third of the size).
    Both parse to the same shape, with the missing parts empty.
    """
    html = session.action(
        "show-bala" if full else "show-shad-bala", chart, divisional=divisional
    )
    result = parse_show_bala(html)
    result["divisional"] = divisional
    return result
