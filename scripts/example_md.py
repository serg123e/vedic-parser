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

from vedic_parser import (  # noqa: E402
    parse_show_avasthas,
    parse_show_bala,
    parse_show_bhava,
    parse_show_chart,
    parse_show_dasha,
    parse_show_info,
    parse_show_other,
    parse_show_sade_sati,
    parse_show_yogas,
)

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


def build_show_other() -> list[str]:
    other = fixture("show-other-en-d1.html", parse_show_other)
    ru = fixture("analyse-other-ru.html", parse_show_other)

    out = ["# Пример данных: `show-other`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-other --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Это вкладка «Разное» — пять разнородных таблиц в одном ответе: "
        "`lagnas`, `panchanga`, `upagrahas`, `points`, `chakras`.\n"
    )
    out.append(
        "**Важно про разметку:** здесь, в отличие от остальных действий, нет ни "
        "классов, ни `href`, ни tooltip'ов — только текст. Поэтому строки и "
        "колонки опознаются по позиции, а канонические ключи (`bhava_lagna`, "
        "`gulika`, `ayanamsa`, …) приделывает парсер. Подписи сайта сохраняются "
        "рядом в `name` / `label`.\n"
    )

    out.append("## 1. Особые лагны и спхуты\n")
    out.append("15 строк в фиксированном порядке:\n")
    table(
        out,
        ["Ключ", "Название", "Градусы", "Дец.", "Знак", "Накшатра", "Пада", "Упр."],
        [
            [
                f'`{x["key"]}`', x["name"], x["degrees"], x["degrees_decimal"], x["sign"],
                (x["nakshatra"] or {}).get("name"), (x["nakshatra"] or {}).get("pada"),
                (x["nakshatra"] or {}).get("lord"),
            ]
            for x in other["lagnas"]
        ],
    )
    out.append("Одна запись как JSON:\n")
    as_json(out, other["lagnas"][0])

    out.append("## 2. Панчанга\n")
    out.append(
        "Семь значений момента рождения. Титхи, карана и йога приходят с "
        "управителем через запятую — парсер его отделяет в `lord` (и признаёт "
        "только код планеты, чтобы не откусить часть названия):\n"
    )
    table(
        out,
        ["Ключ", "Подпись", "Значение", "Управитель"],
        [
            [f"`{key}`", item["label"], item["value"], item.get("lord")]
            for key, item in other["panchanga"].items()
        ],
    )

    out.append("## 3. Упаграхи\n")
    out.append("11 теневых точек — как лагны, но ещё с домом:\n")
    table(
        out,
        ["Ключ", "Название", "Градусы", "Знак", "Накшатра", "Пада", "Дом"],
        [
            [
                f'`{x["key"]}`', x["name"], x["degrees"], x["sign"],
                (x["nakshatra"] or {}).get("name"), (x["nakshatra"] or {}).get("pada"),
                x["house"],
            ]
            for x in other["upagrahas"]
        ],
    )

    out.append("## 4. Отдельные точки\n")
    out.append(
        "Ячейки бывают многострочными (одно и то же от Асцендента и от Луны — "
        "приходит списком) и перечислением кодов планет (тоже списком):\n"
    )
    table(
        out,
        ["Ключ", "Подпись", "Значение"],
        [
            [
                f"`{key}`", item["label"],
                "<br>".join(item["value"]) if isinstance(item["value"], list) else item["value"],
            ]
            for key, item in other["points"].items()
        ],
    )

    out.append("## 5. Чакры\n")
    out.append("Номер и название сайт кладёт в одну ячейку (`3 | Manipura`), парсер их делит:\n")
    table(
        out,
        ["№", "Название", "Значение", "Элемент", "Знаки", "Планеты", "Что в знаке"],
        [
            [
                c["number"], c["name"], c["meaning"], c["element"],
                ", ".join(c["signs"]), ", ".join(c["planets"]), ", ".join(c["in_sign"]),
            ]
            for c in other["chakras"]
        ],
    )

    out.append("## 6. Варга и язык\n")
    out.append(
        "`--divisional D9` пересчитывает лагны и упаграхи — и, в отличие от "
        "`show-info`, **знак здесь тоже от варги**. Бхава Лагна: D1 — "
        f'{other["lagnas"][0]["degrees"]} {other["lagnas"][0]["sign"]}, '
        "D9 — 18°35'06'' Gemini (это ровно навамша от первой). Панчанга и "
        "айянамша от варги не зависят: это свойства момента, а не карты.\n"
    )
    out.append("Русский ответ даёт те же ключи, меняются подписи:\n")
    table(
        out,
        ["Ключ", "en", "ru", "Градусы (совпадают)"],
        [
            [f'`{en["key"]}`', en["name"], ru_row["name"], en["degrees"]]
            for en, ru_row in list(zip(other["lagnas"], ru["lagnas"]))[:5]
        ],
    )
    out.append(
        "Титхи по-русски: "
        f'`{ru["panchanga"]["tithi"]["value"]}` + управитель `{ru["panchanga"]["tithi"]["lord"]}` '
        "— код остаётся латиницей.\n"
    )
    out.append(FOOTER)
    return out


