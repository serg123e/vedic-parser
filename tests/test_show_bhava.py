"""show-bhava parser tests.

* show-bhava-en-d1.html   actions.php show-bhava, D1, .com
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_bhava, parse_show_chart

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def bhava() -> dict:
    return parse_show_bhava((FIXTURES / "show-bhava-en-d1.html").read_text(encoding="utf-8"))


def test_twelve_houses_in_order(bhava: dict) -> None:
    assert [house["house"] for house in bhava["houses"]] == list(range(1, 13))


def test_first_house(bhava: dict) -> None:
    first = bhava["houses"][0]
    assert first["cusp"] == {
        "sign": "Aries",
        "degrees": "00°33'53''",
        "degrees_decimal": pytest.approx(0.564722, abs=1e-5),
    }
    # A bhava spans two signs: it starts in the previous one.
    assert first["start"]["sign"] == "Pisces"
    assert first["end"]["sign"] == "Aries"
    assert first["size"] == "29°59'58''"
    assert first["planets"] == ["As"]


def test_house_sizes_cover_the_zodiac(bhava: dict) -> None:
    """Unequal houses, but they tile 360° (to arc-second rounding)."""
    total = sum(house["size_decimal"] for house in bhava["houses"])
    assert total == pytest.approx(360, abs=0.01)
    assert len({house["size"] for house in bhava["houses"]}) > 1


def test_several_bodies_in_one_house_are_all_kept(bhava: dict) -> None:
    """The cell separates them with commas, not spaces."""
    fifth = bhava["houses"][4]
    assert fifth["planets"] == ["Su", "Mo", "Ma"]
    assert bhava["houses"][8]["planets"] == ["Ju", "Ke"]
    assert bhava["houses"][1]["planets"] == []  # the site prints "-"


def test_table_and_drawing_agree(bhava: dict) -> None:
    """The response's own chart places the same bodies in the same houses."""
    drawing: dict[int, list[str]] = {}
    for planet in bhava["chart"]["planets"]:
        drawing.setdefault(planet["house"], []).append(planet["code"])
    for house in bhava["houses"]:
        assert sorted(house["planets"]) == sorted(drawing.get(house["house"], []))


def test_embedded_chart_parses_as_a_chart(bhava: dict) -> None:
    assert bhava["chart"]["style"] == "north"
    assert [house["house"] for house in bhava["chart"]["houses"]] == list(range(1, 13))


def test_the_standalone_chart_endpoint_uses_the_same_parser() -> None:
    """show-chart-bhava returns only the drawing, in show-chart's markup."""
    drawing = parse_show_chart(
        (FIXTURES / "show-bhava-en-d1.html").read_text(encoding="utf-8")
    )
    assert drawing["style"] == "north"


def test_rejects_a_response_that_is_not_show_bhava() -> None:
    with pytest.raises(ValueError, match="no table.chart-info"):
        parse_show_bhava("<div>Access Denied</div>")


def test_no_bhava_bala_is_reported(bhava: dict) -> None:
    """Documents an absence: the site gives house geometry, not house strength.

    Nothing in this response carries a bala, so anything needing Bhava Bala has
    to come from elsewhere — the drik bala matrix onto houses in show-bala is
    the only house-level strength the open endpoints have.
    """
    assert set(bhava["houses"][0]) == {
        "house", "cusp", "start", "end", "size", "size_decimal", "planets",
    }


def test_result_is_json_serialisable(bhava: dict) -> None:
    assert json.loads(json.dumps(bhava)) == bhava
