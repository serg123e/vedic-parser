"""Command line front end.

    python -m vedic_parser session
    python -m vedic_parser show-info --name Ss --date 07.08.1983 --time 23:00:00 \
        --latitude 55.45 --longitude 37.37 --timezone +4
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from . import api
from .chart import Chart
from .parsers import (
    parse_show_avasthas,
    parse_show_bala,
    parse_show_chart,
    parse_show_dasha,
    parse_show_info,
    parse_show_other,
    parse_show_yogas,
)
from .session import BASE_BY_LANG, Session, VedicHoroError


def _add_chart_args(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("birth data")
    group.add_argument("--name", required=True, help="name or event label")
    group.add_argument("--date", required=True, metavar="DD.MM.YYYY")
    group.add_argument("--time", required=True, metavar="HH:MM:SS")
    group.add_argument(
        "--latitude", required=True, metavar="DEG.MIN", help="e.g. 55.45 (negative for South)"
    )
    group.add_argument(
        "--longitude", required=True, metavar="DEG.MIN", help="e.g. 37.37 (negative for West)"
    )
    group.add_argument("--timezone", required=True, metavar="HOURS", help="e.g. +4")


def _chart(args: argparse.Namespace) -> Chart:
    return Chart(
        name=args.name,
        date=args.date,
        time=args.time,
        timezone=args.timezone,
        latitude=args.latitude,
        longitude=args.longitude,
    )


def _add_common_args(parser: argparse.ArgumentParser, *, suppress: bool = False) -> None:
    """Options accepted both before and after the subcommand.

    On the subparsers the defaults are suppressed, so a value given before the
    subcommand is not overwritten by a default afterwards.
    """

    def default(value: Any) -> Any:
        return argparse.SUPPRESS if suppress else value

    parser.add_argument(
        "--lang",
        default=default("en"),
        choices=sorted(BASE_BY_LANG),
        help="en -> vedic-horo.com, ru -> vedic-horo.ru (default: en)",
    )
    parser.add_argument("--base-url", default=default(None), help="override the domain entirely")
    parser.add_argument(
        "--indent", type=int, default=default(2), help="JSON indent (0 for one line)"
    )
    credentials = parser.add_argument_group(
        "browser credentials",
        "Skip the bootstrap request and reuse a session from a browser; both "
        "values come from the same page load. Needed when a domain answers "
        "with its JavaScript gate.",
    )
    credentials.add_argument(
        "--session-id", default=default(None), help="the PHPSESSID cookie value"
    )
    credentials.add_argument(
        "--token", default=default(None), help="the token_security value from the page source"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vedic_parser", description="Query vedic-horo and parse the results."
    )
    _add_common_args(parser)

    sub = parser.add_subparsers(dest="command", required=True)

    session_cmd = sub.add_parser("session", help="open a session and show the credentials")
    _add_common_args(session_cmd, suppress=True)
    session_cmd.set_defaults(handler=_cmd_session)

    info_cmd = sub.add_parser(
        "show-info", help="planets table and Ashtakavarga for one divisional chart"
    )
    _add_common_args(info_cmd, suppress=True)
    _add_chart_args(info_cmd)
    info_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    info_cmd.add_argument(
        "--from",
        dest="from_",
        default="",
        choices=["", "1", "2", "AL"],
        help="reckon from: 1 Sun, 2 Moon, AL Arudha Lagna (default: Ascendant)",
    )
    info_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    info_cmd.set_defaults(handler=_cmd_show_info)

    chart_cmd = sub.add_parser(
        "show-chart", help="one divisional chart: the twelve houses with their contents"
    )
    _add_common_args(chart_cmd, suppress=True)
    _add_chart_args(chart_cmd)
    chart_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    chart_cmd.add_argument(
        "--style",
        default="North",
        choices=["North", "South"],
        help="chart style to request; both parse to the same shape (default: North)",
    )
    chart_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    chart_cmd.set_defaults(handler=_cmd_show_chart)

    other_cmd = sub.add_parser(
        "show-other", help="special lagnas, panchanga, upagrahas, points and chakras"
    )
    _add_common_args(other_cmd, suppress=True)
    _add_chart_args(other_cmd)
    other_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    other_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    other_cmd.set_defaults(handler=_cmd_show_other)

    dasha_cmd = sub.add_parser("show-dasha", help="one dasha table with exact boundaries")
    _add_common_args(dasha_cmd, suppress=True)
    _add_chart_args(dasha_cmd)
    dasha_cmd.add_argument(
        "--dasha", default="vimshottari", choices=api.DASHAS, help="dasha system"
    )
    dasha_cmd.add_argument(
        "--level", type=int, default=2, choices=[1, 2, 3, 4],
        help="1 maha, 2 antar, 3 pratyantar, 4 sookshma (default: 2)",
    )
    dasha_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    dasha_cmd.add_argument(
        "--current", metavar="D.M.YYYY H:M", help="which stretch to return (default: now)"
    )
    dasha_cmd.add_argument("--cycle", type=int, default=0, help="step whole cycles (default: 0)")
    dasha_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    dasha_cmd.set_defaults(handler=_cmd_show_dasha)

    bala_cmd = sub.add_parser(
        "show-bala", help="Shad Bala, varga strengths and the aspect matrices"
    )
    _add_common_args(bala_cmd, suppress=True)
    _add_chart_args(bala_cmd)
    bala_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    bala_cmd.add_argument(
        "--shad-bala-only",
        action="store_true",
        help="request show-shad-bala instead: the Shad Bala table alone",
    )
    bala_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    bala_cmd.set_defaults(handler=_cmd_show_bala)

    yogas_cmd = sub.add_parser("show-yogas", help="the yogas the chart forms")
    _add_common_args(yogas_cmd, suppress=True)
    _add_chart_args(yogas_cmd)
    yogas_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    yogas_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    yogas_cmd.set_defaults(handler=_cmd_show_yogas)

    avasthas_cmd = sub.add_parser("show-avasthas", help="the states of the planets")
    _add_common_args(avasthas_cmd, suppress=True)
    _add_chart_args(avasthas_cmd)
    avasthas_cmd.add_argument("--divisional", default="D1", help="varga code, D1…D60 (default: D1)")
    avasthas_cmd.add_argument("--html", metavar="FILE", help="parse a saved response instead of fetching")
    avasthas_cmd.set_defaults(handler=_cmd_show_avasthas)

    return parser


def _cmd_session(args: argparse.Namespace) -> dict[str, Any]:
    session = _open_session(args)
    return {
        "base_url": session.base_url,
        "session_id": session.session_id,
        "token_security": session.token,
    }


def _cmd_show_info(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_info(handle.read())
    return api.show_info(
        _open_session(args), _chart(args), divisional=args.divisional, from_=args.from_
    )


def _cmd_show_chart(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_chart(handle.read())
    return api.show_chart(
        _open_session(args), _chart(args), divisional=args.divisional, style=args.style
    )


def _cmd_show_other(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_other(handle.read())
    return api.show_other(_open_session(args), _chart(args), divisional=args.divisional)


def _cmd_show_dasha(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_dasha(handle.read())
    return api.show_dasha(
        _open_session(args),
        _chart(args),
        dasha=args.dasha,
        level=args.level,
        divisional=args.divisional,
        cycle=args.cycle,
        current=args.current,
    )


def _cmd_show_bala(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_bala(handle.read())
    return api.show_bala(
        _open_session(args),
        _chart(args),
        divisional=args.divisional,
        full=not args.shad_bala_only,
    )


def _cmd_show_yogas(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_yogas(handle.read())
    return api.show_yogas(_open_session(args), _chart(args), divisional=args.divisional)


def _cmd_show_avasthas(args: argparse.Namespace) -> dict[str, Any]:
    if args.html:
        with open(args.html, encoding="utf-8") as handle:
            return parse_show_avasthas(handle.read())
    return api.show_avasthas(_open_session(args), _chart(args), divisional=args.divisional)


def _open_session(args: argparse.Namespace) -> Session:
    session = Session(lang=args.lang, base_url=args.base_url)
    if bool(args.session_id) != bool(args.token):
        raise SystemExit("error: --session-id and --token must be given together")
    if args.session_id:
        session.adopt(args.session_id, args.token)
    else:
        session.open()
    return session


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.handler(args)
    except VedicHoroError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    try:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=args.indent or None)
        sys.stdout.write("\n")
    except BrokenPipeError:  # piped into head and friends
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
