"""Parser tests against recorded responses.

Fixtures were captured with scripts/probe.sh for
Ss, 07.08.1983 23:00:00, +4, 55.45 N 37.37 E:

* show-info-en.html          actions.php show-info, D1, vedic-horo.com
* show-info-ru-d9.html       actions.php show-info, D9, vedic-horo.ru
* analyse-natal-info-ru.html the #natal-info block of a full analyse.php page
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_info
from vedic_parser.chart import parse_degrees

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_info((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def info_en() -> dict:
    return load("show-info-en.html")


def by_code(info: dict, code: str) -> dict:
    return next(planet for planet in info["planets"] if planet["code"] == code)


def test_all_ten_bodies_are_parsed(info_en: dict) -> None:
    assert [planet["code"] for planet in info_en["planets"]] == [
        "As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke",
    ]
    assert info_en["divisional"] == "D1"


def test_sun_row(info_en: dict) -> None:
    sun = by_code(info_en, "Su")
    assert sun["name"] == "Sun"
    assert sun["retrograde"] is False
    assert sun["karaka"] == "AK"
    assert sun["degrees"] == "21°05'41''"
    assert sun["degrees_decimal"] == pytest.approx(21.094722, abs=1e-5)
    assert sun["rasi"] == {"code": "Cn", "name": "Cancer", "dignity": "Friend"}
    assert sun["navamsa"] == "Capricorn"
    assert sun["nakshatra"] == {"code": "Asl", "name": "Aslesha", "pada": 2, "lord": "Me"}
    assert sun["house"] == 4
    assert sun["shad_bala"] == 124
    assert sun["bindu"] == {"sav": 26, "bav": 7}
    assert sun["functional_beneficence"]["code"] == "B"
    assert "Benefic" in sun["functional_beneficence"]["description"]
    assert sun["planetary_war"] is None


def test_lordship_is_read_from_hrefs(info_en: dict) -> None:
    # Mars rules the 1st and the 8th and sits in the 4th.
    mars = by_code(info_en, "Ma")
    assert [(lord["house"], lord["in_house"]) for lord in mars["lords"]] == [(1, 4), (8, 4)]
    assert all(lord["co_lord"] is False for lord in mars["lords"])


def test_nodes_are_marked_retrograde_and_co_lords(info_en: dict) -> None:
    rahu = by_code(info_en, "Ra")
    assert rahu["retrograde"] is True
    assert rahu["name"] == "Rahu"
    assert rahu["house"] == 3
    assert rahu["shad_bala"] is None
    assert rahu["bindu"] == {"sav": 31, "bav": None}
    assert [(lord["house"], lord["co_lord"]) for lord in rahu["lords"]] == [(11, True)]


def test_ascendant_has_no_house_or_karaka(info_en: dict) -> None:
    ascendant = by_code(info_en, "As")
    assert ascendant["house"] is None
    assert ascendant["karaka"] is None
    assert ascendant["relationship"] is None
    assert ascendant["degrees_decimal"] == pytest.approx(0.564722, abs=1e-5)
    # Gandanta, Sandhi, Mrityu Bhaga, Vargottama
    assert [marker["code"] for marker in ascendant["position"]] == ["G1°", "S", "MB", "V"]
    assert "Vargottama" in ascendant["position"][-1]["description"]


def test_dignity_comes_from_the_sign_tooltip(info_en: dict) -> None:
    assert by_code(info_en, "Sa")["rasi"]["dignity"] == "Exaltation"
    assert by_code(info_en, "Ke")["rasi"]["dignity"] == "Moolatrikona"


def test_ashtakavarga(info_en: dict) -> None:
    ashtakavarga = info_en["ashtakavarga"]
    assert ashtakavarga["first_house_sign"] == 1  # Aries rises
    assert ashtakavarga["sav"] == [35, 38, 31, 26, 28, 29, 25, 18, 28, 31, 27, 21]
    assert sorted(ashtakavarga["bav"]) == ["As", "Ju", "Ma", "Me", "Mo", "Sa", "Su", "Ve"]
    assert all(len(values) == 12 for values in ashtakavarga["bav"].values())
    # Sarvashtakavarga sums the seven planetary Bhinnashtakavargas; the
    # Ascendant's own BAV is shown alongside but not counted.
    planets = {code: values for code, values in ashtakavarga["bav"].items() if code != "As"}
    for house, total in enumerate(ashtakavarga["sav"]):
        assert total == sum(values[house] for values in planets.values())


def test_bindu_column_agrees_with_the_ashtakavarga_blocks(info_en: dict) -> None:
    ashtakavarga = info_en["ashtakavarga"]
    for planet in info_en["planets"]:
        house = planet["house"] or 1  # the Ascendant is in the 1st by definition
        assert planet["bindu"]["sav"] == ashtakavarga["sav"][house - 1]
        if planet["code"] in ashtakavarga["bav"]:
            assert planet["bindu"]["bav"] == ashtakavarga["bav"][planet["code"]][house - 1]


def test_russian_response_parses_to_the_same_shape() -> None:
    info_ru = load("show-info-ru-d9.html")
    # The fragment was fetched with divisional=D9 but its <select> still shows
    # the session default; the missing Nakshatra column is what gives the
    # varga away. api.show_info() records the requested one instead.
    assert info_ru["divisional"] == "D1"
    assert [planet["code"] for planet in info_ru["planets"]] == [
        "As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke",
    ]
    sun = by_code(info_ru, "Su")
    assert sun["name"] == "Солнце"  # labels stay in the site's language
    assert sun["rasi"]["code"] == "Cn"  # codes do not
    assert sun["house"] == 10
    assert sun["degrees_decimal"] is not None
    # Only D1 carries a Nakshatra column.
    assert sun["nakshatra"] is None


def test_full_page_natal_info_block_parses() -> None:
    """The block inside analyse.php has no <thead>; the header is still skipped."""
    info = load("analyse-natal-info-ru.html")
    assert len(info["planets"]) == 10
    assert by_code(info, "Su")["house"] == 4
    assert info["ashtakavarga"]["sav"][0] == 35


def test_result_is_json_serialisable(info_en: dict) -> None:
    assert json.loads(json.dumps(info_en)) == info_en


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("21°05'41''", 21.094722),
        ("00°33'53''", 0.564722),
        ("15°", 15.0),
        ("-", None),
        ("", None),
    ],
)
def test_parse_degrees(text: str, expected: float | None) -> None:
    result = parse_degrees(text)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected, abs=1e-5)
