"""show-current-periods parser tests.

* show-current-periods-en-2026.html   asked for 13.09.2026, .com
* show-current-periods-en-birth.html  asked for the moment of birth, .com
* show-current-periods-ru-2026.html   the same 13.09.2026 request against .ru
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import (
    parse_show_chart,
    parse_show_current_periods,
    parse_show_dasha,
)
from vedic_parser.parsers.show_current_periods import DASHA_TITLES

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_current_periods((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current() -> dict:
    return load("show-current-periods-en-2026.html")


def by_key(parsed: dict, key: str) -> dict:
    return next(dasha for dasha in parsed["dashas"] if dasha["dasha"] == key)


def test_the_echoed_date_is_parsed(current: dict) -> None:
    assert current["date_label"] == "13.09.2026"
    assert current["date"] == "2026-09-13"


def test_all_four_systems_are_keyed(current: dict) -> None:
    assert [dasha["dasha"] for dasha in current["dashas"]] == [
        "vimshottari", "yogini", "chara_rao", "narayana",
    ]
    assert [dasha["abbr"] for dasha in current["dashas"]] == ["VD", "YD", "CD", "ND"]


def test_planet_and_sign_systems_are_told_apart(current: dict) -> None:
    assert by_key(current, "vimshottari") == {
        "dasha": "vimshottari",
        "title": "Vimshottari dasha",
        "abbr": "VD",
        "kind": "planet",
        "lords": ["Ve", "Mo", "Ra"],
    }
    # Sign systems come back as codes here — show-dasha only gives their names.
    assert by_key(current, "chara_rao")["kind"] == "sign"
    assert by_key(current, "chara_rao")["lords"] == ["Sg", "Le", "Cp"]
    assert by_key(current, "narayana")["lords"] == ["Ta", "Cn", "Pi"]


def test_every_chain_is_three_deep(current: dict) -> None:
    for dasha in current["dashas"]:
        assert len(dasha["lords"]) == 3


def test_the_chain_agrees_with_show_dasha() -> None:
    """The running periods are the same ones the dasha table lists."""
    antar = parse_show_dasha(
        (FIXTURES / "show-dasha-en-vimshottari-l2.html").read_text(encoding="utf-8")
    )
    for name, moment in [
        ("show-current-periods-en-2026.html", "2026-09-13T00:00"),
        ("show-current-periods-en-birth.html", "1983-08-07T23:00"),
    ]:
        running = next(p for p in antar["periods"] if p["start"] <= moment < p["end"])
        assert by_key(load(name), "vimshottari")["lords"][:2] == running["lords"]


def test_the_sign_chain_agrees_with_show_dasha_too() -> None:
    """Mapping the chara table's localised names through a chart's sign codes."""
    chart = parse_show_chart(
        (FIXTURES / "show-chart-en-d1-north.html").read_text(encoding="utf-8")
    )
    code_of = {house["sign"]["name"]: house["sign"]["code"] for house in chart["houses"]}
    chara = parse_show_dasha(
        (FIXTURES / "show-dasha-en-chara-l2.html").read_text(encoding="utf-8")
    )
    moment = "2026-09-13T00:00"
    running = next(p for p in chara["periods"] if p["start"] <= moment < p["end"])

    current = load("show-current-periods-en-2026.html")
    assert [code_of[label] for label in running["labels"]] == (
        by_key(current, "chara_rao")["lords"][:2]
    )


def test_a_different_moment_gives_different_periods(current: dict) -> None:
    birth = load("show-current-periods-en-birth.html")
    assert birth["date"] == "1983-08-07"
    assert by_key(birth, "vimshottari")["lords"] == ["Sa", "Me", "Ra"]
    assert by_key(birth, "vimshottari")["lords"] != by_key(current, "vimshottari")["lords"]


def test_titles_cover_every_system_the_site_offers() -> None:
    """The table keys the systems by the site's own wording, in both languages.

    Six systems, two languages — and the keys are the ones show-dasha takes.
    """
    assert set(DASHA_TITLES.values()) == {
        "vimshottari", "yogini", "ashtottari", "chara_rao", "narayana", "navamsa",
    }
    assert len(DASHA_TITLES) == 12


def test_russian_response_keys_the_same_systems(current: dict) -> None:
    """The whole point of the title table: both languages give the same keys."""
    russian = load("show-current-periods-ru-2026.html")
    assert russian["date"] == current["date"]
    assert [d["dasha"] for d in russian["dashas"]] == [d["dasha"] for d in current["dashas"]]
    for dasha_ru, dasha_en in zip(russian["dashas"], current["dashas"]):
        # Codes are identical, wording is not.
        assert dasha_ru["lords"] == dasha_en["lords"]
        assert dasha_ru["kind"] == dasha_en["kind"]
        assert dasha_ru["title"] != dasha_en["title"]
        assert dasha_ru["abbr"] != dasha_en["abbr"]
    assert russian["dashas"][0]["abbr"] == "ВД"
    assert russian["dashas"][2]["title"] == "Чара даша (К.Н. Рао)"


def test_unknown_system_keeps_its_label(current: dict) -> None:
    parsed = parse_show_current_periods(
        '<b title="Kalachakra dasha">KD: </b><span class="Su">Su</span>'
    )
    assert parsed["dashas"][0]["dasha"] is None
    assert parsed["dashas"][0]["title"] == "Kalachakra dasha"
    assert parsed["dashas"][0]["lords"] == ["Su"]


def test_an_answer_without_a_moment_is_empty_not_broken() -> None:
    """Asked without a datetime the site returns a label and no chain."""
    parsed = parse_show_current_periods(
        '<span style="color: #475D63;"></span><b title="Vimshottari dasha">VD: </b>'
    )
    assert parsed["date"] is None
    assert parsed["dashas"][0]["lords"] == []
    assert parsed["dashas"][0]["kind"] is None


def test_result_is_json_serialisable(current: dict) -> None:
    assert json.loads(json.dumps(current)) == current
