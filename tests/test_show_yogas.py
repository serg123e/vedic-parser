"""show-yogas parser tests.

* show-yogas-en-d1.html   actions.php show-yogas, D1, .com
* show-yogas-ru-d1.html   the same request against .ru
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_yogas
from vedic_parser.parsers._html import PLANET_CODES
from vedic_parser.parsers.show_yogas import CATEGORY_KEYS

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_yogas((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def yogas() -> dict:
    return load("show-yogas-en-d1.html")


def test_every_row_becomes_a_yoga(yogas: dict) -> None:
    assert len(yogas["yogas"]) == 32
    assert all(yoga["name"] for yoga in yogas["yogas"])
    assert all(yoga["effect"] and yoga["condition"] for yoga in yogas["yogas"])


def test_first_yoga(yogas: dict) -> None:
    assert yogas["yogas"][0] == {
        "name": "Sasa",
        "category": "mahapurusha",
        "category_label": "Mahapurusha",
        "planets": ["Sa"],
        "planets_label": "Sa",
        "all_planets": False,
        "effect": "Wandering leader of free spirit",
        "condition": "Saturn in a kendra in own or exaltation sign",
    }


def test_categories_are_mapped_to_stable_keys(yogas: dict) -> None:
    assert sorted({yoga["category"] for yoga in yogas["yogas"]}) == [
        "lunar", "mahapurusha", "nabhasa", "other", "raja_dhana", "solar",
    ]
    assert all(yoga["category_label"] for yoga in yogas["yogas"])


def test_planet_codes_are_parsed(yogas: dict) -> None:
    chandra_mangala = next(y for y in yogas["yogas"] if y["name"] == "Chandra-Mangala")
    assert chandra_mangala["planets"] == ["Mo", "Ma"]
    assert chandra_mangala["category"] == "lunar"
    for yoga in yogas["yogas"]:
        assert all(code in PLANET_CODES for code in yoga["planets"])


def test_all_planets_marker(yogas: dict) -> None:
    """A yoga over every planet says "All" instead of listing them."""
    kedara = next(y for y in yogas["yogas"] if y["name"] == "Kedara")
    assert kedara["all_planets"] is True
    assert kedara["planets"] == []
    assert kedara["planets_label"] == "All"
    # Everything else names its planets.
    named = [y for y in yogas["yogas"] if not y["all_planets"]]
    assert all(y["planets"] for y in named)


def test_the_same_yoga_can_repeat_from_the_moon(yogas: dict) -> None:
    """The site lists a yoga again when it also forms from the Moon."""
    sasa = [y for y in yogas["yogas"] if y["name"].startswith("Sasa")]
    assert len(sasa) == 2
    assert sasa[1]["name"] == "Sasa (from Moon)"  # the suffix is localised text


def test_russian_response_matches_row_for_row() -> None:
    en, ru = load("show-yogas-en-d1.html"), load("show-yogas-ru-d1.html")
    assert len(en["yogas"]) == len(ru["yogas"])
    for yoga_en, yoga_ru in zip(en["yogas"], ru["yogas"]):
        assert yoga_en["category"] == yoga_ru["category"]
        assert yoga_en["planets"] == yoga_ru["planets"]
        assert yoga_en["all_planets"] == yoga_ru["all_planets"]
        # Names, effects and conditions are localised.
        assert yoga_en["name"] != yoga_ru["name"]
    assert ru["yogas"][0]["category_label"] == "Махапуруша"


def test_unknown_category_keeps_its_label_instead_of_guessing() -> None:
    parsed = parse_show_yogas(
        '<tr><td type="Something New">X</td><td>Su</td><td>e</td><td>c</td></tr>'
    )
    assert parsed["yogas"][0]["category"] is None
    assert parsed["yogas"][0]["category_label"] == "Something New"


def test_every_known_label_maps_to_a_key() -> None:
    assert set(CATEGORY_KEYS.values()) == {
        "mahapurusha", "solar", "lunar", "nabhasa", "raja_dhana", "other",
    }


def test_a_response_with_no_yogas_is_empty_not_an_error() -> None:
    assert parse_show_yogas("") == {"yogas": []}


def test_result_is_json_serialisable(yogas: dict) -> None:
    assert json.loads(json.dumps(yogas)) == yogas
