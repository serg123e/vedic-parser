# AGENTS.md

Справочник по подключению парсеров `vedic-parser` — для агентов и для кода,
который будет их вызывать. Здесь: как устроен поток данных, что на входе, какие
схемы на выходе, как запускать и где грабли.

Сопутствующее чтение: `docs/recon.md` — карта эндпоинтов сайта и его особенности;
`docs/example-*.md` — реальные ответы по одной карте, таблицами; `README.md` —
краткая инструкция для человека.

---

## 1. Как это устроено

Сайт [vedic-horo.com](https://vedic-horo.com) (и его русское зеркало
`vedic-horo.ru`) не имеет JSON API: всё отдаётся готовым HTML. Библиотека делает
две вещи:

1. **`Session`** — держит пару «cookie + токен», без которой `actions.php` не
   отвечает, и шлёт POST-запросы.
2. **`parse_*`** — превращают HTML-фрагменты в обычные `dict`/`list`, пригодные
   для `json.dumps` без дополнительной обработки.

```
Chart (данные рождения)
      │
      ▼
Session.action("show-info", chart, divisional="D9")   →  HTML-фрагмент
      │                                                        │
      │                                                        ▼
      └──────────────  api.show_info(session, chart)  ──►  parse_show_info(html)  →  dict
```

Слои независимы. `parse_*` — чистые функции от строки, сеть им не нужна: их можно
скармливать сохранённым ответам, кускам страницы `analyse.php` или фикстурам.

Модули:

| Модуль | Назначение |
|---|---|
| `vedic_parser.chart` | `Chart` — данные рождения, `parse_degrees` |
| `vedic_parser.session` | `Session`, исключения |
| `vedic_parser.api` | по функции на действие: запрос + разбор |
| `vedic_parser.parsers` | `parse_show_*` — чистые парсеры HTML |
| `vedic_parser.cli` | CLI поверх `api`, печатает JSON в stdout |

---

## 2. Вход

### `Chart`

```python
from vedic_parser import Chart

chart = Chart(
    name="Ss",              # имя или название события, произвольная строка
    date="07.08.1983",      # ДД.ММ.ГГГГ
    time="23:00:00",        # ЧЧ:ММ:СС
    timezone="+4",          # часы от UTC: "+4", "-5.30"
    latitude="55.45",       # градусы.минуты, отрицательные — южная широта
    longitude="37.37",      # градусы.минуты, отрицательные — западная долгота
)
```

**Координаты — это не десятичные градусы.** `55.45` означает 55°45′, а не
55,45°. Так их отправляет собственная форма сайта; передашь десятичные — получишь
другую карту без единой ошибки. Всё — строки: сайт принимает их как есть, и
любое приведение типов только исказило бы ввод.

`chart.to_data()` даёт ту самую pipe-строку, которую ждёт `actions.php`:
`name=Ss|date=07.08.1983|time=23:00:00|timezone=+4|latitude=55.45|longitude=37.37`.

### `Session`

```python
from vedic_parser import Session

session = Session()            # lang="en" → vedic-horo.com
session = Session(lang="ru")   # → vedic-horo.ru
```

Параметры: `lang` (`en`/`ru`), `base_url` (полностью заменяет домен), `http`
(свой `requests.Session` — для ретраев, прокси, тестов), `timeout` (30 с).

Сессия открывается лениво при первом запросе; `session.open()` форсирует.
`session.token` и `session.session_id` — та самая пара. `session.action(...)`
возвращает сырой HTML, если нужен свой разбор.

**Язык выбирается доменом, не параметром.** Он влияет только на подписи; коды
(`Su`, `Cn`, `Asl`, номера домов) везде одинаковы.

---

## 3. Выход: общие правила

* Всё сериализуется в JSON без обработки (`json.dumps(result)` — есть тест на
  каждый парсер).
