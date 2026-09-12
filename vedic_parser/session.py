"""Session handling for vedic-horo.com / vedic-horo.ru.

Every actions.php call needs two things that belong together: the PHPSESSID
cookie and the `token_security` value printed into an inline script on any
page of the same domain. This module fetches that pair and keeps it fresh.

See docs/recon.md for the endpoint map.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import requests

BASE_EN = "https://vedic-horo.com"
BASE_RU = "https://vedic-horo.ru"

BASE_BY_LANG = {"en": BASE_EN, "ru": BASE_RU}

TOKEN_RE = re.compile(r'token_security\s*=\s*"([0-9a-f]+)"')

DEFAULT_TIMEOUT = 30


class VedicHoroError(RuntimeError):
    """Any failure talking to the site."""


class TokenNotFound(VedicHoroError):
    """The bootstrap page carried no token_security."""


class AccessDenied(VedicHoroError):
    """The action needs a paid account (403 Access Denied)."""


class BootstrapBlocked(TokenNotFound):
    """The domain answered with its JavaScript gate instead of a real page.

    vedic-horo.ru does this per client — it serves a small page that sets a
    `__jua_` cookie from JavaScript and reloads — and once it starts, it
    applies to every path on that domain. Use ``lang="en"`` (vedic-horo.com),
    or open the site in a browser and hand the session its PHPSESSID and
    token_security via :meth:`Session.adopt`.
    """


@dataclass
class Session:
    """An anonymous session against one of the two domains.

    ``lang`` picks the domain, which picks the language of every label the
    site returns: ``en`` -> vedic-horo.com, ``ru`` -> vedic-horo.ru. Textual
    interpretations only exist on ``ru``.

    The session is opened lazily; ``open()`` forces it.
    """

    lang: str = "en"
    base_url: str | None = None
    http: requests.Session = field(default_factory=requests.Session)
    timeout: int = DEFAULT_TIMEOUT
    token: str | None = None
    _adopted: bool = False

    def __post_init__(self) -> None:
        if self.base_url is None:
            try:
                self.base_url = BASE_BY_LANG[self.lang]
            except KeyError:
                raise ValueError(
                    f"lang must be one of {sorted(BASE_BY_LANG)}, got {self.lang!r}"
                ) from None
        self.base_url = self.base_url.rstrip("/")

    # -- bootstrap ---------------------------------------------------------

    def open(self, path: str = "/") -> str:
        """Fetch a page of the domain and pick up the cookie and the token.

        Any page works. The home page is used because it is small and, unlike
        analyse.php on .com, never behind the Cloudflare challenge.
        """
        response = self.http.get(
            f"{self.base_url}{path}", timeout=self.timeout, allow_redirects=True
        )
        if response.status_code == 403 and "cf-mitigated" in response.headers:
            raise VedicHoroError(
                f"{path} is behind the Cloudflare challenge; bootstrap from a plain "
                "page such as / instead"
            )
        response.raise_for_status()
        match = TOKEN_RE.search(response.text)
        if not match:
            if "__jua_" in response.text:
                raise BootstrapBlocked(
                    f"{self.base_url} served its JavaScript gate instead of a page; "
                    "use lang='en' (vedic-horo.com) or adopt() a browser session"
                )
            raise TokenNotFound(f"no token_security in {self.base_url}{path}")
        self.token = match.group(1)
        return self.token

    def adopt(self, session_id: str, token: str) -> None:
        """Use a PHPSESSID and token_security taken from a browser session.

        Both come from the same page load: the cookie from the browser's
        storage, the token from ``var token_security = "…"`` in the page
        source. They only work as a pair.
        """
        self.token = token
        self._adopted = True
        jar = self.http.cookies
        setter = getattr(jar, "set", None)
        if callable(setter):
            setter("PHPSESSID", session_id)
        else:  # a plain mapping, e.g. in tests
            jar["PHPSESSID"] = session_id

    @property
    def session_id(self) -> str | None:
        """The PHPSESSID the token is bound to."""
        return self.http.cookies.get("PHPSESSID")

    @property
    def is_open(self) -> bool:
        return bool(self.token and self.session_id)

    # -- calls -------------------------------------------------------------

    def action(self, action: str, chart: object | None = None, **params: str) -> str:
        """POST one actions.php action and return the HTML fragment.

        ``chart`` is a :class:`~vedic_parser.chart.Chart` (or anything with a
        ``to_data()`` method); actions that do not take birth data omit it.
        A 419 means the token expired, so the session is reopened once and the
        call retried.
        """
        payload: dict[str, str] = {"action": action}
        if chart is not None:
            payload["data"] = chart.to_data()
        payload.update({k: v for k, v in params.items() if v is not None})

        response = self._post("/actions.php", payload)
        if response.status_code == 419:
            if self._adopted:
                raise VedicHoroError(
                    "the adopted token has expired; adopt a fresh PHPSESSID/token pair"
                )
            self.open()
            response = self._post("/actions.php", payload)

        if response.status_code == 403:
            raise AccessDenied(
                f"action {action!r} was refused (403 {response.text.strip()[:40]!r}); "
                "it likely needs a paid account"
            )
        response.raise_for_status()
        return response.text

    def _post(self, path: str, payload: dict[str, str]) -> requests.Response:
        if not self.is_open:
            self.open()
        body = dict(payload)
        body["token_security"] = self.token or ""
        return self.http.post(
            f"{self.base_url}{path}",
            data=body,
            timeout=self.timeout,
            headers={"Referer": f"{self.base_url}/"},
        )
