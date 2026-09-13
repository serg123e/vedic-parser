"""show-vargas and first-house tests.

Both answer with chart markup, so they lean on the show-chart parser; what is
worth pinning down is the batching of one and the rotation of the other.

* show-vargas-en-d1-d9-d10.html   D1 North, D9 North, D10 South, .com
* show-vargas-ru-d1-d9-d10.html   the same request against .ru
* first-house-en-sign4.html       D1 recounted from Cancer, .com
* first-house-en-sign7.html       D1 recounted from Libra, .com
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_chart, parse_show_vargas

FIXTURES = Path(__file__).parent / "fixtures"


def chart(name: str) -> dict:
    return parse_show_chart((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def vargas() -> dict:
    return parse_show_vargas(
        (FIXTURES / "show-vargas-en-d1-d9-d10.html").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def natal() -> dict:
    return chart("show-chart-en-d1-north.html")


def placement(parsed: dict, code: str) -> dict:
    return next(planet for planet in parsed["planets"] if planet["code"] == code)


# -- show-vargas -----------------------------------------------------------


def test_one_chart_per_requested_varga(vargas: dict) -> None:
    assert [c["divisional"] for c in vargas["charts"]] == ["D1", "D9", "D10"]
    for parsed in vargas["charts"]:
        assert [house["house"] for house in parsed["houses"]] == list(range(1, 13))


def test_styles_are_honoured_per_chart(vargas: dict) -> None:
    """The request asked for North, North, South — and got exactly that."""
    assert [c["style"] for c in vargas["charts"]] == ["north", "north", "south"]


def test_the_varga_selector_is_trustworthy_here(vargas: dict) -> None:
    """Unlike show-info, each block's select names that block's own varga."""
    assert vargas["charts"][1]["divisional"] == "D9"
    assert vargas["charts"][2]["divisional"] == "D10"


def test_batched_charts_match_the_single_requests(vargas: dict, natal: dict) -> None:
    """The same data a chart-at-a-time request gives, in one response."""
    d1, d9 = vargas["charts"][0], vargas["charts"][1]
    for planet in natal["planets"]:
        assert placement(d1, planet["code"])["house"] == planet["house"]
        assert placement(d1, planet["code"])["sign"] == planet["sign"]

    separate_d9 = chart("show-chart-en-d9-south.html")
    for planet in separate_d9["planets"]:
        batched = placement(d9, planet["code"])
        assert batched["house"] == planet["house"]
        assert batched["sign"] == planet["sign"]


def test_russian_response_gives_the_same_placements(vargas: dict) -> None:
    russian = parse_show_vargas(
        (FIXTURES / "show-vargas-ru-d1-d9-d10.html").read_text(encoding="utf-8")
    )
    assert [c["divisional"] for c in russian["charts"]] == ["D1", "D9", "D10"]
    for chart_ru, chart_en in zip(russian["charts"], vargas["charts"]):
        assert [(p["code"], p["house"], p["sign"]) for p in chart_ru["planets"]] == [
            (p["code"], p["house"], p["sign"]) for p in chart_en["planets"]
        ]
    # Only the sign names are translated.
    assert russian["charts"][0]["houses"][0]["sign"]["name"] == "Овен"


def test_rejects_a_response_with_no_chart_blocks() -> None:
    with pytest.raises(ValueError, match="no div.chart-block"):
        parse_show_vargas("<div>Access Denied</div>")


def test_result_is_json_serialisable(vargas: dict) -> None:
    assert json.loads(json.dumps(vargas)) == vargas


# -- first-house -----------------------------------------------------------


@pytest.mark.parametrize(("name", "sign"), [("first-house-en-sign4.html", 4),
                                            ("first-house-en-sign7.html", 7)])
def test_first_house_puts_the_chosen_sign_first(name: str, sign: int) -> None:
    rotated = chart(name)
    assert rotated["houses"][0]["sign"]["number"] == sign


@pytest.mark.parametrize(("name", "sign"), [("first-house-en-sign4.html", 4),
                                            ("first-house-en-sign7.html", 7)])
def test_first_house_only_renumbers_the_houses(name: str, sign: int, natal: dict) -> None:
    """Nothing moves: each body keeps its sign and its house count rotates.

    A body in sign S lands in the house S is from the chosen sign.
    """
    rotated = chart(name)
    for planet in natal["planets"]:
        moved = placement(rotated, planet["code"])
        assert moved["sign"] == planet["sign"]
        assert moved["degree"] == planet["degree"]
        assert moved["house"] == (moved["sign_number"] - sign) % 12 + 1


def test_first_house_from_the_ascendant_sign_is_the_natal_chart(natal: dict) -> None:
    """Sanity: the natal chart is this same rotation, from the rising sign."""
    rising = natal["houses"][0]["sign"]["number"]
    for planet in natal["planets"]:
        assert planet["house"] == (planet["sign_number"] - rising) % 12 + 1
