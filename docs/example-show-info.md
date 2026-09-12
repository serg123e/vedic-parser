# Пример данных: `show-info`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-info --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4
```

Ответ — один JSON-объект: `divisional`, `from`, `planets` (10 записей) и `ashtakavarga`.

## 1. Одна запись целиком

Так выглядит элемент `planets` без сокращений — Венера, ретроградная, в планетной войне:

```json
{
  "code": "Ve",
  "name": "Venus",
  "retrograde": true,
  "karaka": "BK",
  "degrees": "15°35'04''",
  "degrees_decimal": 15.584444,
  "rasi": {
    "code": "Le",
    "name": "Leo",
    "dignity": "Enemy"
  },
  "navamsa": "Leo",
  "nakshatra": {
    "code": "PPh",
    "name": "Purvaphalguni",
    "pada": 1,
    "lord": "Ve"
  },
  "relationship": "Neutral",
  "house": 5,
  "lords": [
    {
      "house": 2,
      "in_house": 5,
      "co_lord": false,
      "label": "2nd"
    },
    {
      "house": 7,
      "in_house": 5,
      "co_lord": false,
      "label": "7th"
    }
  ],
  "functional_beneficence": {
    "code": "N-",
    "description": "Neutral with a touch of malefic. 33% malefic"
  },
  "natural_beneficence": {
    "code": "B",
    "description": "Benefic. 100% benefic"
  },
  "shad_bala": 133,
  "bindu": {
    "sav": 28,
    "bav": 5
  },
  "position": [
    {
      "code": "V",
      "description": "Vargottama. The same sign in Navamsa strengthens the planet as if it were in own sign"
    }
  ],
  "planetary_war": "✓"
}
```

## 2. Все десять тел (D1 Раши)

| Код | Планета | Град. | Дец. | Знак | Достоинство | Навамша | Накшатра | Пада | Упр. | Отнош. | Дом | Управитель | ФБ | ЕБ | Шад-бала | САВ/БАВ | Положение | ПВ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| As | Ascendant | 00°33'53'' | 0.564722 | Aries | — | Aries | Ashvini | 1 | Ke | — | — | — | — | — | — | 35 / 5 | G1°, S, MB, V | — |
| Su | Sun | 21°05'41'' | 21.094722 | Cancer | Friend | Capricorn | Aslesha | 2 | Me | Neutral | 4 | 5 | B | M | 124% | 26 / 7 | ZDB | — |
| Mo | Moon | 06°38'11'' | 6.636389 | Cancer | Own sign | Leo | Pushya | 1 | Sa | Own sign | 4 | 4 | N+ | M | 163% | 26 / 1 | DB | — |
| Ma | Mars | 02°33'32'' | 2.558889 | Cancer | Debilitation | Cancer | Punarvasu | 4 | Ju | Debilitation, 26° | 4 | 1, 8 | B- | M+ | 134% | 26 / 3 | ZDB, V, PN | — |
| Me | Mercury | 15°48'08'' | 15.802222 | Leo | Friend | Leo | Purvaphalguni | 1 | Ve | Big friend | 5 | 3, 6 | M+ | B | 73% | 28 / 5 | V | ✕ |
| Ju | Jupiter | 07°36'02'' | 7.600556 | Scorpio | Friend | Virgo | Anuradha | 2 | Sa | Neutral | 8 | 9, 12 | B- | B+ | 94% | 18 / 3 | HM, PN | — |
| Ve | Venus (R) | 15°35'04'' | 15.584444 | Leo | Enemy | Leo | Purvaphalguni | 1 | Ve | Neutral | 5 | 2, 7 | N- | B | 133% | 28 / 5 | V | ✓ |
| Sa | Saturn | 05°14'05'' | 5.234722 | Libra | Exaltation | Scorpio | Chitra | 4 | Ma | Exaltation, 15° | 7 | 10, 11 | M | M+ | 175% | 25 / 2 | DB | — |
| Ra | Rahu (R) | 00°23'39'' | 0.394167 | Gemini | Moolatrikona | Libra | Mrigashira | 3 | Ma | Moolatrikona | 3 | со-11 | M | M | — | 31 / — | S | — |
| Ke | Ketu (R) | 00°23'39'' | 0.394167 | Sagittarius | Moolatrikona | Aries | Mula | 1 | Ke | Moolatrikona | 9 | со-8 | M | M | — | 28 / — | G0°, S | — |

Колонка `karaka` (Чара Караки) вынесена отдельно, чтобы таблица не расползалась:

| As | Su | Mo | Ma | Me | Ju | Ve | Sa | Ra | Ke |
|---|---|---|---|---|---|---|---|---|---|
| — | AK | PK | DK | AmK | MK | BK | GK | — | — |

Коды: `As` асцендент, `Su Mo Ma Me Ju Ve Sa` планеты, `Ra Ke` узлы. Знаки — `Ar Ta Ge Cn Le Vi Li Sc Sg Cp Aq Pi`. Всё это читается из CSS-классов и `href`, поэтому одинаково для обоих языков.

## 3. Расшифровки, которые приходят в tooltip'ах

Сокращения в колонках ФБ / ЕБ / Положение сайт поясняет в атрибуте `title` — парсер их сохраняет в `description`:

| Код | Значение |
|---|---|
| `G1°` | Gandanta. The closer to the border of the water/fire sign - the stronger the defeat |
| `S` | Sandhi. The closer to the border between the signs - the stronger the defeat |
| `MB` | Mrityu Bhaga. The live indicators and health are destroying, a touch of the malefic is added |
| `V` | Vargottama. The same sign in Navamsa strengthens the planet as if it were in own sign |
| `B` | Benefic. 100% benefic |
| `M` | Malefic. 100% malefic |
| `ZDB` | Zero Dig Bala. The house that prevents to the full potential of the planet |
| `N+` | Neutral with a touch of benefic. 33% benefic |
| `DB` | Dig Bala. The house that contributes to the full potential of the planet |
| `B-` | Benefic with a touch of malefic. 67% benefic, 33% malefic |
| `M+` | Strong malefic. 150% malefic |
| `PN` | Pushkara Navamsa. Additional energy for the manifestation of favorable qualities (weaker than PB) |
| `B+` | Strong benefic. 150% benefic |
| `HM` | Hemmed by malefics. The more malefics and the stronger they are - the stronger the defeat |
| `N-` | Neutral with a touch of malefic. 33% malefic |
| `G0°` | Gandanta. The closer to the border of the water/fire sign - the stronger the defeat |

## 4. Аштакаварга

`first_house_sign` = 1 → в 1-м доме Ar, дальше по порядку. Значения идут домами 1…12.

| Ряд | 1<br>Ar | 2<br>Ta | 3<br>Ge | 4<br>Cn | 5<br>Le | 6<br>Vi | 7<br>Li | 8<br>Sc | 9<br>Sg | 10<br>Cp | 11<br>Aq | 12<br>Pi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **САВ** | **35** | **38** | **31** | **26** | **28** | **29** | **25** | **18** | **28** | **31** | **27** | **21** |
| БАВ As | 5 | 5 | 4 | 3 | 4 | 7 | 3 | 3 | 6 | 3 | 2 | 4 |
| БАВ Su | 6 | 5 | 3 | 7 | 3 | 3 | 4 | 1 | 2 | 6 | 4 | 4 |
| БАВ Mo | 4 | 6 | 4 | 1 | 4 | 5 | 3 | 4 | 6 | 3 | 6 | 3 |
| БАВ Ma | 5 | 4 | 4 | 3 | 3 | 4 | 4 | 1 | 3 | 5 | 2 | 1 |
| БАВ Me | 7 | 6 | 5 | 4 | 5 | 3 | 6 | 4 | 4 | 4 | 3 | 3 |
| БАВ Ju | 5 | 7 | 3 | 3 | 6 | 6 | 3 | 3 | 5 | 7 | 5 | 3 |
| БАВ Ve | 3 | 6 | 8 | 4 | 5 | 4 | 3 | 4 | 5 | 2 | 4 | 4 |
| БАВ Sa | 5 | 4 | 4 | 4 | 2 | 4 | 2 | 1 | 3 | 4 | 3 | 3 |

САВ — сумма семи планетных БАВ; БАВ асцендента показан рядом, но в сумму не входит (проверка по 1-му дому: 6 + 4 + 5 + 7 + 5 + 3 + 5 = 35).

## 5. Другая варга: `--divisional D9`

```sh
vedic-parser show-info ... --divisional D9
```

Тут есть ловушка. Пересчитываются `degrees`, `house`, бинду и балы, а колонка «Раши» **остаётся натальным D1-знаком**, «Навамша» — D9-знаком. Знака планеты в самой варге в этом ответе нет: за ним — в `show-chart` (для D9 он совпадает с колонкой «Навамша»). Плюс у всех варг кроме D1 нет колонки накшатры, поэтому `nakshatra: null`.

| Код | Планета | Град. в D9 | Раши (D1!) | Навамша (= знак в D9) | Дом в D9 | Накшатра | САВ/БАВ | Шад-бала |
|---|---|---|---|---|---|---|---|---|
| As | Ascendant | 05°04'55'' | Aries | Aries | — | — | 32 / 4 | — |
| Su | Sun | 09°51'07'' | Cancer | Capricorn | 10 | — | 35 / 7 | 124% |
| Mo | Moon | 29°43'37'' | Cancer | Leo | 5 | — | 27 / 5 | 163% |
| Ma | Mars | 23°01'41'' | Cancer | Cancer | 4 | — | 31 / 4 | 134% |
| Me | Mercury | 22°13'05'' | Leo | Leo | 5 | — | 27 / 5 | 73% |
| Ju | Jupiter | 08°24'11'' | Scorpio | Virgo | 6 | — | 27 / 6 | 94% |
| Ve | Venus (R) | 20°15'32'' | Leo | Leo | 5 | — | 27 / 5 | 133% |
| Sa | Saturn | 17°06'43'' | Libra | Scorpio | 8 | — | 23 / 2 | 175% |
| Ra | Rahu (R) | 03°32'46'' | Gemini | Libra | 7 | — | 25 / — | — |
| Ke | Ketu (R) | 03°32'46'' | Sagittarius | Aries | 1 | — | 32 / — | — |

Аштакаварга тоже своя: САВ D9 = `[32, 28, 38, 31, 27, 27, 25, 23, 23, 35, 27, 21]`.

## 6. Русские подписи: `--lang ru`

Структура та же, меняются только человекочитаемые поля; коды остаются латиницей:

| Код | Планета | Град. | Знак | Накшатра | Пада | Дом | Управитель | ФБ | Положение |
|---|---|---|---|---|---|---|---|---|---|
| As | Асцендент | 00°33'53'' | Овен | Ашвини | 1 | — | — | — | Г1°, С, МБ, В |
| Su | Солнце | 21°05'41'' | Рак | Ашлеша | 2 | 4 | 5 | Б | НДБ |
| Mo | Луна | 06°38'11'' | Рак | Пушья | 1 | 4 | 4 | Н+ | ДБ |
| Ma | Марс | 02°33'32'' | Рак | Пунарвасу | 4 | 4 | 1, 8 | Б- | НДБ, В, ПН |
| Me | Меркурий | 15°48'08'' | Лев | Пурвапхалгуни | 1 | 5 | 3, 6 | В+ | В |

Пример расшифровки по-русски: `Н-` — Нейтральная с оттенком вредителя. 33% вредитель.

## 7. Чего в этом ответе нет

`show-info` — это только таблица планет и аштакаварга. Остальное живёт в других действиях (см. `docs/recon.md`): сама карта с домами — `show-chart`, панчанга и упаграхи — `show-other`, даши — `show-dasha`, компоненты Шад-балы — `show-bala`, авастхи — `show-avasthas`, йоги — `show-yogas`.

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