* Отсутствующее значение — `None`, а не `"-"` и не `""`. Пустой список — `[]`.
* **Коды стабильны, подписи — нет.** Читаются из CSS-классов и `href`:
  * планеты: `As Su Mo Ma Me Ju Ve Sa Ra Ke`;
  * знаки: `Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi`;
  * дома и управляемые дома — числа 1…12.
  Поля `name` / `label` несут то, что нарисовал сайт, на языке домена. Сравнивать
  и ветвиться нужно по кодам.
* Градусы приходят в двух видах: `degrees` — строка как на сайте
  (`"21°05'41''"`), `degrees_decimal` — то же числом (`21.094722`).
* Поле `divisional` в результатах `api.*` — та варга, которую **запросили**.
  Разметка ответа отдаёт значение по умолчанию для сессии (сайт переключает
  `<select>` уже в JS), поэтому `parse_*` без `api` доверять ему нельзя.

---

## 4. Схемы по действиям

Ниже — сокращённые схемы; полные примеры с настоящими числами лежат в
`docs/example-<действие>.md`.

### 4.1 `show_info` — таблица планет и аштакаварга

```python
api.show_info(session, chart, divisional="D1", from_="")
```

`from_`: `""` от Асцендента, `"1"` от Солнца, `"2"` от Луны, `"AL"` от Арудха
Лагны (сайт в этих случаях ждёт `divisional="D1"`).

```python
{
  "divisional": "D1", "from": None,
  "planets": [                       # 10: As + 9 грах, всегда в этом порядке
    {"code": "Su", "name": "Sun", "retrograde": False, "karaka": "AK",
     "degrees": "21°05'41''", "degrees_decimal": 21.094722,
     "rasi": {"code": "Cn", "name": "Cancer", "dignity": "Friend"},
     "navamsa": "Capricorn",
     "nakshatra": {"code": "Asl", "name": "Aslesha", "pada": 2, "lord": "Me"},
     "relationship": "Neutral", "house": 4,
     "lords": [{"house": 5, "in_house": 4, "co_lord": False, "label": "5th"}],
     "functional_beneficence": {"code": "B", "description": "Benefic. 100% benefic"},
     "natural_beneficence": {"code": "M", "description": "..."},
     "shad_bala": 124,                       # проценты от минимума
     "bindu": {"sav": 26, "bav": 7},
     "position": [{"code": "ZDB", "description": "Zero Dig Bala. ..."}],
     "planetary_war": None},
  ],
  "ashtakavarga": {
    "first_house_sign": 1,
    "sav": [35, 38, ...],            # 12 значений, домами 1…12
    "bav": {"As": [...], "Su": [...], ...},   # 8 рядов по 12
  },
}
```

Заметки:
* `house` у Асцендента `None` (он по определению в 1-м). `karaka`, `relationship`
  у него тоже пустые.
* `lords` — управляемые дома из `href` (`lord-in?<управляемый>-<где стоит>`);
  у узлов `co_lord: True`.
* Сокращения в `functional_beneficence` / `natural_beneficence` / `position`
  приходят с расшифровкой в `description` — это tooltip сайта.
* САВ — сумма **семи** планетных БАВ; БАВ Асцендента показан рядом, но в сумму
  не входит.

### 4.2 `show_chart` — одна карта, 12 домов

```python
api.show_chart(session, chart, divisional="D1", style="North")  # или "South"
```

```python
{
  "style": "north", "divisional": "D1",
  "chart": {"name": "Ss", "date": "07.08.1983", "time": "23:00:00",
            "timezone": "+4", "latitude": "55.45", "longitude": "37.37"},
  "houses": [                        # всегда 12, по порядку домов
    {"house": 1,
     "sign": {"number": 1, "code": "Ar", "name": "Aries"},
     "planets": [{"code": "As", "degree": 0, "degree_label": "00°",
                  "retrograde": False}],
     "aspects": ["Sa"]},             # кто аспектирует дом, кодами
  ],
  "planets": [                       # то же плоским списком, выводится из houses
    {"code": "Su", "house": 4, "sign": "Cn", "sign_number": 4,
     "degree": 21, "retrograde": False},
  ],
}
```

