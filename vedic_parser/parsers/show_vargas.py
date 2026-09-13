"""Parser for the `show-vargas` fragment: several divisional charts at once.

The endpoint takes a list of vargas and answers with one ``div.chart-block``
per varga, each holding an ordinary chart — so each block is handed to
:func:`~vedic_parser.parsers.show_chart.parse_show_chart` and the styles can
differ from block to block.

Unlike ``show-info``, the varga selector inside each block really is the varga
of that block, so it can be trusted here.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from ._html import selected_option
from .show_chart import parse_show_chart


def parse_show_vargas(html: str) -> dict[str, Any]:
    """Parse a `show-vargas` response into plain data.

    Returns ``{"charts": [...]}`` in the order the site drew them, each entry
    in the shape :func:`parse_show_chart` produces plus its own ``divisional``.
    """
    soup = BeautifulSoup(html, "lxml")
    blocks = soup.select("div.chart-block")
    if not blocks:
        raise ValueError("no div.chart-block found; is this a show-vargas response?")

    charts = []
    for block in blocks:
        chart = parse_show_chart(str(block))
        chart["divisional"] = selected_option(block.select_one("select.divisional"))
        charts.append(chart)
    return {"charts": charts}
