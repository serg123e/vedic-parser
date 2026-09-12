"""show-sade-sati parser tests.

* show-sade-sati-en.html   actions.php show-sade-sati, .com
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_sade_sati

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def sade_sati() -> dict:
    return parse_show_sade_sati(
        (FIXTURES / "show-sade-sati-en.html").read_text(encoding="utf-8")
    )


def test_both_methods_with_four_occurrences_each(sade_sati: dict) -> None:
    assert [method["title"] for method in sade_sati["methods"]] == [
        "Sade Sati (traditional)",
        "Sade Sati (Shri H.N. Katwe)",
    ]
    for method in sade_sati["methods"]:
        assert [period["title"] for period in method["periods"]] == [
            "FIRST SADE SATI", "SECOND SADE SATI", "THIRD SADE SATI", "FOURTH SADE SATI",
        ]


def test_first_occurrence(sade_sati: dict) -> None:
    first = sade_sati["methods"][0]["periods"][0]
    assert first["start"] == "2003-04-08T00:00"
    assert first["end"] == "2009-09-10T00:00"
    assert first["segments"][1] == {
        "start": "2003-04-08T00:00",
        "end": "2004-09-06T00:00",
        "description": "Saturn in 12th in Gemini",
        "house": 12,
        "within_main": True,
    }


def test_the_swallowed_first_phase_is_still_found(sade_sati: dict) -> None:
    """The site leaves a style attribute unterminated, eating one <u> wrapper.

    Segments are therefore walked from the date spans; if that regressed, the
    first phase of the main span would be missing and the coverage test below
    would fail too.
    """
    first = sade_sati["methods"][0]["periods"][0]
    inside = [segment for segment in first["segments"] if segment["within_main"]]
    assert len(inside) == 7
    assert inside[0]["start"] == first["start"]


def test_phases_tile_the_main_span(sade_sati: dict) -> None:
    for method in sade_sati["methods"]:
        for period in method["periods"]:
            inside = [s for s in period["segments"] if s["within_main"]]
            assert inside[0]["start"] == period["start"]
            assert inside[-1]["end"] == period["end"]
            for earlier, later in zip(inside, inside[1:]):
                assert earlier["end"] == later["start"]


def test_segments_outside_the_main_span_stay_outside(sade_sati: dict) -> None:
    """Saturn brushing the sign before or after the continuous period."""
    outside = [
        segment
        for method in sade_sati["methods"]
        for period in method["periods"]
        for segment in period["segments"]
        if not segment["within_main"]
    ]
    assert outside  # this chart has them in every occurrence
    for method in sade_sati["methods"]:
        for period in method["periods"]:
            for segment in period["segments"]:
                if segment["within_main"]:
                    continue
                assert segment["end"] <= period["start"] or segment["start"] >= period["end"]


def test_houses_are_the_ones_sade_sati_is_about(sade_sati: dict) -> None:
    """The 12th, 1st and 2nd from the Moon — plus the 11th in Katwe's method."""
    houses = {
        segment["house"]
        for method in sade_sati["methods"]
        for period in method["periods"]
        for segment in period["segments"]
    }
    assert houses == {11, 12, 1, 2}


def test_dates_come_from_the_data_attributes_not_the_labels(sade_sati: dict) -> None:
    """Every boundary is a full ISO moment, which the rendered "23 Jul 2002" is not."""
    for method in sade_sati["methods"]:
        for period in method["periods"]:
            for segment in period["segments"]:
                assert segment["start"].endswith("T00:00")
                assert segment["start"] < segment["end"]


def test_occurrences_are_chronological(sade_sati: dict) -> None:
    for method in sade_sati["methods"]:
        starts = [period["start"] for period in method["periods"]]
        assert starts == sorted(starts)


def test_an_empty_response_is_not_an_error() -> None:
    assert parse_show_sade_sati("") == {"methods": []}


def test_result_is_json_serialisable(sade_sati: dict) -> None:
    assert json.loads(json.dumps(sade_sati)) == sade_sati
