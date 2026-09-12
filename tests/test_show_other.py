"""show-other parser tests.

* show-other-en-d1.html    actions.php show-other, D1, .com
* analyse-other-ru.html    the #other block of a full analyse.php page, .ru

This response carries no classes or hrefs at all, so the parser leans on
position. These tests pin that positional mapping down in both languages.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_other
from vedic_parser.parsers.show_other import LAGNA_KEYS, POINT_KEYS, UPAGRAHA_KEYS

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_other((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def other() -> dict:
    return load("show-other-en-d1.html")


@pytest.fixture(scope="module")
def other_ru() -> dict:
    return load("analyse-other-ru.html")


def test_all_five_tables_are_found(other: dict) -> None:
    assert len(other["lagnas"]) == 15
    assert len(other["upagrahas"]) == 11
    assert len(other["chakras"]) == 6
    assert len(other["panchanga"]) == 7
    assert len(other["points"]) == 8


def test_special_lagnas(other: dict) -> None:
    assert [lagna["key"] for lagna in other["lagnas"]] == list(LAGNA_KEYS)
    bhava = other["lagnas"][0]
    assert bhava == {
        "key": "bhava_lagna",
        "name": "Bhava Lagna",
        "degrees": "08°43'54''",
        "degrees_decimal": pytest.approx(8.731667, abs=1e-5),
        "sign": "Aries",
        "nakshatra": {"name": "Ashvini", "pada": 3, "lord": "Ke"},
    }
    bhrigu = next(x for x in other["lagnas"] if x["key"] == "bhrigu_bindu")
    assert bhrigu["sign"] == "Gemini"
    assert bhrigu["nakshatra"] == {"name": "Ardra", "pada": 4, "lord": "Ra"}


def test_panchanga_splits_off_the_ruling_planet(other: dict) -> None:
    panchanga = other["panchanga"]
    assert panchanga["sunrise"]["value"] == "05:46:42"
    assert panchanga["sunset"]["value"] == "21:22:39"
    assert panchanga["hora"]["value"] == "Moon"
    assert panchanga["vara"]["value"] == "Sun"
    assert panchanga["tithi"] == {"value": "29 K. Chaturdashi", "lord": "Sa", "label": "Tithi"}
    assert panchanga["yoga"] == {"value": "Siddhi", "lord": "Ma", "label": "Yoga"}
    # The site prints a trailing comma with no planet after this one.
    assert panchanga["karana"] == {"value": "Shakuni", "lord": None, "label": "Karana"}


def test_a_time_is_not_mistaken_for_a_lord(other: dict) -> None:
    assert other["panchanga"]["sunrise"]["lord"] is None


def test_upagrahas_carry_a_house(other: dict) -> None:
    assert [x["key"] for x in other["upagrahas"]] == list(UPAGRAHA_KEYS)
    gulika = next(x for x in other["upagrahas"] if x["key"] == "gulika")
    assert gulika["degrees"] == "18°25'35''"
    assert gulika["sign"] == "Aries"
    assert gulika["house"] == 1
    assert gulika["nakshatra"]["name"] == "Bharani"
    assert all(1 <= x["house"] <= 12 for x in other["upagrahas"])


def test_points_table(other: dict) -> None:
    points = other["points"]
    assert points["ayanamsa"]["value"] == "23°36'22''"
    assert points["sahayogi"]["value"] == "Saturn"
    assert points["badhaka"]["value"] == "Aquarius (Sa/Ra)"
    # Two lines: reckoned from the Ascendant and from the Moon.
    assert points["drekkana_22"]["value"] == ["Scorpio 0°-10° (Ma)", "Aquarius 0°-10° (Sa)"]
    assert points["dagdha_rasi"]["value"] == ["Gemini, Virgo", "Sagittarius, Pisces"]
    # A run of planet codes becomes a list.
    assert points["sarpa_drekkana"]["value"] == ["Su", "Ju"]
    assert points["visha_navamsa"]["value"] == ["As", "Me", "Ve", "Ke"]


def test_chakras(other: dict) -> None:
    assert [chakra["number"] for chakra in other["chakras"]] == [1, 2, 3, 4, 5, 6]
    assert other["chakras"][2] == {
        "number": 3,
        "name": "Manipura",  # the site packs "3 | Manipura" into one cell
        "meaning": "Navel",
        "element": "Fire",
        "signs": ["Aries", "Scorpio"],
        "planets": ["Mars", "Sun"],
        "in_sign": ["Ascendant", "Jupiter"],
    }
    # An empty cell is an empty list, not a "-" string.
    assert other["chakras"][0]["in_sign"] == []


def test_russian_response_gets_the_same_keys(other: dict, other_ru: dict) -> None:
    assert [lagna["key"] for lagna in other_ru["lagnas"]] == list(LAGNA_KEYS)
    assert [x["key"] for x in other_ru["upagrahas"]] == list(UPAGRAHA_KEYS)
    assert list(other_ru["points"]) == list(POINT_KEYS) == list(other["points"])
    assert list(other_ru["panchanga"]) == list(other["panchanga"])
    assert other_ru["lagnas"][0]["name"] == "Бхава Лагна"
    assert other_ru["panchanga"]["tithi"]["lord"] == "Sa"  # code stays latin
    assert other_ru["chakras"][0]["name"] == "Муладхара"


def test_values_agree_across_languages(other: dict, other_ru: dict) -> None:
    """Same chart, same numbers — only the labels differ."""
    for en, ru in zip(other["lagnas"], other_ru["lagnas"]):
        assert en["degrees"] == ru["degrees"]
        assert en["nakshatra"]["pada"] == ru["nakshatra"]["pada"]
        assert en["nakshatra"]["lord"] == ru["nakshatra"]["lord"]
    for en, ru in zip(other["upagrahas"], other_ru["upagrahas"]):
        assert (en["degrees"], en["house"]) == (ru["degrees"], ru["house"])
    assert other["points"]["ayanamsa"]["value"] == other_ru["points"]["ayanamsa"]["value"]


def test_rejects_a_response_that_is_not_show_other() -> None:
    with pytest.raises(ValueError, match="no table.chart-info"):
        parse_show_other("<html><body>Access Denied</body></html>")


def test_result_is_json_serialisable(other: dict) -> None:
    assert json.loads(json.dumps(other)) == other
