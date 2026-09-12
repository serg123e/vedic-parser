# vedic-parser

Tools for querying [vedic-horo.com / vedic-horo.ru](https://vedic-horo.com) and
parsing what it returns. The site has no JSON API — everything comes back as
HTML — so these tools call its `actions.php` endpoints and turn the fragments
into plain data.

`docs/recon.md` maps out the endpoints, the response structure and the access
quirks. `scripts/probe.sh` dumps raw responses for inspection.

Two tools so far: **session** and **show-info**.

## Install

```sh
pip install -e '.[dev]'
```

## Use

```sh
# open a session: the PHPSESSID + token_security pair every call needs
vedic-parser session

# the main planets table and Ashtakavarga, as JSON
vedic-parser show-info --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4

# another divisional chart, or reckoned from the Moon (2), Sun (1), Arudha Lagna (AL)
vedic-parser show-info ... --divisional D9
vedic-parser show-info ... --from 2

# parse a response saved earlier, without touching the network
vedic-parser show-info ... --html response.html
```

`--lang en` (default) uses vedic-horo.com and returns English labels, `--lang ru`
uses vedic-horo.ru and returns Russian ones. Options work before or after the
subcommand.

From Python:

```python
from vedic_parser import Chart, Session, api

chart = Chart(
    name="Ss", date="07.08.1983", time="23:00:00",
    timezone="+4", latitude="55.45", longitude="37.37",
)
info = api.show_info(Session(), chart, divisional="D1")

info["planets"][1]["code"]        # 'Su'
info["planets"][1]["house"]       # 4
info["planets"][1]["bindu"]       # {'sav': 26, 'bav': 7}
info["ashtakavarga"]["sav"]       # [35, 38, 31, 26, 28, 29, 25, 18, 28, 31, 27, 21]
```

Coordinates are degrees and minutes, not decimal degrees: `55.45` means 55°45',
exactly as the site's own form submits them. Negative for South and West.

### What show-info returns

Per body (Ascendant plus the nine grahas): `code`, `name`, `retrograde`,
`karaka`, `degrees` and `degrees_decimal`, `rasi` (with sign code and the
dignity from its tooltip), `navamsa`, `nakshatra` (name, pada, lord — D1 only),
`relationship`, `house`, `lords`, `functional_beneficence`,
`natural_beneficence`, `shad_bala`, `bindu`, `position` markers and
`planetary_war`. Plus `ashtakavarga` with the SAV row and the eight BAV rows.

Codes (`Su`, `Cn`, `Asl`, house and lordship numbers) are read from CSS classes
and hrefs, so they are the same in both languages; `name` fields carry whatever
the site rendered.

## Access notes

* Only `vedic-horo.com/analyse.php` is behind a Cloudflare challenge. The
  `actions.php` endpoints these tools use are not, so no challenge solving is
  involved anywhere.
* `vedic-horo.ru` intermittently answers every path with a small JavaScript
  gate page instead of content. When that happens the session raises
  `BootstrapBlocked`; use `--lang en`, or open the site in a browser and pass
  `--session-id` and `--token` from that page load.
* Paid features (transits, compatibility, varshaphala, muhurta) answer
  `403 Access Denied` and raise `AccessDenied`.
* Every call makes the site compute a chart, so cache responses rather than
  re-requesting them.

## Tests

```sh
python -m pytest
```

The suite is offline: the parser runs against recorded responses in
`tests/fixtures/`, and the session tests replace the HTTP layer with a stub.