def build_show_dasha() -> list[str]:
    maha = fixture("show-dasha-en-vimshottari-l1.html", parse_show_dasha)
    antar = fixture("show-dasha-en-vimshottari-l2.html", parse_show_dasha)
    chara = fixture("show-dasha-en-chara-l2.html", parse_show_dasha)
    ru = fixture("show-dasha-ru-vimshottari-l2.html", parse_show_dasha)

    out = ["# Пример данных: `show-dasha`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-dasha --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4 \\",
        "    --dasha vimshottari --level 1",
    )
    out.append(
        "Ответ: `dasha`, `divisional`, `kind`, `level` и `periods` — список "
        "периодов. Самое ценное здесь в атрибутах строки, а не в тексте:\n"
    )
    code_block(
        out,
        "html",
        '<tr start="23.11.1978 16:25" end="23.11.1997 13:21">',
        '  <td><span class="Sa">Saturn</span></td>',
        "  <td>23 Nov 1978</td><td class=\"hide\">16:25</td><td>-</td>",
        "</tr>",
    )
    out.append(
        "Границы берутся из `start`/`end` и приводятся к ISO, а видимая дата "
        "(`23 Nov 1978` / `23 ноя 1978`) остаётся просто подписью — по ней "
        "парсить не надо.\n"
    )

    out.append("## 1. Один период целиком\n")
    as_json(out, antar["periods"][12])

    out.append("## 2. Маха-даши (`--level 1`)\n")
    out.append(f'Девять периодов Вимшоттари, `kind` = `{maha["kind"]}`:\n')
    table(
        out,
        ["Управитель", "Начало", "Конец", "Возраст", "Подпись сайта"],
        [
            [", ".join(p["lords"]), p["start"], p["end"], p["age"], p["start_label"]]
            for p in maha["periods"]
        ],
    )
    out.append(
        "`age` — возраст на начало периода; у первой махи он `null`, потому что "
        "она началась до рождения (1978 против 1983 — это нормально, Вимшоттари "
        "стартует от накшатры Луны).\n"
    )

    out.append("## 3. Антар-даши (`--level 2`)\n")
    out.append(
        f'Уровень множит число строк: {len(antar["periods"])} строк вместо '
        f'{len(maha["periods"])}. Уровни: 1 маха, 2 антар, 3 пратьянтар '
        "(≈700 строк, ~175 КБ), 4 сукшма. Первые девять — антары внутри махи "
        "Сатурна:\n"
    )
    table(
        out,
        ["Цепочка", "Начало", "Конец", "Возраст"],
        [
            ["-".join(p["lords"]), p["start"], p["end"], p["age"]]
            for p in antar["periods"][:9]
        ],
    )
    out.append(
        "Вложенность сходится: первая антара начинается ровно с махой, последняя "
        "ею же заканчивается.\n"
    )
    seams = [
        (a["labels"], a["end"], b["start"])
        for a, b in zip(antar["periods"], antar["periods"][1:])
        if a["end"] != b["start"]
    ]
    out.append(
        "**Одна особенность данных:** время приходит с точностью до минуты, и на "
        "стыках махи две стороны иногда округляются по-разному. В этой таблице "
        f'такой шов один: после {"-".join(seams[0][0])} конец `{seams[0][1]}`, '
        f"а следующий период начинается в `{seams[0][2]}`. То есть на строгую "
        "непрерывность полагаться нельзя.\n"
    )

    out.append("## 4. Знаковые даши\n")
    code_block(out, "sh", "vedic-parser show-dasha ... --dasha chara_rao --level 2")
    out.append(
        "Чара и Нарайана идут по знакам, и сайт печатает их обычным текстом — "
        "без `<span class=\"Sa\">`. Поэтому `kind` = `sign`, `lords` пустой, а в "
        "`labels` лежат названия на языке домена. Если нужны коды знаков — "
        "сопоставление имя→код даёт `show-chart` для того же языка.\n"
    )
    table(
        out,
        ["Цепочка", "Начало", "Конец", "Возраст"],
        [
            ["-".join(p["labels"]), p["start"], p["end"], p["age"]]
            for p in chara["periods"][:8]
        ],
    )
    out.append(
        f'Всего периодов: {len(chara["periods"])} — знаковые даши покрывают '
        "больше века, поэтому таблица длинная.\n"
    )

    out.append("## 5. Шесть систем\n")
    table(
        out,
        ["`--dasha`", "Тип", "Что это"],
        [
            ["`vimshottari`", "планетная", "основная, 120 лет"],
            ["`yogini`", "планетная", "36 лет"],
            ["`ashtottari`", "планетная", "108 лет"],
            ["`chara_rao`", "знаковая", "Чара даша в трактовке К.Н. Рао"],
            ["`narayana`", "знаковая", "Нарайана даша"],
            ["`navamsa`", "планетная", "Навамша даша"],
        ],
    )
    out.append(
        "Плюс параметры `--divisional` (любая варга D1…D60), `--current` "
        "(какой отрезок последовательности вернуть, по умолчанию «сейчас») и "
        "`--cycle` (шаг целыми циклами — те самые стрелки ↓↑ в интерфейсе).\n"
    )

    out.append("## 6. Язык ничего не меняет\n")
    out.append(
        "Русский ответ даёт те же коды и те же границы до минуты — отличаются "
        "только подписи:\n"
    )
    table(
        out,
        ["Коды", "Начало", "en", "ru"],
        [
            ["-".join(en["lords"]), en["start"], "-".join(en["labels"]), "-".join(ru_row["labels"])]
            for en, ru_row in list(zip(antar["periods"], ru["periods"]))[:5]
        ],
    )
    out.append(FOOTER)
    return out


