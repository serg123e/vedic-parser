# Пример данных: `show-chart`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-chart --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4 --divisional D1
```

Ответ: `style`, `divisional`, `chart` (эхо введённых данных), `houses` — всегда 12 домов по порядку, и `planets` — то же самое, но плоским списком по планетам (выводится из `houses`).

## 1. Один дом целиком

4-й дом этой карты — стеллиум из трёх планет плюс два аспекта:

```json
{
  "house": 4,
  "sign": {
    "number": 4,
    "code": "Cn",
    "name": "Cancer"
  },
  "planets": [
    {
      "code": "Ma",
      "degree": 2,
      "degree_label": "02°",
      "retrograde": false
    },
    {
      "code": "Mo",
      "degree": 6,
      "degree_label": "06°",
      "retrograde": false
    },
    {
      "code": "Su",
      "degree": 21,
      "degree_label": "21°",
      "retrograde": false
    }
  ],
  "aspects": [
    "Ju",
    "Sa"
  ]
}
```

## 2. Все двенадцать домов (D1, North)

| Дом | Знак | № | Название | Планеты | Аспектируют |
|---|---|---|---|---|---|
| 1 | Ar | 1 | Aries | As 00° | Sa |
| 2 | Ta | 2 | Taurus | — | Ju |
| 3 | Ge | 3 | Gemini | Ra 00° R | — |
| 4 | Cn | 4 | Cancer | Ma 02°, Mo 06°, Su 21° | Ju, Sa |
| 5 | Le | 5 | Leo | Ve 15° R, Me 15° | — |
| 6 | Vi | 6 | Virgo | — | — |
| 7 | Li | 7 | Libra | Sa 05° | Ma |
| 8 | Sc | 8 | Scorpio | Ju 07° | — |
| 9 | Sg | 9 | Sagittarius | Ke 00° R | Sa |
| 10 | Cp | 10 | Capricorn | — | Su, Mo, Ma |
| 11 | Aq | 11 | Aquarius | — | Ma, Me, Ve |
| 12 | Pi | 12 | Pisces | — | Ju |

И то же самое плоским списком — `planets`:

| Код | Дом | Знак | № знака | Градус | Ретро |
|---|---|---|---|---|---|
| As | 1 | Ar | 1 | 0 | нет |
| Su | 4 | Cn | 4 | 21 | нет |
| Mo | 4 | Cn | 4 | 6 | нет |
| Ma | 4 | Cn | 4 | 2 | нет |
| Me | 5 | Le | 5 | 15 | нет |
| Ju | 8 | Sc | 8 | 7 | нет |
| Ve | 5 | Le | 5 | 15 | да |
| Sa | 7 | Li | 7 | 5 | нет |
| Ra | 3 | Ge | 3 | 0 | да |
| Ke | 9 | Sg | 9 | 0 | да |

Градусы здесь целые — в рисунке карты сайт больше не показывает. Точные, до секунды, есть в `show-info` (`degrees_decimal`).

## 3. Два стиля — одна структура

Разметка North и South не имеет ничего общего: в North двенадцать `div.house` в порядке домов, и каждый называет свой знак; в South — `table.chart` с ячейками в порядке знаков, и каждая называет свой дом. Парсер приводит оба к одному виду, поэтому `--style` влияет только на то, что отдаёт сервер:

|  | North (D1) | South (D9) |
|---|---|---|
| `style` | `north` | `south` |
| разметка | `div.chart-north` + `div.house`×12 | `table.chart` + `td.houses`×12 |
| порядок в HTML | по домам | по знакам (переупорядочивается) |
| аспекты | `<u>Sa</u>` | текст в `div.aspects` |
| 1-й дом | As | Ke, As |

## 4. Другая варга: D9 (South)

```sh
vedic-parser show-chart ... --divisional D9 --style South
```

| Дом | Знак | Планеты | Аспектируют |
|---|---|---|---|
| 1 | Aries | Ke 03° R, As 05° | — |
| 2 | Taurus | — | Ju, Sa |
| 3 | Gemini | — | — |
| 4 | Cancer | Ma 23° | Su |
| 5 | Leo | Ve 20° R, Me 22°, Mo 29° | Sa |
| 6 | Virgo | Ju 08° | — |
| 7 | Libra | Ra 03° R | Ma |
| 8 | Scorpio | Sa 17° | — |
| 9 | Sagittarius | — | — |
| 10 | Capricorn | Su 09° | Ma, Ju, Sa |
| 11 | Aquarius | — | Mo, Ma, Me, Ve |
| 12 | Pisces | — | Ju |

Именно отсюда берутся знаки варги — в `show-info` для D9 колонка «Раши» показывает натальный знак, а не D9 (см. `docs/example-show-info.md`, §5).

## 5. Русский вариант

Коды знаков латиницей, названия — как на сайте:

| Дом | Код | Название | Планеты |
|---|---|---|---|
| 1 | Ar | Овен | As |
| 2 | Ta | Телец | — |
| 3 | Ge | Близнецы | Ra |
| 4 | Cn | Рак | Ma, Mo, Su |
| 5 | Le | Лев | Ve, Me |
| 6 | Vi | Дева | — |

## 6. Сверка с `show-info`

Рисунок и таблица — две проекции одного расчёта, и они сходятся: для всех десяти тел знак, дом, ретроградность и целая часть градуса совпадают (это проверяется тестом `test_agrees_with_show_info_on_the_same_chart`).

Чего в `show-chart` нет: аспектов планет на планеты (только на дома), аргалы, накшатр, бал. Аспекты и аргала одного дома — отдельные действия `get-aspects` / `get-argala`, они отдают компактный текст вида `Sa|5 8 11`.

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
