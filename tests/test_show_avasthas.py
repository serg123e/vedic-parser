"""show-avasthas parser tests.

* show-avasthas-en-d1.html   actions.php show-avasthas, D1, .com
* show-avasthas-ru-d1.html   the same request against .ru
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vedic_parser import parse_show_avasthas

FIXTURES = Path(__file__).parent / "fixtures"

PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"]


def load(name: str) -> dict:
    return parse_show_avasthas((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def avasthas() -> dict:
    return load("show-avasthas-en-d1.html")


def by_code(parsed: dict, code: str) -> dict:
    return next(planet for planet in parsed["planets"] if planet["code"] == code)


def test_every_planet_is_covered(avasthas: dict) -> None:
    """The nodes are included here, so nine rows rather than seven."""
    assert [planet["code"] for planet in avasthas["planets"]] == PLANETS
    assert all(planet["name"] for planet in avasthas["planets"])


def test_baladi_and_jagradadi(avasthas: dict) -> None:
    sun = by_code(avasthas, "Su")
    assert sun["baladi"] == {"state": "Young", "strength_percent": 50, "tone": "orange"}
    assert sun["jagradadi"] == {"state": "Dreaming", "strength_percent": 50, "tone": "orange"}
    moon = by_code(avasthas, "Mo")
    assert moon["baladi"] == {"state": "Old", "strength_percent": 15, "tone": "red"}
    assert moon["jagradadi"] == {"state": "Awake", "strength_percent": 100, "tone": "green"}


def test_tone_tracks_the_strength(avasthas: dict) -> None:
    """100% is green, 50% orange, anything lower red — across every state."""
    expected = {100: "green", 50: "orange", 25: "red", 15: "red", 0: "red"}
    for planet in avasthas["planets"]:
        for state in (planet["baladi"], planet["jagradadi"]):
            assert state["tone"] == expected[state["strength_percent"]]
        for group in planet["shayanadi"]["by_letter_group"]:
            assert group["tone"] == expected[group["strength_percent"]]


def test_moods_pair_each_state_with_its_reason(avasthas: dict) -> None:
    sun = by_code(avasthas, "Su")
    assert len(sun["deeptadi"]) == 5
    assert sun["deeptadi"][0] == {
        "state": "Relaxed, inspired, open and supported",
        "tone": "green",
        "reason": "Benefic influence: Ju",
        "planets": ["Ju"],
        "signs": [],
    }
    # Codes are pulled out of the reason text; signs appear there too.
    friend = next(m for m in sun["deeptadi"] if "Friend sign" in (m["reason"] or ""))
    assert friend["signs"] == ["Cn"]
    assert friend["planets"] == ["Mo", "Ma", "Ju"]
    assert all(mood["tone"] in ("green", "red", "orange") for mood in sun["deeptadi"])


def test_shayanadi_state_and_syllable_groups(avasthas: dict) -> None:
    """Strength depends on the name's first syllable, so all five groups come."""
    sun = by_code(avasthas, "Su")["shayanadi"]
    assert sun["state"] == "Gaining"
    assert sun["tone"] == "red"
    assert "Problems from enemies" in sun["effect"]

    groups = sun["by_letter_group"]
    assert len(groups) == 5
    assert groups[0]["letters"] == ["a", "bh", "chh", "d`", "dh``", "k", "v"]
    assert [group["strength_percent"] for group in groups] == [50, 100, 15, 50, 100]


def test_legend_covers_every_planet_once(avasthas: dict) -> None:
    legend = avasthas["shayanadi_legend"]
    assert [entry["state"] for entry in legend] == [
        "Resting", "Seated", "Gaining", "Eating", "Aspiring",
    ]
    # The bracketed number is how many planets are in that state.
    assert sum(entry["count"] for entry in legend) == len(avasthas["planets"])
    counted = {entry["state"]: entry["count"] for entry in legend}
    for state, count in counted.items():
        assert sum(
            1 for planet in avasthas["planets"] if planet["shayanadi"]["state"] == state
        ) == count
    assert all(entry["description"] for entry in legend)


def test_note_is_kept(avasthas: dict) -> None:
    assert "first syllable of the name" in avasthas["shayanadi_note"]


def test_russian_response_agrees_on_everything_but_wording() -> None:
    en, ru = load("show-avasthas-en-d1.html"), load("show-avasthas-ru-d1.html")
    assert [p["code"] for p in ru["planets"]] == PLANETS
    for planet_en, planet_ru in zip(en["planets"], ru["planets"]):
        for key in ("baladi", "jagradadi"):
            assert planet_en[key]["strength_percent"] == planet_ru[key]["strength_percent"]
            assert planet_en[key]["tone"] == planet_ru[key]["tone"]
            assert planet_en[key]["state"] != planet_ru[key]["state"]
        # Syllable groups are transliteration, latin in both languages.
        assert [g["letters"] for g in planet_en["shayanadi"]["by_letter_group"]] == [
            g["letters"] for g in planet_ru["shayanadi"]["by_letter_group"]
        ]
        for mood_en, mood_ru in zip(planet_en["deeptadi"], planet_ru["deeptadi"]):
            assert mood_en["planets"] == mood_ru["planets"]
            assert mood_en["signs"] == mood_ru["signs"]
    assert [e["count"] for e in en["shayanadi_legend"]] == [
        e["count"] for e in ru["shayanadi_legend"]
    ]


def test_rejects_a_response_that_is_not_avasthas() -> None:
    with pytest.raises(ValueError, match="no table.chart-info"):
        parse_show_avasthas("<div>Access Denied</div>")


def test_result_is_json_serialisable(avasthas: dict) -> None:
    assert json.loads(json.dumps(avasthas)) == avasthas