def build_show_bala() -> list[str]:
    bala = fixture("show-bala-en-d1.html", parse_show_bala)
    ru = fixture("show-shad-bala-ru-d1.html", parse_show_bala)

    out = ["# Пример данных: `show-bala`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-bala --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Четыре таблицы в одном ответе: `shad_bala`, `varga_bala` и две матрицы "
        "аспектов в `aspects`. Есть облегчённый вариант — `--shad-bala-only` "
        "(действие `show-shad-bala`), он отдаёт только первую таблицу, втрое "
        "меньше по объёму.\n"
    )
    out.append(
        "Колонки здесь сгруппированы через `colspan`, причём ячейки перекрывают "
        "группы неравномерно: у одних бал это пара «процент + вирупы», у других "
        "одно число. Парсер разворачивает и шапку, и строку в колонки и "
        "сопоставляет их, а таблицы опознаёт по строению (сколько строк в шапке, "
        "чем подписаны колонки), не по подписям.\n"
    )

    out.append("## 1. Шад-бала\n")
    out.append("Одна планета целиком:\n")
    as_json(out, bala["shad_bala"][0])
    out.append("И все семь — процент от необходимого минимума:\n")
    keys = list(bala["shad_bala"][0]["components"])
    table(
        out,
        ["Планета"] + [f'`{k}`' for k in keys],
        [
            [row["code"]]
            + [
                (
                    f'{c["percent"]}% / {c["virupas"]}'
                    if c["percent"] is not None
                    else (c["virupas"] if c["virupas"] is not None else None)
                )
                for c in (row["components"][k] for k in keys)
            ]
            for row in bala["shad_bala"]
        ],
    )
    out.append(
        "Где есть процент — это доля от требуемого минимума, а второе число "
        "вирупы. У Шад-балы дополнительно приходят рупы (те же вирупы делённые "
        "на 60 — сходится на всех семи планетах). Йуддха-бала пустая: в этой "
        "карте никто не в планетной войне. Проценты совпадают с колонкой "
        "«Шад-бала» в `show-info`.\n"
    )

    out.append("## 2. Варга-балы\n")
    out.append(
        "Вимшопака и Вайшешикамша считаются по наборам варг; набор опознаётся по "
        "числу в подписи («Shodasha Varga (16)»), которое от языка не зависит — "
        "отсюда ключи `shodasha` / `dasha` / `sapta` / `shad`. Варготтама-бала — "
        "просто счётчик. Здесь 9 строк: с Раху и Кету.\n"
    )
    table(
        out,
        ["Планета", "Вимшопака 16", "10", "7", "6", "Вайшешикамша 16", "Варготтама"],
        [
            [
                row["code"],
                f'{row["vimsopaka"]["shodasha"]["percent"]}% / {row["vimsopaka"]["shodasha"]["value"]}',
                f'{row["vimsopaka"]["dasha"]["percent"]}%',
                f'{row["vimsopaka"]["sapta"]["percent"]}%',
                f'{row["vimsopaka"]["shad"]["percent"]}%',
                row["vaiseshikamsa"]["shodasha"]["percent"],
                row["vargottama"],
            ]
            for row in bala["varga_bala"]
        ],
    )

    out.append("## 3. Матрица аспектов на планеты\n")
    on_planets = bala["aspects"]["on_planets"]
    out.append(
        "Строки — аспектирующие планеты (узлы не аспектируют), колонки — цели. "
        "В ячейках вирупы дрик-балы. Там, где сайт печатает `+` или `-`, "
        "величины нет — парсер сохраняет символ как есть.\n"
    )
    table(
        out,
        ["От \\ на"] + on_planets["columns"] + ["природа"],
        [
            [code] + values + [on_planets["nature"].get(code)]
            for code, values in on_planets["rows"].items()
        ]
        + [
            ["**+ (благо)**"] + on_planets["totals"]["benefic"] + [""],
            ["**− (вред)**"] + on_planets["totals"]["malefic"] + [""],
        ],
    )
    out.append(
        "Две нижние строки — суммы: `+` складывает аспекты благодетелей, `−` — "
        "вредителей, а символьные ячейки дают ноль. Это проверено арифметикой по "
        "всем колонкам обеих матриц. Кто благодетель — вердикт самой карты (цвет "
        "подписи строки), и он совпадает с колонкой «ЕБ» в `show-info`: Луна "
        "здесь убывающая, поэтому вредитель.\n"
    )

    out.append("## 4. Матрица аспектов на дома\n")
    on_houses = bala["aspects"]["on_houses"]
    table(
        out,
        ["От \\ дом"] + [str(h) for h in on_houses["columns"]],
        [[code] + values for code, values in on_houses["rows"].items()]
        + [
            ["**+**"] + on_houses["totals"]["benefic"],
            ["**−**"] + on_houses["totals"]["malefic"],
        ],
    )

    out.append("## 5. Облегчённый вариант и язык\n")
    out.append(
        "`--shad-bala-only` отдаёт ту же структуру, только `varga_bala` и "
        "`aspects` приходят пустыми. Числа от языка не зависят:\n"
    )
    table(
        out,
        ["Код", "en", "ru", "Шад-бала", "Вирупы", "Рупы"],
        [
            [
                en["code"], en["name"], ru_row["name"],
                f'{en["components"]["shad_bala"]["percent"]}%',
                en["components"]["shad_bala"]["virupas"],
                en["components"]["shad_bala"]["rupas"],
            ]
            for en, ru_row in zip(bala["shad_bala"], ru["shad_bala"])
        ],
    )
    out.append(FOOTER)
    return out


