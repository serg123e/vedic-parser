# vedic-parser

Tools for querying [vedic-horo.com / vedic-horo.ru](https://vedic-horo.com) and
parsing what it returns. The site has no JSON API — everything comes back as
HTML — so these tools call its `actions.php` endpoints and turn the fragments
into plain data.

The `docs/example-*.md` documents show the data these tools return for one real
chart. `docs/recon.md` maps out the endpoints, the response structure and the
access quirks. `scripts/probe.sh` dumps raw responses for inspection.

Tools so far: **session**, **show-info**, **show-chart**, **show-other**,
**show-dasha**, **show-bala**.

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

# one divisional chart: twelve houses with their signs, planets and aspects
vedic-parser show-chart --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4 --divisional D9

# the "Other" tab: special lagnas, panchanga, upagrahas, points, chakras
vedic-parser show-other --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4

# a dasha table with exact period boundaries
vedic-parser show-dasha --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4 --dasha vimshottari --level 2

# planetary strengths: Shad Bala, varga strengths, aspect matrices
vedic-parser show-bala --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4

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

Mind one trap: in a `show-info` for a varga other than D1, `rasi` is still the
natal D1 sign and `navamsa` the D9 sign — only `degrees`, `house`, `bindu` and
the balas follow the varga. The signs of that varga come from `show-chart`.

### What show-chart returns

Twelve houses in order, each with its sign (code, number, name), the bodies in
it (whole degrees, retrograde flag) and the bodies aspecting it; plus the same
placements as a flat `planets` list. `--style North|South` only changes what the
site renders — the two very different markups parse to the same shape.

### What show-other returns

`lagnas` (15 special lagnas and sphutas), `panchanga` (sunrise, sunset, hora,
vara, tithi, karana, yoga — each with the planet ruling it split off),
`upagrahas` (11 shadow points with their house), `points` (ayanamsa, sahayogi,
badhaka, dagdha rasi, 22nd drekkana, 64th navamsa, sarpa drekkana, visha
navamsa) and `chakras`.

This is the one response with no classes or hrefs anywhere, so rows and columns
are identified by position and the stable `key` fields are supplied by the
parser; the site's own wording stays in `name` / `label`. Unlike `show-info`,
signs here do follow the requested varga.

### What show-dasha returns

`periods`, each with exact `start`/`end` in ISO form (read from the row's own
attributes, not from the rendered date), the chain of `lords` as planet codes,
the rendered `labels`, and the `age` reached at the start. `kind` says whether
the system is planet-based (vimshottari, yogini, ashtottari, navamsa — lords
come back as codes) or sign-based (chara_rao, narayana — names only), and
`level` is the depth: 1 maha, 2 antar, 3 pratyantar, 4 sookshma.

Boundaries are minute-resolution and a few maha seams round a minute apart, so
do not assume periods join exactly.

### What show-bala returns

`shad_bala` per planet with every component (percentage of the required
minimum plus virupas, and rupas for the total), `varga_bala` (Vimsopaka and
Vaiseshikamsa across the four varga sets, plus the Vargottama count) and
`aspects` — the drik bala matrices onto planets and onto houses, each with the
benefic/malefic summary rows and the nature the chart assigns to each planet.
`--shad-bala-only` requests the lighter `show-shad-bala` endpoint; the missing
parts come back empty.

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
`python scripts/example_md.py` regenerates the example document from those same
fixtures.
