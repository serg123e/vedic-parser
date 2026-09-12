"""get-aspects and get-argala parser tests.

These two endpoints answer with plain text, so the fixtures are the strings
themselves, recorded from vedic-horo.com for
Ss, 07.08.1983 23:00:00, +4, 55.45 N 37.37 E.
"""

from __future__ import annotations

import json

import pytest

from vedic_parser import parse_get_argala, parse_get_aspects, parse_show_chart
from vedic_parser.parsers.effects import ARGALA_LAYOUT

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

# Recorded answers: sign -> response.
ASPECTS = {1: "Sa|5 8 11", 5: "|1 7 10", 3: "|6 9 12", 4: "Ju Sa|2 8 11"}
ARGALA_1 = {
    1: "2 12 4 10 11 3",
    5: "6 4 8 2 3 7",
    9: "8 10 6 12 11 7",
    12: "1 11 3 9 10 2",
}
ARGALA_2 = {1: "5 9 8 6 3", 5: "9 1 12 10 7", 9: "5 1 2 4", 12: "4 8 7 5"}


def test_aspects_split_planets_from_signs() -> None:
    assert parse_get_aspects("Sa|5 8 11") == {"planets": ["Sa"], "signs": [5, 8, 11]}
    assert parse_get_aspects("Ju Sa|2 8 11") == {"planets": ["Ju", "Sa"], "signs": [2, 8, 11]}


def test_a_sign_nothing_aspects_has_an_empty_first_half() -> None:
    assert parse_get_aspects("|1 7 10") == {"planets": [], "signs": [1, 7, 10]}


def test_aspected_signs_follow_rasi_drishti() -> None:
    """A movable sign aspects the fixed ones bar the adjacent, and so on."""
    movable, fixed, dual = {1, 4, 7, 10}, {2, 5, 8, 11}, {3, 6, 9, 12}
    for sign, answer in ASPECTS.items():
        signs = set(parse_get_aspects(answer)["signs"])
        if sign in movable:
            expected = fixed - {sign % 12 + 1}  # all but the next sign along
        elif sign in fixed:
            expected = movable - {sign - 1 or 12}
        else:
            expected = dual - {sign}
        assert signs == expected, (sign, signs, expected)


def test_aspecting_planets_match_the_chart() -> None:
    """The planets half repeats what the chart shows against that house."""
    chart = parse_show_chart(
        (FIXTURES / "show-chart-en-d1-north.html").read_text(encoding="utf-8")
    )
    for house in chart["houses"]:
        answer = ASPECTS.get(house["sign"]["number"])
        if answer is None:
            continue
        assert parse_get_aspects(answer)["planets"] == house["aspects"]


def test_argala_groups_follow_the_sites_own_colouring() -> None:
    parsed = parse_get_argala("2 12 4 10 11 3", type=1)
    assert parsed == {
        "type": 1,
        "signs": [2, 12, 4, 10, 11, 3],
        "argala": [2, 4, 11],
        "virodha": [12, 10, 3],
        "special": [],
    }


def test_type_two_has_its_own_layout_and_an_extra_position() -> None:
    parsed = parse_get_argala("5 9 8 6 3", type=2)
    assert parsed["argala"] == [5, 8]
    assert parsed["virodha"] == [9, 6]
    assert parsed["special"] == [3]


def test_a_short_answer_does_not_invent_positions() -> None:
    """Type 2 sometimes comes back with four numbers instead of five."""
    parsed = parse_get_argala("5 1 2 4", type=2)
    assert parsed["signs"] == [5, 1, 2, 4]
    assert parsed["argala"] == [5, 2]
    assert parsed["virodha"] == [1, 4]
    assert parsed["special"] == []


def test_numbers_are_absolute_signs_not_relative_positions() -> None:
    """From Aries the 2nd is Taurus; from Leo it is Virgo, not Taurus again."""
    assert parse_get_argala(ARGALA_1[1], type=1)["argala"] == [2, 4, 11]
    assert parse_get_argala(ARGALA_1[5], type=1)["argala"] == [6, 8, 3]
    assert parse_get_argala(ARGALA_1[12], type=1)["argala"] == [1, 3, 10]
    for answer in ARGALA_1.values():
        assert all(1 <= sign <= 12 for sign in parse_get_argala(answer)["signs"])


def positions(sign: int, offsets: tuple[int, ...]) -> list[int]:
    return [(sign + offset - 1) % 12 + 1 for offset in offsets]


ARGALA_OFFSETS = (1, 3, 10)  # the 2nd, 4th and 11th from the sign
VIRODHA_OFFSETS = (11, 9, 2)  # the 12th, 10th and 3rd, which obstruct them
KETU_SIGN = 9  # where Ketu sits in this chart


def test_primary_argala_sits_in_the_classic_places() -> None:
    for sign, answer in ARGALA_1.items():
        if sign == KETU_SIGN:
            continue
        parsed = parse_get_argala(answer, type=1)
        assert parsed["argala"] == positions(sign, ARGALA_OFFSETS)
        assert parsed["virodha"] == positions(sign, VIRODHA_OFFSETS)


def test_the_ketu_sign_comes_back_with_the_groups_swapped() -> None:
    """A real quirk, not a parsing artefact.

    Over all twelve signs of two charts exactly one sign per chart had argala
    and virodha the other way round, and both times it was the sign Ketu
    occupied — Rahu's did not. The parser reports the site's grouping as given
    rather than "correcting" it.
    """
    parsed = parse_get_argala(ARGALA_1[KETU_SIGN], type=1)
    assert parsed["argala"] == positions(KETU_SIGN, VIRODHA_OFFSETS)
    assert parsed["virodha"] == positions(KETU_SIGN, ARGALA_OFFSETS)


def test_the_six_positions_are_the_classic_ones_whatever_the_grouping() -> None:
    for sign, answer in ARGALA_1.items():
        parsed = parse_get_argala(answer, type=1)
        assert set(parsed["signs"]) == set(
            positions(sign, ARGALA_OFFSETS) + positions(sign, VIRODHA_OFFSETS)
        )


def test_every_type_has_a_layout() -> None:
    assert set(ARGALA_LAYOUT) == {1, 2}
    for layout in ARGALA_LAYOUT.values():
        assert set(layout) == {"argala", "virodha", "special"}


def test_empty_answers_are_empty_results() -> None:
    assert parse_get_aspects("") == {"planets": [], "signs": []}
    assert parse_get_argala("")["signs"] == []


def test_results_are_json_serialisable() -> None:
    for answer in ASPECTS.values():
        parsed = parse_get_aspects(answer)
        assert json.loads(json.dumps(parsed)) == parsed
    for answer in ARGALA_2.values():
        parsed = parse_get_argala(answer, type=2)
        assert json.loads(json.dumps(parsed)) == parsed


@pytest.mark.parametrize("sign", sorted(ARGALA_1))
def test_argala_and_virodha_never_overlap(sign: int) -> None:
    parsed = parse_get_argala(ARGALA_1[sign], type=1)
    assert not set(parsed["argala"]) & set(parsed["virodha"])