def build_show_yogas() -> list[str]:
    en = fixture("show-yogas-en-d1.html", parse_show_yogas)
    ru = fixture("show-yogas-ru-d1.html", parse_show_yogas)

    out = ["# Пример данных: `show-yogas`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-yogas --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Ответ — только те йоги, которые в карте **образовались**; длина списка "
        f'зависит от карты (здесь {len(en["yogas"])}, на других картах попадалось '
        "от 26 до 42). Разметка — голый набор `<tr>` без таблицы вокруг.\n"
    )

    out.append("## 1. Одна запись\n")
    as_json(out, en["yogas"][0])

    counts: dict[str, int] = {}
    for yoga in en["yogas"]:
        counts[yoga["category"]] = counts.get(yoga["category"], 0) + 1
    out.append("## 2. Категории\n")
    out.append(
        "Категория лежит в атрибуте строки `type`, но переводится вместе с "
        "интерфейсом, поэтому парсер приводит её к стабильному ключу; незнакомую "
        "категорию он не угадывает — `category` станет `null`, а подпись "
        "сохранится в `category_label`.\n"
    )
    table(
        out,
        ["`category`", "en", "ru", "Сколько в этой карте"],
        [
            [f"`{key}`", label_en, label_ru, counts.get(key)]
            for key, label_en, label_ru in [
                ("mahapurusha", "Mahapurusha", "Махапуруша"),
                ("solar", "Solar", "Солнечные"),
                ("lunar", "Lunar", "Лунные"),
                ("nabhasa", "Nabhasa", "Набхаса"),
                ("raja_dhana", "Raja + Dhana", "Раджа + Дхана"),
                ("other", "Other", "Другие"),
            ]
        ],
    )

    out.append("## 3. Все йоги карты\n")
    table(
        out,
        ["Йога", "Категория", "Планеты", "Эффект", "Условие"],
        [
            [
                y["name"], f'`{y["category"]}`',
                ", ".join(y["planets"]) or y["planets_label"],
                y["effect"], y["condition"],
            ]
            for y in en["yogas"]
        ],
    )
    out.append(
        "Йога, которая образуется и от Асцендента, и от Луны, приходит двумя "
        "строками («Sasa» и «Sasa (from Moon)») — суффикс локализован, поэтому "
        "разбирать его парсер не пытается.\n"
    )
    out.append(
        "`All` в колонке планет означает «все планеты» и остаётся английским даже "
        "в русском ответе — это стабильный токен, отсюда булево `all_planets`.\n"
    )

    out.append("## 4. Русский ответ\n")
    out.append("Строка в строку та же, отличаются только тексты:\n")
    table(
        out,
        ["`category`", "Планеты", "en", "ru"],
        [
            [f'`{a["category"]}`', ", ".join(a["planets"]) or a["planets_label"],
             a["name"], b["name"]]
            for a, b in list(zip(en["yogas"], ru["yogas"]))[:6]
        ],
    )
    out.append(FOOTER)
    return out


