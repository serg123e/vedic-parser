"""Parsers for the HTML fragments actions.php returns."""

from .show_chart import parse_show_chart
from .show_info import parse_show_info

__all__ = ["parse_show_chart", "parse_show_info"]