`--style` меняет только то, что рисует сервер: разметки North и South не имеют
между собой ничего общего, но парсер приводит их к одной форме. Градусы в
рисунке **целые**; точные — в `show_info`.

### 4.3 `show_other` — вкладка «Разное»

```python
api.show_other(session, chart, divisional="D1")
```

```python
{
  "divisional": "D1",
  "lagnas": [                        # 15 строк, ключи из LAGNA_KEYS
    {"key": "bhava_lagna", "name": "Bhava Lagna",
     "degrees": "08°43'54''", "degrees_decimal": 8.731667, "sign": "Aries",
     "nakshatra": {"name": "Ashvini", "pada": 3, "lord": "Ke"}},
  ],
  "panchanga": {                     # ключи из PANCHANGA_KEYS
    "tithi": {"value": "29 K. Chaturdashi", "lord": "Sa", "label": "Tithi"},
    "sunrise": {"value": "05:46:42", "lord": None, "label": "Sunrise"},
  },
  "upagrahas": [                     # 11 строк, ключи из UPAGRAHA_KEYS, + "house"
    {"key": "gulika", "name": "Gulika", "degrees": "18°25'35''",
     "degrees_decimal": 18.426389, "sign": "Aries",
     "nakshatra": {...}, "house": 1},
  ],
  "points": {                        # ключи из POINT_KEYS
    "ayanamsa": {"value": "23°36'22''", "label": "Ayanamsa"},
    "drekkana_22": {"value": ["Scorpio 0°-10° (Ma)", "Aquarius 0°-10° (Sa)"], ...},
    "sarpa_drekkana": {"value": ["Su", "Ju"], ...},
  },
  "chakras": [
    {"number": 3, "name": "Manipura", "meaning": "Navel", "element": "Fire",
     "signs": ["Aries", "Scorpio"], "planets": ["Mars", "Sun"],
     "in_sign": ["Ascendant", "Jupiter"]},
  ],
}
```

Списки ключей импортируются:

```python
from vedic_parser.parsers.show_other import (
    LAGNA_KEYS, PANCHANGA_KEYS, POINT_KEYS, UPAGRAHA_KEYS,
)
```

`value` в `points` бывает строкой или списком: список — это либо две строки
(«от Асцендента» и «от Луны»), либо перечисление кодов планет.

### 4.4 `show_dasha` — таблица периодов

```python
api.show_dasha(session, chart, dasha="vimshottari", level=2,
               divisional="D1", cycle=0, current=None)
```

`dasha` — одно из `api.DASHAS`: `vimshottari`, `yogini`, `ashtottari`,
`chara_rao`, `narayana`, `navamsa`. `level`: 1 маха, 2 антар, 3 пратьянтар,
4 сукшма. `current` — момент, вокруг которого вернуть отрезок
(`datetime`, строка `"12.9.2026 0:0"` или `None` = сейчас); `cycle` — шаг целыми
циклами.

```python
{
  "dasha": "vimshottari", "divisional": "D1",
  "kind": "planet",                  # "planet" | "sign"
  "level": 2,                        # выведен из самих строк
  "periods": [
    {"start": "1978-11-23T16:25",    # ISO, из атрибутов строки
     "end": "1981-11-26T11:56",
     "lords": ["Sa", "Sa"],          # коды; [] у знаковых даш
     "labels": ["Saturn", "Saturn"], # подписи сайта
     "start_label": "23 Nov 1978", "start_time": "16:25",
     "age": None},                   # возраст на начало; None до рождения
  ],
}
```

**Знаковые даши (`chara_rao`, `narayana`) кодов не дают** — сайт печатает знаки
обычным текстом, поэтому `kind: "sign"`, `lords: []`, а названия лежат в
`labels` на языке домена. Сопоставление имя→код для текущего языка можно взять
из `show_chart` (там у каждого знака есть и `code`, и `name`).