def build_show_avasthas() -> list[str]:
    en = fixture("show-avasthas-en-d1.html", parse_show_avasthas)
    ru = fixture("show-avasthas-ru-d1.html", parse_show_avasthas)
    sun = next(p for p in en["planets"] if p["code"] == "Su")

    out = ["# Пример данных: `show-avasthas`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-avasthas --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Состояния планет: `planets` (9 записей — с узлами), `shayanadi_legend` "
        "и `shayanadi_note`. В ответе три таблицы: авастхи по возрасту и "
        "пробуждённости, авастхи по настроению с причинами, шаянади по "
        "деятельности.\n"
    )
    out.append(
        "Вердикт сайт кодирует цветом, и цвет строго следует за силой: 100% — "
        "зелёный, 50% — оранжевый, 25/15/0% — красный. Парсер отдаёт класс как "
        "`tone`, ничего не переосмысливая.\n"
    )

    out.append("## 1. Балади и джаградади\n")
    table(
        out,
        ["Планета", "Балади (по возрасту)", "Сила", "Джаградади (по пробуждённости)", "Сила"],
        [
            [p["code"] + " " + p["name"], p["baladi"]["state"],
             f'{p["baladi"]["strength_percent"]}%', p["jagradadi"]["state"],
             f'{p["jagradadi"]["strength_percent"]}%']
            for p in en["planets"]
        ],
    )

    out.append("## 2. Авастхи по настроению\n")
    out.append(
        "Диптади и Ладжджитади приходят двумя параллельными колонками: состояние "
        "и причина. Причина называет виновников, и коды планет и знаков в ней "
        "остаются латиницей на обоих языках — парсер вытаскивает их точным "
        "совпадением. Солнце этой карты:\n"
    )
    table(
        out,
        ["Состояние", "Тон", "Причина", "Планеты", "Знаки"],
        [
            [m["state"], m["tone"], m["reason"], ", ".join(m["planets"]), ", ".join(m["signs"])]
            for m in sun["deeptadi"]
        ],
    )

    out.append("## 3. Шаянади-авастхи\n")
    out.append(f'_{en["shayanadi_note"]}_\n')
    out.append(
        "Поэтому сила приходит не одним числом, а по всем пяти группам слогов — "
        "выбирать нужную должен тот, кто знает имя:\n"
    )
    letters = [" ".join(g["letters"]) for g in sun["shayanadi"]["by_letter_group"]]
    table(
        out,
        ["Планета", "Состояние"] + letters,
        [
            [p["code"], p["shayanadi"]["state"]]
            + [f'{g["strength_percent"]}%' for g in p["shayanadi"]["by_letter_group"]]
            for p in en["planets"]
        ],
    )
    out.append("Запись одной планеты целиком:\n")
    as_json(out, sun["shayanadi"])

    out.append("## 4. Легенда шаянади\n")
    out.append(
        "Перечислены только состояния, встретившиеся в этой карте; число в "
        "скобках — сколько планет в этом состоянии (в сумме ровно "
        f'{sum(e["count"] for e in en["shayanadi_legend"])} — все планеты):\n'
    )
    table(
        out,
        ["Состояние", "Планет", "Тон", "Описание"],
        [
            [e["state"], e["count"], e["tone"], e["description"]]
            for e in en["shayanadi_legend"]
        ],
    )

    out.append("## 5. Русский ответ\n")
    ru_sun = next(p for p in ru["planets"] if p["code"] == "Su")
    table(
        out,
        ["Поле", "en", "ru"],
        [
            ["Балади", sun["baladi"]["state"], ru_sun["baladi"]["state"]],
            ["Джаградади", sun["jagradadi"]["state"], ru_sun["jagradadi"]["state"]],
            ["Шаянади", sun["shayanadi"]["state"], ru_sun["shayanadi"]["state"]],
            ["Сила (совпадает)", f'{sun["baladi"]["strength_percent"]}%',
             f'{ru_sun["baladi"]["strength_percent"]}%'],
            ["Группы слогов (совпадают)", " ".join(sun["shayanadi"]["by_letter_group"][0]["letters"]),
             " ".join(ru_sun["shayanadi"]["by_letter_group"][0]["letters"])],
        ],
    )
    out.append(FOOTER)
    return out


