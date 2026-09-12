# Пример данных: `show-yogas`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-yogas --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4
```

Ответ — только те йоги, которые в карте **образовались**; длина списка зависит от карты (здесь 32, на других картах попадалось от 26 до 42). Разметка — голый набор `<tr>` без таблицы вокруг.

## 1. Одна запись

```json
{
  "name": "Sasa",
  "category": "mahapurusha",
  "category_label": "Mahapurusha",
  "planets": [
    "Sa"
  ],
  "planets_label": "Sa",
  "all_planets": false,
  "effect": "Wandering leader of free spirit",
  "condition": "Saturn in a kendra in own or exaltation sign"
}
```

## 2. Категории

Категория лежит в атрибуте строки `type`, но переводится вместе с интерфейсом, поэтому парсер приводит её к стабильному ключу; незнакомую категорию он не угадывает — `category` станет `null`, а подпись сохранится в `category_label`.

| `category` | en | ru | Сколько в этой карте |
|---|---|---|---|
| `mahapurusha` | Mahapurusha | Махапуруша | 2 |
| `solar` | Solar | Солнечные | 1 |
| `lunar` | Lunar | Лунные | 2 |
| `nabhasa` | Nabhasa | Набхаса | 1 |
| `raja_dhana` | Raja + Dhana | Раджа + Дхана | 15 |
| `other` | Other | Другие | 11 |

## 3. Все йоги карты

| Йога | Категория | Планеты | Эффект | Условие |
|---|---|---|---|---|
| Sasa | `mahapurusha` | Sa | Wandering leader of free spirit | Saturn in a kendra in own or exaltation sign |
| Sasa (from Moon) | `mahapurusha` | Sa | Wandering leader of free spirit | Saturn in a kendra in own or exaltation sign from Moon |
| Vesi | `solar` | Me, Ve | Balanced, truthful and happy | Planets other than Moon in 2nd from Sun |
| Chandra-Mangala | `lunar` | Mo, Ma | Worldly wise and materially successful | Moon and Mars together or in mutual 7ths |
| Sunapha | `lunar` | Me, Ve | Intelligent, wealthy and famous | Planets other than Sun in 2nd from Moon |
| Kedara | `nabhasa` | All | Happy, wealthy and helpful | Seven planets in four rasis |
| Kala-Amrita | `other` | All | Restrictions, extremes and suffering, inclines to spirituality, rejecting materialism | 7 planets are placed in between the lunar nodes in the direction from Rahu to Ketu |
| Parvata | `other` | Mo | Fortunate, charitable, eloquent, easy-going, famous | Dispositor of Lagna lord in own sign or exaltation and in a kendra or trine |
| Kahala | `other` | Mo, Sa | Strong, bold, cunning, leads a large army | The 4th lord is in own or exaltation sign conjoined or aspected by 10th lord |
| Kahala | `other` | Mo | Strong, bold, cunning, leads a large army | Dispositor of the dispositor of Lagna lord in own sign or exaltation and in a kendra or trine |
| Trilochana | `other` | Su, Mo, Ma | Victorious over enemies, wealthy, intelligent, long-lived | Sun, Moon and Mars in mutual trines |
| Raja | `raja_dhana` | Ma | Successful and high achievements | Kendra lord in a trine or trine lord in a kendra |
| Raja | `raja_dhana` | Su | Successful and high achievements | Kendra lord in a trine or trine lord in a kendra |
| Raja | `raja_dhana` | Ve | Successful and high achievements | Kendra lord in a trine or trine lord in a kendra |
| Raja | `raja_dhana` | Ma, Mo | Successful and high achievements | Conjunction, aspect or exchange of kendra and trine lords |
| Raja | `raja_dhana` | Su, Ma | Successful and high achievements | Conjunction, aspect or exchange of kendra and trine lords |
| Raja | `raja_dhana` | Su, Mo | Successful and high achievements | Conjunction, aspect or exchange of kendra and trine lords |
| Raja | `raja_dhana` | Ma, Sa | Successful and high achievements | Conjunction, aspect or exchange of kendra and trine lords |
| Raja | `raja_dhana` | Su, Mo, Ma | Successful and high achievements | AK and PK together, 1st and 5th lords together |
| Raja | `raja_dhana` | Sa | Successful and high achievements | The 10th lord aspects Lagna from own or exaltation sign |
| Raja | `raja_dhana` | Me, Ju, Ve | Will become a king or an equal | Benefics in 2nd, 4th and 5th from AK or Lagna lord |
| Raja | `raja_dhana` | Su, Ma | Will become a king | The 5th lord joins 1st or 9th lord in 1st, 4th or 10th |
| Viparita Raja | `raja_dhana` | Ju | Success after pressures or losses | The 12th lord in 6th or 8th |
| Raja Sambandha | `raja_dhana` | Me | Will become a famous minister | AmK in a trine |
| Raja Sambandha | `raja_dhana` | Su, Ma | A king`s friend | Lagna lord or AK with 5th lord in a kendra or trine |
| Dhana | `raja_dhana` | Ma, Su | Wealth and prosperity | Conjunction, aspect or exchange of trine, 2nd and 11th lords |
| Daridra | `other` | Ju | Poverty | Lord of the 1st, 2nd, 5th, 9th or 11th in dusthana |
| Daridra | `other` | Me | Poverty | Dusthana lord in the 1st, 2nd, 5th, 9th or 11th |
| Daridra | `other` | Ve, Me | Poverty | Conjunction, aspect or exchange of 1st, 2nd, 5th, 9th or 11th and dusthana lords |
| Daridra | `other` | Su, Ma | Poverty | Conjunction, aspect or exchange of 1st, 2nd, 5th, 9th or 11th and dusthana lords |
| Daridra | `other` | Ma, Sa | Poverty | Conjunction, aspect or exchange of 1st, 2nd, 5th, 9th or 11th and dusthana lords |
| Neecha Bhanga | `other` | Ma | Cancellation of debilitation of the planet | - Debilitated planet in a kendra from Moon or Lagna - Dispositor of debilitated planet in a kendra from Moon or Lagna - Lord of the sign of exaltation of the falling planet in kendra from Moon or Lagna |

Йога, которая образуется и от Асцендента, и от Луны, приходит двумя строками («Sasa» и «Sasa (from Moon)») — суффикс локализован, поэтому разбирать его парсер не пытается.

`All` в колонке планет означает «все планеты» и остаётся английским даже в русском ответе — это стабильный токен, отсюда булево `all_planets`.

## 4. Русский ответ

Строка в строку та же, отличаются только тексты:

| `category` | Планеты | en | ru |
|---|---|---|---|
| `mahapurusha` | Sa | Sasa | Шаша |
| `mahapurusha` | Sa | Sasa (from Moon) | Шаша (от Луны) |
| `solar` | Me, Ve | Vesi | Веси |
| `lunar` | Mo, Ma | Chandra-Mangala | Чандра-Мангала |
| `lunar` | Me, Ve | Sunapha | Сунапха |
| `nabhasa` | All | Kedara | Кедара |

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