### 4.5 `show_bala` — силы планет

```python
api.show_bala(session, chart, divisional="D1", full=True)
```

`full=False` дёргает облегчённое действие `show-shad-bala` — только первая
таблица, втрое меньше; остальные части возвращаются пустыми.

```python
{
  "divisional": "D1",
  "shad_bala": [                     # 7 планет (без узлов)
    {"code": "Su", "name": "Sun",
     "components": {                 # ключи из SHAD_BALA_KEYS
       "shad_bala":      {"percent": 124, "virupas": 485.04, "rupas": 8.08},
       "sthana_bala":    {"percent": 120, "virupas": 198.15, "rupas": None},
       "drik_bala":      {"percent": None, "virupas": 4.3,   "rupas": None},
       "yuddha_bala":    {"percent": None, "virupas": None,  "rupas": None},
     }},
  ],
  "varga_bala": [                    # 9 строк: с Раху и Кету
    {"code": "Su", "name": "Sun",
     "vimsopaka": {"shodasha": {"percent": 52, "value": 10.33},
                   "dasha": {...}, "sapta": {...}, "shad": {...}},
     "vaiseshikamsa": {...},
     "vargottama": 2},
  ],
  "aspects": {
    "on_planets": {
      "columns": ["Su", ..., "Ke"],
      "rows": {"Su": ["-", "+", "+", "-", 37, "-", 29, "-", 21]},
      "nature": {"Su": "malefic", "Me": "benefic", ...},
      "totals": {"benefic": [...], "malefic": [...]},
    },
    "on_houses": {"columns": [1, ..., 12], "rows": {...}, "nature": {...},
                  "totals": {...}},
  },
}
```

Заметки:
* Проценты — доля от требуемого минимума, вторая цифра — вирупы; у итоговой
  Шад-балы есть ещё рупы (вирупы/60). Дрик-бала бывает отрицательной.
* В матрицах ячейка — число (вирупы дрик-балы) **или** символ `"+"` / `"-"`, у
  которого величины нет. Строки `totals` — суммы по благодетелям и вредителям;
  символьные ячейки дают ноль.
* `nature` — вердикт этой карты (из цвета подписи строки), совпадает с колонкой
  естественной благотворности в `show_info`. Луна бывает вредителем.

### 4.6 `show_yogas` — образовавшиеся йоги

```python
api.show_yogas(session, chart, divisional="D1")
```

```python
{
  "divisional": "D1",
  "yogas": [                         # только то, что образовалось; длина плавает
    {"name": "Sasa",
     "category": "mahapurusha",      # стабильный ключ, None у незнакомой
     "category_label": "Mahapurusha",# подпись сайта, локализована
     "planets": ["Sa"],              # коды
     "planets_label": "Sa",
     "all_planets": False,           # True, когда сайт пишет "All"
     "effect": "Wandering leader of free spirit",
     "condition": "Saturn in a kendra in own or exaltation sign"},
  ],
}
```

Ключи категорий: `mahapurusha`, `solar`, `lunar`, `nabhasa`, `raja_dhana`,
`other` (таблица `CATEGORY_KEYS` в `parsers/show_yogas.py`). Одна и та же йога
может прийти дважды — отдельно «от Луны»; суффикс локализован, парсер его не
разбирает.

### 4.7 `show_avasthas` — состояния планет

```python
api.show_avasthas(session, chart, divisional="D1")
```