def build_show_bhava() -> list[str]:
    bhava = fixture("show-bhava-en-d1.html", parse_show_bhava)

    out = ["# Пример данных: `show-bhava`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-bhava --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Бхава-чалита: `houses` — двенадцать домов с куспидом, границами, "
        "размером и составом, и `chart` — рисунок в той же разметке, что у "
        "`show-chart` (разбирается тем же парсером).\n"
    )
    out.append(
        "**Чего здесь нет: бхава-балы.** Сайт в этом ответе силу домов не "
        "отдаёт вообще — только геометрию и состав. Ближайшее, что есть среди "
        "открытых действий, — матрица дрик-балы на дома в `show-bala`.\n"
    )

    out.append("## 1. Один дом целиком\n")
    as_json(out, bhava["houses"][0])

    out.append("## 2. Все двенадцать\n")
    out.append(
        "Дома неравные: каждый начинается в одном знаке, а заканчивается в "
        "следующем, и размеры гуляют от 24° до 35°.\n"
    )
    table(
        out,
        ["Дом", "Куспид", "Начало", "Конец", "Размер", "Планеты"],
        [
            [
                h["house"],
                f'{h["cusp"]["sign"]} {h["cusp"]["degrees"]}',
                f'{h["start"]["sign"]} {h["start"]["degrees"]}',
                f'{h["end"]["sign"]} {h["end"]["degrees"]}',
                h["size"],
                ", ".join(h["planets"]),
            ]
            for h in bhava["houses"]
        ],
    )
    total = sum(h["size_decimal"] for h in bhava["houses"])
    out.append(
        f"Сумма размеров — {total:.4f}°, то есть дома покрывают зодиак целиком "
        "(разница в сотые — округление секунд).\n"
    )

    out.append("## 3. Рисунок из того же ответа\n")
    out.append(
        "Состав домов в таблице и в рисунке сходится по всем двенадцати "
        "(проверяется тестом). Планеты в бхава-чалите расставлены по домам, а не "
        "по знакам, поэтому положения отличаются от D1:\n"
    )
    drawing: dict[int, list[str]] = {}
    for planet in bhava["chart"]["planets"]:
        drawing.setdefault(planet["house"], []).append(planet["code"])
    table(
        out,
        ["Дом", "Знак", "Планеты в бхава-чалите"],
        [
            [h["house"], h["sign"]["name"], ", ".join(drawing.get(h["house"], []))]
            for h in bhava["chart"]["houses"]
        ],
    )
    out.append(
        "Отдельное действие `show-chart-bhava` отдаёт только этот рисунок, без "
        "таблицы, и разбирается функцией `parse_show_chart`.\n"
    )
    out.append(FOOTER)
    return out


