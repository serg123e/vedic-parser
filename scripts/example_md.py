#!/usr/bin/env python3
"""Regenerate docs/example-show-info.md from the recorded responses.

    python scripts/example_md.py

Reads tests/fixtures/ only, so it needs no network and produces the same file
every run. Refresh the fixtures with scripts/probe.sh if the site changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vedic_parser import parse_show_info  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def fixture(name: str) -> dict:
    return parse_show_info((FIXTURES / name).read_text(encoding="utf-8"))


d1 = fixture("show-info-en.html")
d9 = fixture("show-info-en-d9.html")
ru = fixture("analyse-natal-info-ru.html")

SIGNS = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"]
out = []
w = out.append

def cell(v):
    return "—" if v in (None, "", []) else str(v)

def marker(m):
    return cell(m and m["code"])

w("# Пример данных: `show-info`\n")
w("Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:")
w("**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).\n")
w("```sh")
w("vedic-parser show-info --name Ss --date 07.08.1983 --time 23:00:00 \\")
w("    --latitude 55.45 --longitude 37.37 --timezone +4")
w("```\n")
w("Ответ — один JSON-объект: `divisional`, `from`, `planets` (10 записей) и `ashtakavarga`.\n")

w("## 1. Одна запись целиком\n")
w("Так выглядит элемент `planets` без сокращений — Венера, ретроградная, в планетной войне:\n")
w("```json")
ve = [p for p in d1["planets"] if p["code"] == "Ve"][0]
w(json.dumps(ve, ensure_ascii=False, indent=2))
w("```\n")

w("## 2. Все десять тел (D1 Раши)\n")
w("| Код | Планета | Град. | Дец. | Знак | Достоинство | Навамша | Накшатра | Пада | Упр. | Отнош. | Дом | Управитель | ФБ | ЕБ | Шад-бала | САВ/БАВ | Положение | ПВ |")
w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for p in d1["planets"]:
    nak = p["nakshatra"] or {}
    lords = ", ".join(
        ("со-" if l["co_lord"] else "") + f"{l['house']}" for l in p["lords"]
    ) or "—"
    w("| {} | {}{} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
        p["code"],
        p["name"], " (R)" if p["retrograde"] else "",
        cell(p["degrees"]), cell(p["degrees_decimal"]),
        cell(p["rasi"] and p["rasi"]["name"]),
        cell(p["rasi"] and p["rasi"]["dignity"]),
        cell(p["navamsa"]),
        cell(nak.get("name")), cell(nak.get("pada")), cell(nak.get("lord")),
        cell(p["relationship"]), cell(p["house"]), lords,
        marker(p["functional_beneficence"]), marker(p["natural_beneficence"]),
        cell(p["shad_bala"] and f'{p["shad_bala"]}%'),
        f'{cell(p["bindu"]["sav"])} / {cell(p["bindu"]["bav"])}',
        ", ".join(m["code"] for m in p["position"]) or "—",
        cell(p["planetary_war"]),
    ))
w("")
w("Колонка `karaka` (Чара Караки) вынесена отдельно, чтобы таблица не расползалась:\n")
w("| " + " | ".join(p["code"] for p in d1["planets"]) + " |")
w("|" + "---|" * len(d1["planets"]))
w("| " + " | ".join(cell(p["karaka"]) for p in d1["planets"]) + " |")
w("")
w("Коды: `As` асцендент, `Su Mo Ma Me Ju Ve Sa` планеты, `Ra Ke` узлы. "
  "Знаки — `Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi`. Всё это читается из CSS-классов "
  "и `href`, поэтому одинаково для обоих языков.\n")

w("## 3. Расшифровки, которые приходят в tooltip'ах\n")
w("Сокращения в колонках ФБ / ЕБ / Положение сайт поясняет в атрибуте `title` — "
  "парсер их сохраняет в `description`:\n")
seen = {}
for p in d1["planets"]:
    for m in [p["functional_beneficence"], p["natural_beneficence"], *p["position"]]:
        if m and m["description"] and m["code"] not in seen:
            seen[m["code"]] = m["description"]
w("| Код | Значение |")
w("|---|---|")
for code, desc in seen.items():
    w(f"| `{code}` | {desc} |")
w("")

w("## 4. Аштакаварга\n")
first = d1["ashtakavarga"]["first_house_sign"]
order = [SIGNS[(first - 1 + i) % 12] for i in range(12)]
w(f"`first_house_sign` = {first} → в 1-м доме {order[0]}, дальше по порядку. "
  "Значения идут домами 1…12.\n")
w("| Ряд | " + " | ".join(f"{i+1}<br>{order[i]}" for i in range(12)) + " |")
w("|---|" + "---|" * 12)
w("| **САВ** | " + " | ".join(f"**{v}**" for v in d1["ashtakavarga"]["sav"]) + " |")
for code, values in d1["ashtakavarga"]["bav"].items():
    w(f"| БАВ {code} | " + " | ".join(str(v) for v in values) + " |")
w("")
planets_only = {k: v for k, v in d1["ashtakavarga"]["bav"].items() if k != "As"}
w("САВ — сумма семи планетных БАВ; БАВ асцендента показан рядом, но в сумму не входит "
  f"(проверка по 1-му дому: {' + '.join(str(v[0]) for v in planets_only.values())} = "
  f"{sum(v[0] for v in planets_only.values())}).\n")

w("## 5. Другая варга: `--divisional D9`\n")
w("```sh")
w("vedic-parser show-info ... --divisional D9")
w("```\n")
w("У всех варг кроме D1 в таблице на одну колонку меньше — накшатры нет, "
  "поэтому `nakshatra: null`. Положения планет пересчитаны:\n")
w("| Код | Планета | Град. | Знак | Дом | Накшатра | САВ/БАВ | Шад-бала |")
w("|---|---|---|---|---|---|---|---|")
for p in d9["planets"]:
    w("| {} | {}{} | {} | {} | {} | {} | {} | {} |".format(
        p["code"], p["name"], " (R)" if p["retrograde"] else "",
        cell(p["degrees"]), cell(p["rasi"] and p["rasi"]["name"]), cell(p["house"]),
        cell(p["nakshatra"]),
        f'{cell(p["bindu"]["sav"])} / {cell(p["bindu"]["bav"])}',
        cell(p["shad_bala"] and f'{p["shad_bala"]}%'),
    ))
w("")
w("Аштакаварга тоже своя: САВ D9 = `" + str(d9["ashtakavarga"]["sav"]) + "`.\n")

w("## 6. Русские подписи: `--lang ru`\n")
w("Структура та же, меняются только человекочитаемые поля; коды остаются латиницей:\n")
w("| Код | Планета | Град. | Знак | Накшатра | Пада | Дом | Управитель | ФБ | Положение |")
w("|---|---|---|---|---|---|---|---|---|---|")
for p in ru["planets"][:5]:
    nak = p["nakshatra"] or {}
    w("| {} | {}{} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
        p["code"], p["name"], " (R)" if p["retrograde"] else "",
        cell(p["degrees"]), cell(p["rasi"] and p["rasi"]["name"]),
        cell(nak.get("name")), cell(nak.get("pada")), cell(p["house"]),
        ", ".join(str(l["house"]) for l in p["lords"]) or "—",
        marker(p["functional_beneficence"]),
        ", ".join(m["code"] for m in p["position"]) or "—",
    ))
w("")
ru_ve = [p for p in ru["planets"] if p["code"] == "Ve"][0]
w("Пример расшифровки по-русски: `" + ru_ve["functional_beneficence"]["code"] + "` — " +
  ru_ve["functional_beneficence"]["description"] + ".\n")

w("## 7. Чего в этом ответе нет\n")
w("`show-info` — это только таблица планет и аштакаварга. Остальное живёт в других "
  "действиях (см. `docs/recon.md`): сама карта с домами — `show-chart`, панчанга и "
  "упаграхи — `show-other`, даши — `show-dasha`, компоненты Шад-балы — `show-bala`, "
  "авастхи — `show-avasthas`, йоги — `show-yogas`.\n")
w("---\n")
w("Файл сгенерирован из записанных ответов в `tests/fixtures/`; "
  "обновить — `python scripts/example_md.py`.")

target = ROOT / "docs" / "example-show-info.md"
target.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")
