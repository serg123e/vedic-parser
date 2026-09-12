"""show-bala parser tests.

* show-bala-en-d1.html        actions.php show-bala, D1, .com (all four tables)
* show-shad-bala-ru-d1.html   actions.php show-shad-bala, D1, .ru (one table)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_bala, parse_show_info

FIXTURES = Path(__file__).parent / "fixtures"

PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]


def load(name: str) -> dict:
    return parse_show_bala((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bala() -> dict:
    return load("show-bala-en-d1.html")


def by_code(rows: list[dict], code: str) -> dict:
    return next(row for row in rows if row["code"] == code)


def test_all_four_tables_are_recognised(bala: dict) -> None:
    assert [row["code"] for row in bala["shad_bala"]] == PLANETS
    # The varga table also covers the nodes.
    assert [row["code"] for row in bala["varga_bala"]] == PLANETS + ["Ra", "Ke"]
    assert sorted(bala["aspects"]) == ["on_houses", "on_planets"]


def test_shad_bala_components(bala: dict) -> None:
    sun = by_code(bala["shad_bala"], "Su")["components"]
    assert sun["shad_bala"] == {"percent": 124, "virupas": 485.04, "rupas": 8.08}
    assert sun["sthana_bala"] == {"percent": 120, "virupas": 198.15, "rupas": None}
    assert sun["dig_bala"]["percent"] == 20
    assert sun["kala_bala"]["virupas"] == 164.32
    assert sun["cheshta_bala"]["percent"] == 103
    # These come as a bare number, with no percentage of a minimum.
    assert sun["drik_bala"] == {"percent": None, "virupas": 4.3, "rupas": None}
    assert sun["naisargika_bala"]["virupas"] == 60
    assert sun["ishta_bala"]["virupas"] == 34.44
    assert sun["kashta_bala"]["virupas"] == 25.56
    # Nobody is in a planetary war here, so Yuddha Bala is "-" for everyone.
    assert all(
        row["components"]["yuddha_bala"]["virupas"] is None for row in bala["shad_bala"]
    )


def test_shad_bala_total_matches_its_rupas(bala: dict) -> None:
    """Virupas and rupas are the same number in different units (60 to 1)."""
    for row in bala["shad_bala"]:
        total = row["components"]["shad_bala"]
        assert total["virupas"] / 60 == pytest.approx(total["rupas"], abs=0.01)


def test_shad_bala_percent_agrees_with_show_info(bala: dict) -> None:
    info = parse_show_info((FIXTURES / "show-info-en.html").read_text(encoding="utf-8"))
    for row in info["planets"]:
        if row["shad_bala"] is None:
            continue
        assert by_code(bala["shad_bala"], row["code"])["components"]["shad_bala"]["percent"] == (
            row["shad_bala"]
        )


def test_varga_bala(bala: dict) -> None:
    sun = by_code(bala["varga_bala"], "Su")
    # Keyed by the varga count the site prints in the label, not by its wording.
    assert sorted(sun["vimsopaka"]) == ["dasha", "sapta", "shad", "shodasha"]
    assert sun["vimsopaka"]["shodasha"] == {"percent": 52, "value": 10.33}
    assert sun["vimsopaka"]["shad"] == {"percent": 59, "value": 11.8}
    # Vaiseshikamsa Bala is empty for this chart; Vargottama is a count.
    assert sun["vaiseshikamsa"]["shodasha"] == {"percent": None, "value": None}
    assert sun["vargottama"] == 2


def test_aspect_matrix_shape(bala: dict) -> None:
    on_planets = bala["aspects"]["on_planets"]
    assert on_planets["columns"] == PLANETS + ["Ra", "Ke"]
    assert list(on_planets["rows"]) == PLANETS  # the nodes cast no aspects here
    assert all(len(values) == 9 for values in on_planets["rows"].values())

    on_houses = bala["aspects"]["on_houses"]
    assert on_houses["columns"] == list(range(1, 13))
    assert all(len(values) == 12 for values in on_houses["rows"].values())
    assert on_houses["rows"]["Su"][:2] == [25, 10]


def test_symbol_cells_are_kept_as_symbols(bala: dict) -> None:
    """Where the site prints + or - there is no magnitude to read."""
    row = bala["aspects"]["on_planets"]["rows"]["Su"]
    assert row == ["-", "+", "+", "-", 37, "-", 29, "-", 21]


def test_totals_sum_the_benefic_and_malefic_rows(bala: dict) -> None:
    """The two summary rows are sums, and symbol cells contribute nothing.

    Which planets count as benefic is the chart's own verdict, taken from the
    row colour — and it agrees with the natural beneficence column of
    show-info (a waning Moon is malefic here).
    """
    for matrix in bala["aspects"].values():
        for index, _ in enumerate(matrix["columns"]):
            for nature in ("benefic", "malefic"):
                expected = sum(
                    values[index]
                    for code, values in matrix["rows"].items()
                    if matrix["nature"].get(code) == nature
                    and isinstance(values[index], (int, float))
                )
                assert matrix["totals"][nature][index] == expected


def test_nature_agrees_with_show_info(bala: dict) -> None:
    info = parse_show_info((FIXTURES / "show-info-en.html").read_text(encoding="utf-8"))
    nature = bala["aspects"]["on_planets"]["nature"]
    for row in info["planets"]:
        if row["code"] not in nature:
            continue
        code = row["natural_beneficence"]["code"]
        assert nature[row["code"]] == ("benefic" if code.startswith("B") else "malefic")


def test_shad_bala_only_response_parses_with_the_rest_empty() -> None:
    shad_bala_only = load("show-shad-bala-ru-d1.html")
    assert [row["code"] for row in shad_bala_only["shad_bala"]] == PLANETS
    assert shad_bala_only["varga_bala"] == []
    assert shad_bala_only["aspects"] == {}
    # Same numbers as the English response, Russian labels.
    assert by_code(shad_bala_only["shad_bala"], "Su")["name"] == "Солнце"
    assert by_code(shad_bala_only["shad_bala"], "Su")["components"]["shad_bala"] == {
        "percent": 124,
        "virupas": 485.04,
        "rupas": 8.08,
    }


def test_rejects_a_response_that_is_not_show_bala() -> None:
    with pytest.raises(ValueError, match="no table.chart-info"):
        parse_show_bala("<div>Access Denied</div>")


def test_result_is_json_serialisable(bala: dict) -> None:
    assert json.loads(json.dumps(bala)) == bala
