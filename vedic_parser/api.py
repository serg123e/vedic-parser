"""One function per site action: fetch and parse in a single call."""

from __future__ import annotations

from typing import Any

from datetime import datetime

from .chart import Chart
from .parsers import (
    parse_get_argala,
    parse_get_aspects,
    parse_show_avasthas,
    parse_show_bala,
    parse_show_bhava,
    parse_show_chart,
    parse_show_current_periods,
    parse_show_dasha,
    parse_show_info,
    parse_show_other,
    parse_show_sade_sati,
    parse_show_yogas,
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


def show_yogas(session: Session, chart: Chart, divisional: str = "D1") -> dict[str, Any]:
    """The yogas the chart forms, with the planets, effect and condition of each.

    Only yogas actually present are returned, so the list length varies by
    chart (26 to 42 across the charts tried).
    """
    html = session.action("show-yogas", chart, divisional=divisional)
    result = parse_show_yogas(html)
    result["divisional"] = divisional
    return result


def show_avasthas(session: Session, chart: Chart, divisional: str = "D1") -> dict[str, Any]:
    """The states of the planets: Baladi, Jagradadi, Deeptadi/Lajjitadi and
    Shayanadi avasthas, plus the legend of the Shayanadi states in this chart.

    The Shayanadi strength depends on the first syllable of the person's name,
    so the site reports it for all five syllable groups and leaves the choice
    to the reader.
    """
    html = session.action("show-avasthas", chart, divisional=divisional)
    result = parse_show_avasthas(html)
    result["divisional"] = divisional
    return result


def show_bhava(session: Session, chart: Chart, divisional: str = "D1") -> dict[str, Any]:
    """The Bhava Chalita houses: cusp, boundaries, size and contents of each,
    plus the chart drawing that goes with them.

    Note this endpoint carries no Bhava Bala — the site does not report house
    strengths here or anywhere else that is open anonymously. The closest thing
    available is the drik bala matrix onto houses in :func:`show_bala`.
    """
    html = session.action("show-bhava", chart, divisional=divisional)
    result = parse_show_bhava(html)
    result["divisional"] = divisional
    return result


def show_sade_sati(session: Session, chart: Chart) -> dict[str, Any]:
    """Saturn's passages over the natal Moon, by both methods the site offers.

    Takes no varga: Sade Sati is reckoned from the natal Moon's sign. Each
    method reports four occurrences across a lifetime, so this covers dates far
    beyond a normal span.
    """
    html = session.action("show-sade-sati", chart)
    return parse_show_sade_sati(html)


def get_aspects(
    session: Session, chart: Chart, sign: int, divisional: str = "D1", style: str = "North"
) -> dict[str, Any]:
    """What aspects one sign, and what that sign aspects.

    ``sign`` is an absolute sign number, Aries = 1 — the same number the chart
    prints in each house. The answer names the planets aspecting that sign and
    the signs it aspects by rasi drishti.
    """
    text = session.action(
        "get-aspects", chart, sign=str(sign), divisional=divisional, style=style
    )
    result = parse_get_aspects(text)
    result["sign"] = sign
    return result


def get_argala(
    session: Session,
    chart: Chart,
    sign: int,
    type: int = 1,
    divisional: str = "D1",
    style: str = "North",
) -> dict[str, Any]:
    """Argala and virodha argala on one sign.

    ``sign`` is an absolute sign number, Aries = 1. ``type`` picks the set:
    1 is the primary argala and virodha argala the chart's own link uses, 2 the
    second set; anything else makes the site answer HTTP 500.
    """
    text = session.action(
        "get-argala",
        chart,
        type=str(type),
        sign=str(sign),
        divisional=divisional,
        style=style,
    )
    result = parse_get_argala(text, type=type)
    result["sign"] = sign
    return result


def show_current_periods(
    session: Session, chart: Chart, moment: str | datetime | None = None
) -> dict[str, Any]:
    """Which dasha period is running at one moment, across several systems.

    ``moment`` defaults to now. The site needs it: asked without one it answers
    with the first system's label and nothing else, and a value it cannot parse
    gets the same empty treatment rather than an error — so the moment is
    formatted here the way the site's own JavaScript formats it.

    Sign-based systems come back as sign codes here, unlike ``show-dasha``.
    """
    html = session.action("show-current-periods", chart, datetime=_moment(moment))
    return parse_show_current_periods(html)
