# Пример данных: `show-other`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-other --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4
```

Это вкладка «Разное» — пять разнородных таблиц в одном ответе: `lagnas`, `panchanga`, `upagrahas`, `points`, `chakras`.

**Важно про разметку:** здесь, в отличие от остальных действий, нет ни классов, ни `href`, ни tooltip'ов — только текст. Поэтому строки и колонки опознаются по позиции, а канонические ключи (`bhava_lagna`, `gulika`, `ayanamsa`, …) приделывает парсер. Подписи сайта сохраняются рядом в `name` / `label`.

## 1. Особые лагны и спхуты

15 строк в фиксированном порядке:

| Ключ | Название | Градусы | Дец. | Знак | Накшатра | Пада | Упр. |
|---|---|---|---|---|---|---|---|
| `bhava_lagna` | Bhava Lagna | 08°43'54'' | 8.731667 | Aries | Ashvini | 3 | Ke |
| `hora_lagna` | Hora Lagna | 27°03'24'' | 27.056667 | Sagittarius | Uttarashadha | 1 | Su |
| `ghatika_lagna` | Ghatika Lagna | 22°01'54'' | 22.031667 | Aquarius | Purvabhadra | 1 | Ju |
| `sri_lagna` | Sree Lagna | 29°42'51'' | 29.714167 | Gemini | Punarvasu | 3 | Ju |
| `indu_lagna` | Indu Lagna | 06°38'11'' | 6.636389 | Aquarius | Dhanishtha | 4 | Ma |
| `varnada_lagna` | Varnada Lagna | 00°33'53'' | 0.564722 | Capricorn | Uttarashadha | 2 | Su |
| `paka_lagna` | Paka Lagna | 02°33'32'' | 2.558889 | Cancer | Punarvasu | 4 | Ju |
| `karakamsa_lagna` | Karakamsa Lagna | 09°51'07'' | 9.851944 | Capricorn | Uttarashadha | 4 | Su |
| `pranapada` | Pranapada | 26°54'24'' | 26.906667 | Scorpio | Jyeshtha | 4 | Me |
| `kunda` | Kunda | 15°44'04'' | 15.734444 | Taurus | Rohini | 2 | Mo |
| `bhrigu_bindu` | Bhrigu Bindu | 18°30'55'' | 18.515278 | Gemini | Ardra | 4 | Ra |
| `bija_sphuta` | Beeja Sphuta | 14°16'46'' | 14.279444 | Cancer | Pushya | 4 | Sa |
| `kshetra_sphuta` | Kshetra Sphuta | 16°47'44'' | 16.795556 | Taurus | Rohini | 3 | Mo |
| `yogi_sphuta` | Yogi Sphuta | 01°03'49'' | 1.063611 | Aquarius | Dhanishtha | 3 | Ma |
| `avayogi_sphuta` | Avayogi Sphuta | 07°43'47'' | 7.729722 | Leo | Magha | 3 | Ke |

Одна запись как JSON:

```json
{
  "key": "bhava_lagna",
  "name": "Bhava Lagna",
  "degrees": "08°43'54''",
  "degrees_decimal": 8.731667,
  "sign": "Aries",
  "nakshatra": {
    "name": "Ashvini",
    "pada": 3,
    "lord": "Ke"
  }
}
```

## 2. Панчанга

Семь значений момента рождения. Титхи, карана и йога приходят с управителем через запятую — парсер его отделяет в `lord` (и признаёт только код планеты, чтобы не откусить часть названия):

| Ключ | Подпись | Значение | Управитель |
|---|---|---|---|
| `sunrise` | Sunrise | 05:46:42 | — |
| `sunset` | Sunset | 21:22:39 | — |
| `hora` | Hora | Moon | — |
| `vara` | Vara | Sun | — |
| `tithi` | Tithi | 29 K. Chaturdashi | Sa |
| `karana` | Karana | Shakuni | — |
| `yoga` | Yoga | Siddhi | Ma |

## 3. Упаграхи

11 теневых точек — как лагны, но ещё с домом:

| Ключ | Название | Градусы | Знак | Накшатра | Пада | Дом |
|---|---|---|---|---|---|---|
| `dhuma` | Dhuma | 04°25'41'' | Sagittarius | Mula | 2 | 9 |
| `vyatipata` | Vyatipata | 25°34'21'' | Cancer | Aslesha | 3 | 4 |
| `parivesha` | Parivesha | 25°34'21'' | Capricorn | Dhanishtha | 1 | 10 |
| `indrachapa` | Indrachapa | 04°25'41'' | Gemini | Mrigashira | 4 | 3 |
| `upaketu` | Upaketu | 21°05'41'' | Gemini | Punarvasu | 1 | 3 |
| `gulika` | Gulika | 18°25'35'' | Aries | Bharani | 2 | 1 |
| `mandi` | Mandi | 03°42'15'' | Taurus | Krittika | 3 | 2 |
| `kala` | Kala | 10°41'03'' | Gemini | Ardra | 2 | 3 |
| `mrityu` | Mrityu | 04°36'53'' | Cancer | Pushya | 1 | 4 |
| `ardhaprahara` | Ardhaprahara | 15°20'19'' | Cancer | Pushya | 4 | 4 |
| `yamagantaka` | Yamaghantaka | 12°48'34'' | Aquarius | Satabhisha | 2 | 11 |

## 4. Отдельные точки

Ячейки бывают многострочными (одно и то же от Асцендента и от Луны — приходит списком) и перечислением кодов планет (тоже списком):

| Ключ | Подпись | Значение |
|---|---|---|
| `ayanamsa` | Ayanamsa | 23°36'22'' |
| `sahayogi` | Sahayogi | Saturn |
| `badhaka` | Badhaka | Aquarius (Sa/Ra) |
| `dagdha_rasi` | Dagdha Rasi | Gemini, Virgo<br>Sagittarius, Pisces |
| `drekkana_22` | 22nd Drekkana from As/Mo | Scorpio 0°-10° (Ma)<br>Aquarius 0°-10° (Sa) |
| `navamsa_64` | 64th Navamsa from As/Mo | Scorpio 0°-3°20' (Mo)<br>Aquarius 3°20'-6°40' (Ma) |
| `sarpa_drekkana` | Sarpa Drekkana | Su<br>Ju |
| `visha_navamsa` | Visha Navamsa | As<br>Me<br>Ve<br>Ke |

## 5. Чакры

Номер и название сайт кладёт в одну ячейку (`3 | Manipura`), парсер их делит:

| № | Название | Значение | Элемент | Знаки | Планеты | Что в знаке |
|---|---|---|---|---|---|---|
| 1 | Muladhara | Root | Earth | Capricorn, Aquarius | Saturn, Mars | — |
| 2 | Swadhisthana | Sexual | Water | Sagittarius, Pisces | Jupiter, Venus | Ketu |
| 3 | Manipura | Navel | Fire | Aries, Scorpio | Mars, Sun | Ascendant, Jupiter |
| 4 | Anahata | Heart | Air | Taurus, Libra | Venus, Moon, Saturn | Saturn |
| 5 | Vishuddha | Throat | Ether | Gemini, Virgo | Mercury | Rahu |
| 6 | Ajna | Third eye | All elements | Cancer, Leo | Moon, Sun, Jupiter | Sun, Moon, Mars, Mercury, Venus |

## 6. Варга и язык

`--divisional D9` пересчитывает лагны и упаграхи — и, в отличие от `show-info`, **знак здесь тоже от варги**. Бхава Лагна: D1 — 08°43'54'' Aries, D9 — 18°35'06'' Gemini (это ровно навамша от первой). Панчанга и айянамша от варги не зависят: это свойства момента, а не карты.

Русский ответ даёт те же ключи, меняются подписи:

| Ключ | en | ru | Градусы (совпадают) |
|---|---|---|---|
| `bhava_lagna` | Bhava Lagna | Бхава Лагна | 08°43'54'' |
| `hora_lagna` | Hora Lagna | Хора Лагна | 27°03'24'' |
| `ghatika_lagna` | Ghatika Lagna | Гхатика Лагна | 22°01'54'' |
| `sri_lagna` | Sree Lagna | Шри Лагна | 29°42'51'' |
| `indu_lagna` | Indu Lagna | Инду Лагна | 06°38'11'' |

Титхи по-русски: `29 К. Чатурдаши` + управитель `Sa` — код остаётся латиницей.

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
