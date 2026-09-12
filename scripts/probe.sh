#!/usr/bin/env bash
# Probe the vedic-horo actions.php API and dump every response for inspection.
#
#   scripts/probe.sh [base-url] [out-dir]
#
# Defaults to https://vedic-horo.com (English labels) and ./probe-out.
# See docs/recon.md for what each action returns.
set -euo pipefail

BASE="${1:-https://vedic-horo.com}"
OUT="${2:-probe-out}"
CHART='name=Ss|date=07.08.1983|time=23:00:00|timezone=+4|latitude=55.45|longitude=37.37'

mkdir -p "$OUT"
JAR="$OUT/cookies.txt"
rm -f "$JAR"

# The token lives in an inline script on any page of the domain and is only
# valid together with the PHPSESSID issued in the same response.
curl -sS -c "$JAR" -o "$OUT/index.html" "$BASE/"
TOKEN=$(grep -o 'token_security = "[a-f0-9]*"' "$OUT/index.html" | head -1 | cut -d'"' -f2)
[ -n "$TOKEN" ] || { echo "no token_security found on $BASE/" >&2; exit 1; }
echo "session ready, token ${TOKEN:0:12}…"

act() { # act <name> <action> [extra curl --data-urlencode args...]
	local name="$1" action="$2"
	shift 2
	printf '%-22s ' "$action"
	curl -sS -b "$JAR" -X POST \
		--data-urlencode "action=$action" \
		--data-urlencode "data=$CHART" \
		"$@" \
		--data-urlencode "token_security=$TOKEN" \
		-o "$OUT/$name.html" -w 'HTTP %{http_code}  %{size_download} B\n' \
		"$BASE/actions.php"
}

act info          show-info      --data-urlencode 'divisional=D1' --data-urlencode 'from='
act info-moon     show-info      --data-urlencode 'divisional=D1' --data-urlencode 'from=2'
act info-d9       show-info      --data-urlencode 'divisional=D9' --data-urlencode 'from='
act chart-d1      show-chart     --data-urlencode 'divisional=D1' --data-urlencode 'style=North' --data-urlencode 'type='
act chart-d9      show-chart     --data-urlencode 'divisional=D9' --data-urlencode 'style=South' --data-urlencode 'type='
act other         show-other     --data-urlencode 'divisional=D1'
act bhava         show-bhava     --data-urlencode 'divisional=D1'
act chart-bhava   show-chart-bhava --data-urlencode 'divisional=D1' --data-urlencode 'style=North'
act periods       show-periods   --data-urlencode 'divisional=D1'
act bala          show-bala      --data-urlencode 'divisional=D1'
act avasthas      show-avasthas  --data-urlencode 'divisional=D1'
act yogas         show-yogas     --data-urlencode 'divisional=D1'
act sade-sati     show-sade-sati
act vargas        show-vargas
act current       show-current-periods
act aspects-h1    get-aspects    --data-urlencode 'sign=1' --data-urlencode 'style=North' --data-urlencode 'divisional=D1'
act argala-h1     get-argala     --data-urlencode 'type=1' --data-urlencode 'sign=1' --data-urlencode 'style=North' --data-urlencode 'divisional=D1'
act first-house   first-house    --data-urlencode 'sign=1' --data-urlencode 'style=North' --data-urlencode 'divisional=D1' --data-urlencode 'chart_big=' --data-urlencode 'type='
act transits      show-transits  # paid: expect 403 Access Denied

for level in 1 2 3; do
	act "dasha-vimshottari-l$level" show-dasha \
		--data-urlencode 'dasha=vimshottari' \
		--data-urlencode "level=$level" \
		--data-urlencode 'divisional=D1' \
		--data-urlencode 'cycle=0' \
		--data-urlencode "current=$(date +%-d.%-m.%Y' '%-H:%-M)" \
		--data-urlencode 'search='
done

# Textual interpretations: keys come from the href of a.desc links in the tables.
# Russian only — on .com these answer "Sorry, no information in English yet".
for key in 'planet?Su' 'in-sign?Su-Cn' 'in-house?Su-4' 'nakshatra?Asl' 'lord-in?5-4'; do
	name="${key%%\?*}"
	value="${key#*\?}"
	printf '%-22s ' "interpretation $name"
	curl -sS -b "$JAR" -X POST \
		--data-urlencode "option_name=$name" \
		--data-urlencode "option_value=$value" \
		--data-urlencode "token_security=$TOKEN" \
		-o "$OUT/interp-$name-$value.html" -w 'HTTP %{http_code}  %{size_download} B\n' \
		"$BASE/windows/analyse_interpretation.php"
done

# The full analyse.php page: open on .ru, Cloudflare-challenged on .com.
printf '%-22s ' 'analyse.php'
curl -sS -b "$JAR" -o "$OUT/analyse.html" -w 'HTTP %{http_code}  %{size_download} B\n' \
	"$BASE/analyse.php?name=Ss&date=07.08.1983&time=23:00:00&latitude=55.45&longitude=37.37&timezone=%2B4"

echo "responses in $OUT/"