def build_show_sade_sati() -> list[str]:
    sade = fixture("show-sade-sati-en.html", parse_show_sade_sati)

    out = ["# Пример данных: `show-sade-sati`\n", HEADER]
    code_block(
        out,
        "sh",
        "vedic-parser show-sade-sati --name Ss --date 07.08.1983 --time 23:00:00 \\",
        "    --latitude 55.45 --longitude 37.37 --timezone +4",
    )
    out.append(
        "Проходы Сатурна по знаку натальной Луны. Варга не передаётся — саде-сати "
        "считается от Луны. Сайт даёт **два метода**, в каждом по четыре периода "
        "на всю жизнь, поэтому даты уходят далеко за пределы обычного срока.\n"
    )
    out.append(
        "Разметка здесь рыхлая — заголовки, вложенные div'ы, оформление, — но "
        "даты машинные:\n"
    )
    code_block(out, "html", '<span class="data" data="23.07.2002 00:00">23 Jul 2002</span>')
    out.append(
        "Парсер берёт их из `data`, а не из подписи. Плюс обходит баг вёрстки: у "
        "контейнера с фазами не закрыта кавычка в `style`, из-за чего любой "
        "парсер съедает первый `<u>` — поэтому сегменты ищутся по самим датам, а "
        "не по обёртке.\n"
    )

    out.append("## 1. Что где\n")
    table(
        out,
        ["Метод", "Период", "Начало", "Конец", "Сегментов"],
        [
            [m["title"], p["title"], p["start"], p["end"], len(p["segments"])]
            for m in sade["methods"]
            for p in m["periods"]
        ],
    )

    first = sade["methods"][0]["periods"][0]
    out.append("## 2. Первый период подробно\n")
    out.append(
        "`start`/`end` — непрерывный основной период, `segments` — все отрезки с "
        "положением Сатурна. `within_main` отделяет фазы внутри периода от "
        "касаний снаружи: Сатурн заходит в знак, разворачивается ретроградно и "
        "выходит обратно, и такие заходы сайт показывает отдельно.\n"
    )
    table(
        out,
        ["Начало", "Конец", "Положение", "Дом", "Внутри периода"],
        [
            [s["start"][:10], s["end"][:10], s["description"], s["house"],
             "да" if s["within_main"] else "нет"]
            for s in first["segments"]
        ],
    )
    out.append("Одна запись как JSON:\n")
    as_json(out, first["segments"][1])
    out.append(
        "Фазы внутри периода стыкуются встык и покрывают его целиком — от "
        f'`{first["start"]}` до `{first["end"]}` (проверяется тестом по всем '
        "восьми периодам обоих методов).\n"
    )

    houses = sorted({
        s["house"] for m in sade["methods"] for p in m["periods"] for s in p["segments"]
    })
    out.append("## 3. Дома\n")
    out.append(
        f"В описаниях встречаются дома {houses} — 12-й, 1-й и 2-й от Луны, то есть "
        "сама саде-сати, плюс 11-й в методе Катве, который начинает отсчёт "
        "раньше. Номер дома парсер вытаскивает из текста (цифра переживает "
        "перевод, остальная формулировка — нет).\n"
    )
    out.append(FOOTER)
    return out


DOCUMENTS = {
    "show-info": ("example-show-info.md", build_show_info),
    "show-chart": ("example-show-chart.md", build_show_chart),
    "show-other": ("example-show-other.md", build_show_other),
    "show-dasha": ("example-show-dasha.md", build_show_dasha),
    "show-bala": ("example-show-bala.md", build_show_bala),
    "show-yogas": ("example-show-yogas.md", build_show_yogas),
    "show-avasthas": ("example-show-avasthas.md", build_show_avasthas),
    "show-bhava": ("example-show-bhava.md", build_show_bhava),
    "show-sade-sati": ("example-show-sade-sati.md", build_show_sade_sati),
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
