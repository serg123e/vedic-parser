"""Session tests. No network: the requests session is replaced by a stub."""

from __future__ import annotations

from pathlib import Path

import pytest

from vedic_parser import AccessDenied, Chart, Session, TokenNotFound, api
from vedic_parser.session import BASE_EN, BASE_RU

FIXTURES = Path(__file__).parent / "fixtures"

TOKEN = "f6907666d62c7b64b6ac89e5ce152ab1fb4822de3ec3f1f5816b38610621d8b8"
HOME_PAGE = f'<html><script>var token_security = "{TOKEN}";</script></html>'

CHART = Chart(
    name="Ss",
    date="07.08.1983",
    time="23:00:00",
    timezone="+4",
    latitude="55.45",
    longitude="37.37",
)


class FakeResponse:
    def __init__(self, status_code: int = 200, text: str = "", headers: dict | None = None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected raise_for_status on {self.status_code}")


class FakeHttp:
    """Stands in for requests.Session, recording calls and replaying answers."""

    def __init__(self, page: str = HOME_PAGE, post_responses: list[FakeResponse] | None = None):
        self.page = page
        self.post_responses = post_responses or []
        self.gets: list[str] = []
        self.posts: list[tuple[str, dict]] = []
        self.cookies: dict[str, str] = {}

    def get(self, url: str, **_kwargs) -> FakeResponse:
        self.gets.append(url)
        self.cookies["PHPSESSID"] = f"session{len(self.gets)}"
        return FakeResponse(text=self.page)

    def post(self, url: str, data: dict, **_kwargs) -> FakeResponse:
        self.posts.append((url, data))
        if self.post_responses:
            return self.post_responses.pop(0)
        return FakeResponse(text="<table class='chart-info'></table>")


def test_lang_picks_the_domain() -> None:
    assert Session(lang="en").base_url == BASE_EN
    assert Session(lang="ru").base_url == BASE_RU
    with pytest.raises(ValueError):
        Session(lang="de")


def test_base_url_override_wins_and_loses_its_trailing_slash() -> None:
    assert Session(base_url="https://example.test/").base_url == "https://example.test"


def test_open_picks_up_the_token_and_the_cookie() -> None:
    http = FakeHttp()
    session = Session(http=http)
    assert not session.is_open

    assert session.open() == TOKEN
    assert http.gets == [f"{BASE_EN}/"]
    assert session.token == TOKEN
    assert session.session_id == "session1"
    assert session.is_open


def test_open_complains_when_the_page_has_no_token() -> None:
    session = Session(http=FakeHttp(page="<html>nothing here</html>"))
    with pytest.raises(TokenNotFound):
        session.open()


def test_action_opens_the_session_lazily_and_sends_the_pair() -> None:
    http = FakeHttp()
    session = Session(http=http)

    session.action("show-info", CHART, divisional="D9", **{"from": ""})

    assert http.gets == [f"{BASE_EN}/"]  # bootstrapped on first use
    url, payload = http.posts[0]
    assert url == f"{BASE_EN}/actions.php"
    assert payload == {
        "action": "show-info",
        "data": (
            "name=Ss|date=07.08.1983|time=23:00:00|timezone=+4"
            "|latitude=55.45|longitude=37.37"
        ),
        "divisional": "D9",
        "from": "",
        "token_security": TOKEN,
    }


def test_action_without_chart_omits_the_data_parameter() -> None:
    http = FakeHttp()
    Session(http=http).action("show-current-periods")
    assert "data" not in http.posts[0][1]


def test_expired_token_is_refreshed_once() -> None:
    http = FakeHttp(
        post_responses=[FakeResponse(status_code=419), FakeResponse(text="<html>ok</html>")]
    )
    session = Session(http=http)

    assert session.action("show-info", CHART) == "<html>ok</html>"
    assert len(http.gets) == 2  # reopened after the 419
    assert len(http.posts) == 2


def test_paid_action_raises_access_denied() -> None:
    http = FakeHttp(post_responses=[FakeResponse(status_code=403, text="Access Denied")])
    with pytest.raises(AccessDenied, match="show-transits"):
        Session(http=http).action("show-transits", CHART)


def test_challenged_page_is_reported_clearly() -> None:
    class ChallengedHttp(FakeHttp):
        def get(self, url: str, **_kwargs) -> FakeResponse:
            return FakeResponse(
                status_code=403, text="Just a moment...", headers={"cf-mitigated": "challenge"}
            )

    session = Session(http=ChallengedHttp())
    with pytest.raises(Exception, match="Cloudflare"):
        session.open("/analyse.php")


def test_show_info_records_the_requested_varga() -> None:
    html = (FIXTURES / "show-info-ru-d9.html").read_text(encoding="utf-8")
    http = FakeHttp(post_responses=[FakeResponse(text=html)])

    info = api.show_info(Session(lang="ru", http=http), CHART, divisional="D9")

    assert info["divisional"] == "D9"  # not the "D1" the markup claims
    assert info["from"] is None
    assert len(info["planets"]) == 10
    assert http.posts[0][1]["divisional"] == "D9"


def test_show_info_passes_from_through() -> None:
    http = FakeHttp(
        post_responses=[
            FakeResponse(text=(FIXTURES / "show-info-en.html").read_text(encoding="utf-8"))
        ]
    )
    info = api.show_info(Session(http=http), CHART, divisional="D1", from_="2")

    assert http.posts[0][1]["from"] == "2"
    assert info["from"] == "2"


JS_GATE = (
    '<html><body><script>document.cookie = "__jua_=" + '
    "fixedEncodeURIComponent(navigator.userAgent);</script></body></html>"
)


def test_js_gate_is_reported_as_such() -> None:
    from vedic_parser import BootstrapBlocked

    session = Session(lang="ru", http=FakeHttp(page=JS_GATE))
    with pytest.raises(BootstrapBlocked, match="JavaScript gate"):
        session.open()


def test_adopted_credentials_skip_the_bootstrap() -> None:
    http = FakeHttp(page=JS_GATE)  # would fail if it were fetched
    session = Session(lang="ru", http=http)

    session.adopt("browser-session", "browser-token")
    session.action("show-current-periods")

    assert http.gets == []
    assert session.session_id == "browser-session"
    assert http.posts[0][1]["token_security"] == "browser-token"


def test_adopted_credentials_are_not_silently_refreshed() -> None:
    http = FakeHttp(page=JS_GATE, post_responses=[FakeResponse(status_code=419)])
    session = Session(lang="ru", http=http)
    session.adopt("browser-session", "browser-token")

    with pytest.raises(Exception, match="adopt a fresh"):
        session.action("show-info", CHART)
    assert http.gets == []
