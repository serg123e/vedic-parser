"""Parsers for the fragments actions.php returns."""

from .effects import parse_get_argala, parse_get_aspects
from .show_avasthas import parse_show_avasthas
from .show_bala import parse_show_bala
from .show_bhava import parse_show_bhava
from .show_chart import parse_show_chart
from .show_dasha import parse_show_dasha
from .show_info import parse_show_info
from .show_other import parse_show_other
from .show_sade_sati import parse_show_sade_sati
from .show_yogas import parse_show_yogas

__all__ = [
    "parse_get_argala",
    "parse_get_aspects",
    "parse_show_avasthas",
    "parse_show_bala",
    "parse_show_bhava",
    "parse_show_chart",
    "parse_show_dasha",
    "parse_show_info",
    "parse_show_other",
    "parse_show_sade_sati",
    "parse_show_yogas",
]
