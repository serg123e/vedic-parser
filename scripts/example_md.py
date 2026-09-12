#!/usr/bin/env python3
"""Regenerate the docs/example-*.md documents from the recorded responses.

    python scripts/example_md.py            # all documents
    python scripts/example_md.py show-info  # just one

Reads tests/fixtures/ only, so it needs no network and produces the same files
every run. Refresh the fixtures with scripts/probe.sh if the site changes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vedic_parser import parse_show_chart, parse_show_info  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SIGNS = ("Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi")

HEADER = """Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).
"""

FOOTER = """---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; \
обновить — `python scripts/example_md.py`."""


def fixture(name: str, parse) -> dict:
    return parse((FIXTURES / name).read_text(encoding="utf-8"))


def cell(value) -> str:
    return "—" if value in (None, "", []) else str(value)


def table(out: list[str], header: list[str], rows: list[list]) -> None:
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))
    for row in rows:
        out.append("| " + " | ".join(cell(value) for value in row) + " |")
    out.append("")


def code_block(out: list[str], language: str, *lines: str) -> None:
    out.append(f"```{language}")
    out.extend(lines)
    out.append("```\n")


def as_json(out: list[str], payload) -> None:
    code_block(out, "json", json.dumps(payload, ensure_ascii=False, indent=2))


# -- show-info -------------------------------------------------------------


def build_show_info() -> list[str]:
    d1 = fixture("show-info-en.html", parse_show_info)
    d9 = fixture("show-info-en-d9.html", parse_show_info)
    ru = fixture("analyse-natal-info-ru.html", parse_show_info)

    out = ["# Пример данных: `show-info`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-info --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Ответ — один JSON-объект: `divisional`, `from`, `planets` (10 записей) "
        "и `ashtakavarga`.\n"
    )

    out.append("## 1. Одна запись целиком\n")
    out.append(
        "Так выглядит элемент `planets` без сокращений — Венера, ретроградная, "
        "в планетной войне:\n"
    )
    as_json(out, next(p for p in d1["planets"] if p["code"] == "Ve"))

    out.append("## 2. Все десять тел (D1 Раши)\n")
    table(
        out,
        ["Код", "Планета", "Град.", "Дец.", "Знак", "Достоинство", "Навамша",
         "Накшатра", "Пада", "Упр.", "Отнош.", "Дом", "Управитель", "ФБ", "ЕБ",
         "Шад-бала", "САВ/БАВ", "Положение", "ПВ"],
        [
            [
                p["code"],
                p["name"] + (" (R)" if p["retrograde"] else ""),
                p["degrees"], p["degrees_decimal"],
                p["rasi"] and p["rasi"]["name"], p["rasi"] and p["rasi"]["dignity"],
                p["navamsa"],
                (p["nakshatra"] or {}).get("name"), (p["nakshatra"] or {}).get("pada"),
                (p["nakshatra"] or {}).get("lord"),
                p["relationship"], p["house"],
                ", ".join(("со-" if l["co_lord"] else "") + str(l["house"]) for l in p["lords"]),
                p["functional_beneficence"] and p["functional_beneficence"]["code"],
                p["natural_beneficence"] and p["natural_beneficence"]["code"],
                p["shad_bala"] and f'{p["shad_bala"]}%',
                f'{cell(p["bindu"]["sav"])} / {cell(p["bindu"]["bav"])}',
                ", ".join(m["code"] for m in p["position"]),
                p["planetary_war"],
            ]
            for p in d1["planets"]
        ],
    )
    out.append("Колонка `karaka` (Чара Караки) вынесена отдельно, чтобы таблица не расползалась:\n")
    table(out, [p["code"] for p in d1["planets"]], [[p["karaka"] for p in d1["planets"]]])
    out.append(
        "Коды: `As` асцендент, `Su Mo Ma Me Ju Ve Sa` планеты, `Ra Ke` узлы. "
        "Знаки — `Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi`. Всё это читается из "
        "CSS-классов и `href`, поэтому одинаково для обоих языков.\n"
    )

    out.append("## 3. Расшифровки, которые приходят в tooltip'ах\n")
    out.append(
        "Сокращения в колонках ФБ / ЕБ / Положение сайт поясняет в атрибуте "
        "`title` — парсер их сохраняет в `description`:\n"
    )
    glossary: dict[str, str] = {}
    for planet in d1["planets"]:
        markers = [planet["functional_beneficence"], planet["natural_beneficence"]]
        for marker in markers + planet["position"]:
            if marker and marker["description"]:
                glossary.setdefault(marker["code"], marker["description"])
    table(out, ["Код", "Значение"], [[f"`{code}`", desc] for code, desc in glossary.items()])

    out.append("## 4. Аштакаварга\n")
    first = d1["ashtakavarga"]["first_house_sign"]
    order = [SIGNS[(first - 1 + i) % 12] for i in range(12)]
    out.append(
        f"`first_house_sign` = {first} → в 1-м доме {order[0]}, дальше по порядку. "
        "Значения идут домами 1…12.\n"
    )
    rows = [["**САВ**"] + [f"**{v}**" for v in d1["ashtakavarga"]["sav"]]]
    rows += [[f"БАВ {code}"] + values for code, values in d1["ashtakavarga"]["bav"].items()]
    table(out, ["Ряд"] + [f"{i + 1}<br>{order[i]}" for i in range(12)], rows)
    planets_only = {k: v for k, v in d1["ashtakavarga"]["bav"].items() if k != "As"}
    out.append(
        "САВ — сумма семи планетных БАВ; БАВ асцендента показан рядом, но в сумму "
        "не входит (проверка по 1-му дому: "
        + " + ".join(str(v[0]) for v in planets_only.values())
        + f" = {sum(v[0] for v in planets_only.values())}).\n"
    )

    out.append("## 5. Другая варга: `--divisional D9`\n")
    code_block(out, "sh", "vedic-parser show-info ... --divisional D9")
    out.append(
        "Тут есть ловушка. Пересчитываются `degrees`, `house`, бинду и балы, "
        "а колонка «Раши» **остаётся натальным D1-знаком**, «Навамша» — D9-знаком. "
        "Знака планеты в самой варге в этом ответе нет: за ним — в `show-chart` "
        "(для D9 он совпадает с колонкой «Навамша»). Плюс у всех варг кроме D1 "
        "нет колонки накшатры, поэтому `nakshatra: null`.\n"
    )
    table(
        out,
        ["Код", "Планета", "Град. в D9", "Раши (D1!)", "Навамша (= знак в D9)", "Дом в D9",
         "Накшатра", "САВ/БАВ", "Шад-бала"],
        [
            [
                p["code"], p["name"] + (" (R)" if p["retrograde"] else ""),
                p["degrees"], p["rasi"] and p["rasi"]["name"], p["navamsa"], p["house"],
                p["nakshatra"],
                f'{cell(p["bindu"]["sav"])} / {cell(p["bindu"]["bav"])}',
                p["shad_bala"] and f'{p["shad_bala"]}%',
            ]
            for p in d9["planets"]
        ],
    )
    out.append("Аштакаварга тоже своя: САВ D9 = `" + str(d9["ashtakavarga"]["sav"]) + "`.\n")

    out.append("## 6. Русские подписи: `--lang ru`\n")
    out.append(
        "Структура та же, меняются только человекочитаемые поля; коды остаются "
        "латиницей:\n"
    )
    table(
        out,
        ["Код", "Планета", "Град.", "Знак", "Накшатра", "Пада", "Дом", "Управитель",
         "ФБ", "Положение"],
        [
            [
                p["code"], p["name"] + (" (R)" if p["retrograde"] else ""),
                p["degrees"], p["rasi"] and p["rasi"]["name"],
                (p["nakshatra"] or {}).get("name"), (p["nakshatra"] or {}).get("pada"),
                p["house"], ", ".join(str(l["house"]) for l in p["lords"]),
                p["functional_beneficence"] and p["functional_beneficence"]["code"],
                ", ".join(m["code"] for m in p["position"]),
            ]
            for p in ru["planets"][:5]
        ],
    )
    venus = next(p for p in ru["planets"] if p["code"] == "Ve")
    out.append(
        "Пример расшифровки по-русски: `"
        + venus["functional_beneficence"]["code"]
        + "` — "
        + venus["functional_beneficence"]["description"]
        + ".\n"
    )

    out.append("## 7. Чего в этом ответе нет\n")
    out.append(
        "`show-info` — это только таблица планет и аштакаварга. Остальное живёт в "
        "других действиях (см. `docs/recon.md`): сама карта с домами — "
        "`show-chart`, панчанга и упаграхи — `show-other`, даши — `show-dasha`, "
        "компоненты Шад-балы — `show-bala`, авастхи — `show-avasthas`, йоги — "
        "`show-yogas`.\n"
    )
    out.append(FOOTER)
    return out


# -- show-chart ------------------------------------------------------------


def build_show_chart() -> list[str]:
    north = fixture("show-chart-en-d1-north.html", parse_show_chart)
    south = fixture("show-chart-en-d9-south.html", parse_show_chart)
    ru = fixture("show-chart-ru-d1-north.html", parse_show_chart)

    out = ["# Пример данных: `show-chart`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-chart --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4 --divisional D1",
    )
    out.append(
        "Ответ: `style`, `divisional`, `chart` (эхо введённых данных), `houses` — "
        "всегда 12 домов по порядку, и `planets` — то же самое, но плоским списком "
        "по планетам (выводится из `houses`).\n"
    )

    out.append("## 1. Один дом целиком\n")
    out.append("4-й дом этой карты — стеллиум из трёх планет плюс два аспекта:\n")
    as_json(out, north["houses"][3])

    out.append("## 2. Все двенадцать домов (D1, North)\n")
    table(
        out,
        ["Дом", "Знак", "№", "Название", "Планеты", "Аспектируют"],
        [
            [
                h["house"], h["sign"]["code"], h["sign"]["number"], h["sign"]["name"],
                ", ".join(
                    f'{p["code"]} {p["degree"]:02d}°' + (" R" if p["retrograde"] else "")
                    for p in h["planets"]
                ),
                ", ".join(h["aspects"]),
            ]
            for h in north["houses"]
        ],
    )
    out.append("И то же самое плоским списком — `planets`:\n")
    table(
        out,
        ["Код", "Дом", "Знак", "№ знака", "Градус", "Ретро"],
        [
            [p["code"], p["house"], p["sign"], p["sign_number"], p["degree"],
             "да" if p["retrograde"] else "нет"]
            for p in north["planets"]
        ],
    )
    out.append(
        "Градусы здесь целые — в рисунке карты сайт больше не показывает. "
        "Точные, до секунды, есть в `show-info` (`degrees_decimal`).\n"
    )

    out.append("## 3. Два стиля — одна структура\n")
    out.append(
        "Разметка North и South не имеет ничего общего: в North двенадцать "
        "`div.house` в порядке домов, и каждый называет свой знак; в South — "
        "`table.chart` с ячейками в порядке знаков, и каждая называет свой дом. "
        "Парсер приводит оба к одному виду, поэтому `--style` влияет только на то, "
        "что отдаёт сервер:\n"
    )
    table(
        out,
        ["", "North (D1)", "South (D9)"],
        [
            ["`style`", f'`{north["style"]}`', f'`{south["style"]}`'],
            ["разметка", "`div.chart-north` + `div.house`×12", "`table.chart` + `td.houses`×12"],
            ["порядок в HTML", "по домам", "по знакам (переупорядочивается)"],
            ["аспекты", "`<u>Sa</u>`", "текст в `div.aspects`"],
            ["1-й дом", ", ".join(p["code"] for p in north["houses"][0]["planets"]),
             ", ".join(p["code"] for p in south["houses"][0]["planets"])],
        ],
    )

    out.append("## 4. Другая варга: D9 (South)\n")
    code_block(out, "sh", "vedic-parser show-chart ... --divisional D9 --style South")
    table(
        out,
        ["Дом", "Знак", "Планеты", "Аспектируют"],
        [
            [
                h["house"], h["sign"]["name"],
                ", ".join(
                    f'{p["code"]} {p["degree"]:02d}°' + (" R" if p["retrograde"] else "")
                    for p in h["planets"]
                ),
                ", ".join(h["aspects"]),
            ]
            for h in south["houses"]
        ],
    )
    out.append(
        "Именно отсюда берутся знаки варги — в `show-info` для D9 колонка «Раши» "
        "показывает натальный знак, а не D9 (см. `docs/example-show-info.md`, §5).\n"
    )

    out.append("## 5. Русский вариант\n")
    out.append("Коды знаков латиницей, названия — как на сайте:\n")
    table(
        out,
        ["Дом", "Код", "Название", "Планеты"],
        [
            [h["house"], h["sign"]["code"], h["sign"]["name"],
             ", ".join(p["code"] for p in h["planets"])]
            for h in ru["houses"][:6]
        ],
    )

    out.append("## 6. Сверка с `show-info`\n")
    out.append(
        "Рисунок и таблица — две проекции одного расчёта, и они сходятся: для всех "
        "десяти тел знак, дом, ретроградность и целая часть градуса совпадают "
        "(это проверяется тестом `test_agrees_with_show_info_on_the_same_chart`).\n"
    )
    out.append(
        "Чего в `show-chart` нет: аспектов планет на планеты (только на дома), "
        "аргалы, накшатр, бал. Аспекты и аргала одного дома — отдельные действия "
        "`get-aspects` / `get-argala`, они отдают компактный текст вида `Sa|5 8 11`.\n"
    )
    out.append(FOOTER)
    return out


DOCUMENTS = {
    "show-info": ("example-show-info.md", build_show_info),
    "show-chart": ("example-show-chart.md", build_show_chart),
}


def main(argv: list[str]) -> int:
    wanted = argv or list(DOCUMENTS)
    unknown = [name for name in wanted if name not in DOCUMENTS]
    if unknown:
        print(f"unknown document(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(DOCUMENTS)}", file=sys.stderr)
        return 2
    for name in wanted:
        filename, build = DOCUMENTS[name]
        target = ROOT / "docs" / filename
        target.write_text("\n".join(build()) + "\n", encoding="utf-8")
        print(f"wrote docs/{filename} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
