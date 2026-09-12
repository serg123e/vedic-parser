"""show-chart parser tests, against recorded responses for the same chart.

* show-chart-en-d1-north.html  actions.php show-chart, D1, style=North, .com
* show-chart-en-d9-south.html  actions.php show-chart, D9, style=South, .com
* show-chart-ru-d1-north.html  the first chart block of an analyse.php page, .ru
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_chart, parse_show_info

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_chart((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def north() -> dict:
    return load("show-chart-en-d1-north.html")


@pytest.fixture(scope="module")
def south() -> dict:
    return load("show-chart-en-d9-south.html")


def placement(chart: dict, code: str) -> dict:
    return next(p for p in chart["planets"] if p["code"] == code)


def test_north_is_recognised_and_echoes_the_birth_data(north: dict) -> None:
    assert north["style"] == "north"
    assert north["chart"] == {
        "name": "Ss",
        "date": "07.08.1983",
        "time": "23:00:00",
        "timezone": "+4",
        "latitude": "55.45",
        "longitude": "37.37",
    }


def test_houses_are_ordered_and_complete(north: dict, south: dict) -> None:
    for chart in (north, south):
        assert [house["house"] for house in chart["houses"]] == list(range(1, 13))
        assert all(house["sign"]["code"] for house in chart["houses"])


def test_signs_run_consecutively_from_the_ascendant(north: dict) -> None:
    """Houses are twelve consecutive signs, wrapping after Pisces."""
    numbers = [house["sign"]["number"] for house in north["houses"]]
    assert numbers == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Aries rises
    assert north["houses"][3]["sign"] == {"number": 4, "code": "Cn", "name": "Cancer"}


def test_planets_in_a_house(north: dict) -> None:
    fourth = north["houses"][3]
    assert [planet["code"] for planet in fourth["planets"]] == ["Ma", "Mo", "Su"]
    assert fourth["planets"][2] == {
        "code": "Su",
        "degree": 21,
        "degree_label": "21°",
        "retrograde": False,
    }
    assert fourth["aspects"] == ["Ju", "Sa"]


def test_retrograde_comes_from_the_nested_marker(north: dict) -> None:
    assert placement(north, "Ra")["retrograde"] is True
    assert placement(north, "Ke")["retrograde"] is True
    assert placement(north, "Ve")["retrograde"] is True
    assert placement(north, "Su")["retrograde"] is False


def test_empty_houses_are_kept_as_empty(north: dict) -> None:
    sixth = north["houses"][5]
    assert sixth["planets"] == []
    assert sixth["aspects"] == []


def test_flat_placements_are_derived_from_the_houses(north: dict) -> None:
    assert [planet["code"] for planet in north["planets"]] == [
        "As", "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke",
    ]
    for placed in north["planets"]:
        house = north["houses"][placed["house"] - 1]
        assert placed["sign"] == house["sign"]["code"]
        assert placed["code"] in [planet["code"] for planet in house["planets"]]


def test_south_style_parses_to_the_same_shape(south: dict) -> None:
    assert south["style"] == "south"
    # Signs are fixed in a south chart, so the cells arrive out of house order
    # and the parser has to reorder them.
    assert [house["sign"]["code"] for house in south["houses"]][:4] == ["Ar", "Ta", "Ge", "Cn"]
    assert placement(south, "Su")["house"] == 10
    assert placement(south, "Ke")["house"] == 1
    assert placement(south, "Ke")["retrograde"] is True
    # Two bodies share the first house in this varga.
    assert [planet["code"] for planet in south["houses"][0]["planets"]] == ["Ke", "As"]


def test_aspects_are_codes_in_both_styles(north: dict, south: dict) -> None:
    assert north["houses"][0]["aspects"] == ["Sa"]  # <u>Sa</u>
    assert south["houses"][1]["aspects"] == ["Ju", "Sa"]  # bare text in the div


def test_russian_chart_parses_with_codes_intact() -> None:
    chart_ru = load("show-chart-ru-d1-north.html")
    assert chart_ru["style"] == "north"
    assert chart_ru["houses"][3]["sign"]["code"] == "Cn"
    assert chart_ru["houses"][3]["sign"]["name"] == "Рак"  # label follows the site
    assert placement(chart_ru, "Su")["house"] == 4


def test_agrees_with_show_info_on_the_same_chart(north: dict) -> None:
    """The drawing and the table are two views of one calculation."""
    info = parse_show_info((FIXTURES / "show-info-en.html").read_text(encoding="utf-8"))
    for row in info["planets"]:
        placed = placement(north, row["code"])
        assert placed["sign"] == row["rasi"]["code"]
        assert placed["house"] == (row["house"] or 1)
        assert placed["retrograde"] == row["retrograde"]
        # The drawing truncates to whole degrees.
        assert placed["degree"] == int(row["degrees_decimal"])


def test_d9_chart_agrees_with_show_info_d9(south: dict) -> None:
    """Houses match, and so do the D9 signs — but not via the rasi column.

    In a show-info for a varga other than D1 the rasi column keeps showing the
    natal D1 sign; the sign of the varga is only in the chart. For D9 the
    navamsa column happens to name it too, which is what this checks.
    """
    info = parse_show_info((FIXTURES / "show-info-en-d9.html").read_text(encoding="utf-8"))
    for row in info["planets"]:
        placed = placement(south, row["code"])
        assert placed["house"] == (row["house"] or 1)
        assert placed["sign"] != row["rasi"]["code"] or row["navamsa"] == row["rasi"]["name"]
        assert row["navamsa"] == next(
            house["sign"]["name"]
            for house in south["houses"]
            if house["sign"]["code"] == placed["sign"]
        )


def test_rejects_a_response_that_is_not_a_chart() -> None:
    with pytest.raises(ValueError, match="no chart found"):
        parse_show_chart("<html><body>Access Denied</body></html>")


def test_result_is_json_serialisable(north: dict) -> None:
    assert json.loads(json.dumps(north)) == north