```python
{
  "divisional": "D1",
  "planets": [                       # 9: семь планет + Раху и Кету
    {"code": "Su", "name": "Sun",
     "baladi":    {"state": "Young", "strength_percent": 50, "tone": "orange"},
     "jagradadi": {"state": "Dreaming", "strength_percent": 50, "tone": "orange"},
     "deeptadi": [                   # состояния по настроению + причины
       {"state": "Relaxed, inspired, open and supported", "tone": "green",
        "reason": "Benefic influence: Ju", "planets": ["Ju"], "signs": []},
     ],
     "shayanadi": {
       "state": "Gaining", "tone": "red", "effect": "...",
       "by_letter_group": [          # 5 групп: сила зависит от первого слога имени
         {"letters": ["a", "bh", "chh", "d`", "dh``", "k", "v"],
          "strength_percent": 50, "tone": "orange"},
       ]}},
  ],
  "shayanadi_legend": [              # только встретившиеся состояния
    {"state": "Resting", "count": 1, "tone": "red", "description": "..."},
  ],
  "shayanadi_note": "Note: to determine the strength ...",
}
```

`tone` — цвет, которым сайт пометил вердикт, и он следует за силой: 100% зелёный,
50% оранжевый, 25/15/0% красный. Сумма `count` по легенде равна числу планет.

### 4.8 `show_bhava` — дома бхава-чалиты

```python
api.show_bhava(session, chart, divisional="D1")
```

```python
{
  "divisional": "D1",
  "houses": [                        # 12, по порядку
    {"house": 1,
     "cusp":  {"sign": "Aries",  "degrees": "00°33'53''", "degrees_decimal": 0.564722},
     "start": {"sign": "Pisces", "degrees": "12°48'51''", "degrees_decimal": 12.814167},
     "end":   {"sign": "Aries",  "degrees": "12°48'51''", "degrees_decimal": 12.814167},
     "size": "29°59'58''", "size_decimal": 29.999444,
     "planets": ["As"]},
  ],
  "chart": {...},                    # рисунок в форме show_chart
}
```

**Бхава-балы здесь нет** — сайт отдаёт только геометрию домов и их состав.
Единственная сила уровня домов среди открытых действий — матрица дрик-балы на
дома в `show_bala`. Дома неравные, в сумме 360°.

### 4.9 `show_sade_sati` — проходы Сатурна по Луне

```python
api.show_sade_sati(session, chart)     # варга не передаётся
```

```python
{
  "methods": [                         # два: традиционный и Шри Х.Н. Катве
    {"title": "Sade Sati (traditional)",
     "periods": [                      # по четыре на жизнь
       {"title": "FIRST SADE SATI",
        "start": "2003-04-08T00:00",   # непрерывный основной отрезок
        "end": "2009-09-10T00:00",
        "segments": [
          {"start": "2003-04-08T00:00", "end": "2004-09-06T00:00",
           "description": "Saturn in 12th in Gemini",
           "house": 12,                # цифра из описания
           "within_main": True},       # False — касание вне основного отрезка
        ]}]}
  ],
}
```

Фазы с `within_main: True` стыкуются встык и покрывают основной отрезок
целиком. Даты берутся из атрибутов `data`, а не из подписей.

### 4.10 `get_aspects` / `get_argala` — аспекты и аргала на знак

Единственные два действия с текстовым ответом вместо HTML.

```python
api.get_aspects(session, chart, sign=4, divisional="D1")
api.get_argala(session, chart, sign=1, type=1, divisional="D1")
```

```python
# "Ju Sa|2 8 11"
{"sign": 4, "planets": ["Ju", "Sa"], "signs": [2, 8, 11]}

# "2 12 4 10 11 3"
{"sign": 1, "type": 1, "signs": [2, 12, 4, 10, 11, 3],
 "argala": [2, 4, 11], "virodha": [12, 10, 3], "special": []}
```

`sign` и все числа в ответах — абсолютные номера знаков (Овен = 1). У
`get_aspects` слева планеты, аспектирующие знак, справа — знаки, которые он
аспектирует по раши-дришти. У `get_argala` `type=1` даёт основную аргалу и
вародху, `type=2` — второй набор (пятое число уходит в `special`); другие
значения `type` сайт не понимает и отвечает HTTP 500.

**Ловушка:** шесть позиций всегда классические (2/4/11 и 12/10/3), но для
знака, который занимает Кету, группы `argala` и `virodha` приходят
поменянными местами. Парсер отдаёт группировку сайта как есть.
---

## 5. Как запускать

### Установка

```sh
pip install -e '.[dev]'      # requests, beautifulsoup4, lxml; pytest для тестов
```

### CLI

Печатает JSON в stdout, ошибки в stderr, код возврата 1 при ошибке сайта.

```sh
C="--name Ss --date 07.08.1983 --time 23:00:00 --latitude 55.45 --longitude 37.37 --timezone +4"

