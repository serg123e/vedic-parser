"""show-dasha parser tests.

* show-dasha-en-vimshottari-l1.html   level 1, .com
* show-dasha-en-vimshottari-l2.html   level 2, .com
* show-dasha-en-chara-l2.html         chara dasha (sign based), level 2, .com
* show-dasha-ru-vimshottari-l2.html   the same level 2 table from a .ru page
* show-dasha-ru-chara-l2.html         the same chara table from a .ru page
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from vedic_parser import parse_show_dasha

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return parse_show_dasha((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def maha() -> dict:
    return load("show-dasha-en-vimshottari-l1.html")


@pytest.fixture(scope="module")
def antar() -> dict:
    return load("show-dasha-en-vimshottari-l2.html")


def test_level_and_kind_are_read_from_the_rows(maha: dict, antar: dict) -> None:
    assert (maha["kind"], maha["level"]) == ("planet", 1)
    assert (antar["kind"], antar["level"]) == ("planet", 2)
    assert len(maha["periods"]) == 9  # the nine vimshottari lords
    assert len(antar["periods"]) == 81  # nine antars in each


def test_boundaries_come_from_the_row_attributes(maha: dict) -> None:
    first = maha["periods"][0]
    assert first["start"] == "1978-11-23T16:25"
    assert first["end"] == "1997-11-23T13:21"
    assert first["lords"] == ["Sa"]
    assert first["labels"] == ["Saturn"]
    # The visible date is kept as a label only.
    assert first["start_label"] == "23 Nov 1978"
    assert first["start_time"] == "16:25"


def test_periods_are_contiguous_and_ordered(maha: dict, antar: dict) -> None:
    """Each period ends where the next begins — give or take the site's rounding.

    The boundaries come as HH:MM, and at a few maha seams the two sides round
    apart by a minute (the last Saturn antar ends 13:20, the Mercury maha
    starts 13:21). That is the site's data, not a parsing artefact, so callers
    must not assume exact contiguity.
    """
    for dasha in (maha, antar):
        for earlier, later in zip(dasha["periods"], dasha["periods"][1:]):
            seam = datetime.fromisoformat(later["start"]) - datetime.fromisoformat(earlier["end"])
            assert abs(seam) <= timedelta(minutes=1)
        starts = [period["start"] for period in dasha["periods"]]
        assert starts == sorted(starts)


def test_antar_periods_nest_inside_their_maha(maha: dict, antar: dict) -> None:
    for parent in maha["periods"]:
        children = [p for p in antar["periods"] if p["lords"][0] == parent["lords"][0]]
        assert len(children) == 9
        assert children[0]["start"] == parent["start"]
        # The closing seam can round a minute apart, as above.
        drift = datetime.fromisoformat(parent["end"]) - datetime.fromisoformat(children[-1]["end"])
        assert abs(drift) <= timedelta(minutes=1)


def test_age_is_a_number_or_none_before_birth(maha: dict) -> None:
    # The first maha dasha starts before the 1983 birth date.
    assert maha["periods"][0]["age"] is None
    assert maha["periods"][1]["age"] == 14
    ages = [period["age"] for period in maha["periods"] if period["age"] is not None]
    assert ages == sorted(ages)


def test_sign_dasha_has_names_but_no_codes() -> None:
    chara = load("show-dasha-en-chara-l2.html")
    assert chara["kind"] == "sign"
    assert chara["level"] == 2
    first = chara["periods"][0]
    assert first["labels"] == ["Aries", "Taurus"]
    assert first["lords"] == []  # signs are plain text, with no code to read
    assert first["start"] == "1983-08-07T23:00"  # a chara dasha starts at birth


def test_russian_rows_give_identical_data() -> None:
    for name_en, name_ru in [
        ("show-dasha-en-vimshottari-l2.html", "show-dasha-ru-vimshottari-l2.html"),
        ("show-dasha-en-chara-l2.html", "show-dasha-ru-chara-l2.html"),
    ]:
        en, ru = load(name_en), load(name_ru)
        assert en["kind"] == ru["kind"]
        assert len(en["periods"]) == len(ru["periods"])
        for period_en, period_ru in zip(en["periods"], ru["periods"]):
            assert period_en["start"] == period_ru["start"]
            assert period_en["end"] == period_ru["end"]
            assert period_en["lords"] == period_ru["lords"]
            assert period_en["age"] == period_ru["age"]
            # Only the rendered text differs.
            assert period_en["labels"] != period_ru["labels"] or not period_en["labels"]


def test_boundaries_parse_as_datetimes(antar: dict) -> None:
    for period in antar["periods"]:
        assert datetime.fromisoformat(period["start"]) < datetime.fromisoformat(period["end"])


def test_rejects_a_response_that_is_not_a_dasha_table() -> None:
    with pytest.raises(ValueError, match="no table found"):
        parse_show_dasha("<div>Access Denied</div>")


def test_an_empty_table_is_not_an_error() -> None:
    """The site answers show-dasha with an empty table when parameters are missing."""
    empty = parse_show_dasha('<table class="table"></table>')
    assert empty == {"kind": "sign", "level": 0, "periods": []}


def test_result_is_json_serialisable(maha: dict) -> None:
    assert json.loads(json.dumps(maha)) == maha
