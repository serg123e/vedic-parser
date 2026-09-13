"""Parser for the `show-current-periods` fragment: the periods running at a moment.

One compact line covering several dasha systems at once::

    <span>13.09.2026</span>&nbsp;
    <b title="Vimshottari dasha">VD: </b><span class="Ve">Ve</span>-<span class="Mo">Mo</span>-…
    <b title="Chara dasha (K.N. Rao)">CD: </b>Sg-Le-Cp

Both the abbreviation and the tooltip are localised ("ВД: ", "Вимшоттари даша"),
so the system is keyed through :data:`DASHA_TITLES`, which holds the site's own
wording in both languages — the same strings its dasha selector uses.

Worth knowing: unlike ``show-dasha``, the sign-based systems come back here as
sign **codes** (``Sg-Le-Cp``) rather than localised names, so this is the one
place where a chara or narayana period is language-independent.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from ._html import PLANET_CODES, SIGN_CODES, code_from_class, iso_moment
from ._html import text as _text
from ._html import value as _value

#: The site's name for each dasha system, per language, to the key
#: ``show-dasha`` uses. Verified against the dasha selector of both domains.
DASHA_TITLES = {
    "Vimshottari dasha": "vimshottari",
    "Вимшоттари даша": "vimshottari",
    "Yogini dasha": "yogini",
    "Йогини даша": "yogini",
    "Ashtottari dasha": "ashtottari",
    "Аштоттари даша": "ashtottari",
    "Chara dasha (K.N. Rao)": "chara_rao",
    "Чара даша (К.Н. Рао)": "chara_rao",
    "Narayana dasha": "narayana",
    "Нарайана даша": "narayana",
    "Navamsa dasha": "navamsa",
    "Навамша даша": "navamsa",
}


def parse_show_current_periods(html: str) -> dict[str, Any]:
    """Parse a `show-current-periods` response into plain data.

    Returns ``{"date", "date_label", "dashas"}``. ``date`` is the moment the
    site echoed back, in ISO form when it echoed a date it understood.
    """
    soup = BeautifulSoup(html, "lxml")

    label = soup.find("span")
    dashas = [_parse_system(node) for node in soup.find_all("b")]
    return {
        "date": _date(_value(label)),
        "date_label": _value(label),
        "dashas": dashas,
    }


def _parse_system(marker: Tag) -> dict[str, Any]:
    """One system: its label, and the chain of lords running at that moment."""
    title = (marker.get("title") or "").strip() or None
    codes = _chain(marker)
    planets = [code for code in codes if code in PLANET_CODES]

    return {
        "dasha": DASHA_TITLES.get(title or ""),
        "title": title,
        # "VD: " — the abbreviation, localised like the title.
        "abbr": _text(marker).rstrip(": ").strip() or None,
        "kind": ("planet" if planets else "sign") if codes else None,
        "lords": codes,
    }


def _chain(marker: Tag) -> list[str]:
    """Codes between this marker and the next one.

    Planet lords arrive as spans carrying the code as a class, sign lords as
    bare text joined by hyphens; both are read as codes.
    """
    codes: list[str] = []
    for node in marker.next_siblings:
        if isinstance(node, NavigableString):
            codes.extend(_tokens(str(node)))
            continue
        if node.name == "b":
            break
        code = code_from_class(node, PLANET_CODES)
        codes.append(code) if code else codes.extend(_tokens(_text(node)))
    return codes


def _tokens(raw: str) -> list[str]:
    """Sign codes out of "Sg-Le-Cp", ignoring the separators around it."""
    return [
        token
        for token in raw.replace("\xa0", " ").replace("-", " ").split()
        if token in SIGN_CODES
    ]


def _date(label: str | None) -> str | None:
    """The echoed date as ISO, when the site echoed one it parsed."""
    moment = iso_moment(f"{label} 00:00") if label else None
    return moment.split("T")[0] if moment else None