vedic-parser session                        # показать cookie и токен
vedic-parser show-info  $C --divisional D9
vedic-parser show-chart $C --style South
vedic-parser show-other $C
vedic-parser show-dasha $C --dasha narayana --level 2
vedic-parser show-bala  $C --shad-bala-only
vedic-parser show-yogas $C
vedic-parser show-avasthas $C
vedic-parser show-bhava $C
vedic-parser show-sade-sati $C
vedic-parser get-aspects $C --sign 4
vedic-parser get-argala  $C --sign 1 --type 1
```

Общие флаги (работают и до, и после подкоманды): `--lang en|ru`, `--base-url`,
`--indent 0` (одна строка), `--session-id` + `--token`, `--html FILE`.

`--html` разбирает сохранённый ответ **без обращения к сети** — параметры карты
при этом всё равно требуются формально, но не используются.

Без установки пакета: `python -m vedic_parser ...`.

### Из Python

```python
from vedic_parser import Chart, Session, api

session = Session()                      # одна сессия на много запросов
chart = Chart(name="Ss", date="07.08.1983", time="23:00:00",
              timezone="+4", latitude="55.45", longitude="37.37")

info = api.show_info(session, chart, divisional="D1")
d9 = api.show_chart(session, chart, divisional="D9")
```

### Разбор без сети

```python
from vedic_parser import parse_show_info

info = parse_show_info(open("saved.html", encoding="utf-8").read())
```

Парсеры принимают и фрагмент от `actions.php`, и целую страницу `analyse.php` —
внутри страницы они сами находят нужный блок (`#natal-info`, `#other`).

### Тесты и вспомогательные скрипты

```sh
python -m pytest                    # 137 тестов, все офлайн
scripts/probe.sh [base-url] [dir]   # сложить сырые ответы всех действий в каталог
python scripts/example_md.py        # перегенерировать docs/example-*.md из фикстур
```

Тесты сети не трогают: парсеры гоняются по записанным фикстурам в
`tests/fixtures/`, сессия — по подменённому HTTP-слою. Новые фикстуры берутся из
`scripts/probe.sh`.

---

## 6. Ограничения и грабли

### Доступ

* **`vedic-horo.com/analyse.php` закрыт Cloudflare-челленджем.** Это единственный
  закрытый путь; `actions.php`, на котором всё построено, открыт. Челлендж мы не
  обходим и обходить не будем.
* **`vedic-horo.ru` периодически отдаёт JS-заглушку** на всех путях: страница
  ставит cookie `__jua_` из JavaScript и перезагружается. Токена там нет, сессию
  не поднять. `Session.open()` распознаёт это и кидает `BootstrapBlocked`.
  Варианты: работать через `.com` или передать пару из браузера:

  ```python
  session = Session(lang="ru")
  session.adopt(session_id="<PHPSESSID из браузера>", token="<token_security>")
  ```

  Оба значения берутся из одной загрузки страницы и работают только вместе. При
  истечении такого токена сессия не обновит его молча, а скажет об этом.
* **Платное недоступно анонимно**: транзиты, совместимость, варшапхала, мухурта
  отвечают `403 Access Denied` → `AccessDenied`.
* **Текстовые интерпретации есть только на `.ru`.** На `.com` тот же запрос
  отвечает «Sorry, no information in English yet». Отдельного тула для них пока
  нет (см. `docs/recon.md`, §5).

### Данные

* **Координаты — градусы и минуты**, не десятичные (см. §2).
* **`show_info` для варги ≠ D1 не отдаёт знак этой варги**: колонка «Раши»
  остаётся натальным D1-знаком, «Навамша» — D9-знаком; пересчитываются только
  градусы, дом, бинду и балы. Знак в варге бери из `show_chart`. В `show_other`
  знаки, наоборот, от варги зависят.
* **У всех варг кроме D1 в `show_info` нет накшатры** — `nakshatra: None`.
* **Границы даш непрерывны только до минуты**: время приходит как `HH:MM`, и на
  стыках мах стороны иногда округляются по-разному (конец 13:20 против начала
  13:21). Не строй логику на точном равенстве `end == start`.
* **Объём даш растёт быстро**: вимшоттари level 1 — 9 строк, level 2 — 81,
  level 3 — 729 (~175 КБ). Уровень 4 запрашивай осознанно.
* **`show_other` опознаётся по позиции.** В этом ответе нет ни классов, ни
  `href`, ни tooltip'ов — только текст. Если сайт изменит состав строк (а он
  зависит и от настроек аккаунта), парсер не станет врать: `key` станет `None`,
  а `name` останется. Проверяй `key` перед тем, как на него полагаться.
* **`divisional` из разметки — не то, что запрошено** (см. §3). Функции `api.*`
  подменяют его на запрошенное значение; голые `parse_*` — нет.

### Нагрузка и вежливость

* Каждый вызов заставляет сайт считать карту. Заявленная нагрузка — 35 000 карт
  в день; **кэшируй ответы** вместо повторных запросов и не гоняй циклы по
  варгам без нужды.
* Одна `Session` переиспользует cookie и TCP-соединение — создавай её один раз на
  серию запросов, а не на каждый.
* Ретраев внутри нет. Нужны — передай свой `requests.Session` с
  `HTTPAdapter(max_retries=...)`.

### Исключения

```python
from vedic_parser import (
    VedicHoroError,     # базовое
    TokenNotFound,      # на странице не нашёлся token_security
    BootstrapBlocked,   # домен отдал JS-заглушку (наследник TokenNotFound)
    AccessDenied,       # 403: действие требует платного аккаунта
)
```

Парсеры на чужом HTML кидают `ValueError` с объяснением, что ожидали найти.

---

## 7. Чего пока нет

Реализованы `session` и десять действий: `show-info`, `show-chart`, `show-other`,
`show-dasha`, `show-bala`, `show-yogas`, `show-avasthas`, `show-bhava`,
`show-sade-sati`, `get-aspects`/`get-argala`.

Из бесплатных и доступных анонимно остаются `show-vargas`,
`show-current-periods`, `first-house`, `show-chart-big`/`show-chart-overlay` и
текстовые интерпретации (`windows/analyse_interpretation.php`, только на `.ru`).
Все они разведаны и описаны в `docs/recon.md`, §4–5. Платное (транзиты,
совместимость, варшапхала, мухурта) закрыто `403` и без аккаунта недоступно.

Отдельно: **бхава-балы у сайта нет вообще** — `show-bhava` отдаёт только
геометрию домов. Единственная сила уровня домов среди открытых действий —
матрица дрик-балы на дома в `show-bala`.

Новый парсер добавляется по одной схеме:

1. Снять фикстуру (`scripts/probe.sh`), положить в `tests/fixtures/` с именем
   `<действие>-<язык>-<параметры>.html`.
2. `vedic_parser/parsers/<действие>.py` — чистая функция `parse_<действие>(html)`,
   общие мелочи брать из `parsers/_html.py`. Коды читать из классов и `href`,
   по локализованному тексту не ветвиться.
3. Экспортировать в `parsers/__init__.py` и в `vedic_parser/__init__.py`.
4. Функция в `api.py` (запрос + разбор + подстановка запрошенных параметров) и
   подкоманда в `cli.py`.
5. Тесты в `tests/test_<действие>.py`: английская и русская фикстуры, сверка
   значений между языками, сверка с другими действиями по той же карте.
6. Раздел в `scripts/example_md.py` → новый `docs/example-<действие>.md`.
