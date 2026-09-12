# Пример данных: `show-avasthas`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-avasthas --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4
```

Состояния планет: `planets` (9 записей — с узлами), `shayanadi_legend` и `shayanadi_note`. В ответе три таблицы: авастхи по возрасту и пробуждённости, авастхи по настроению с причинами, шаянади по деятельности.

Вердикт сайт кодирует цветом, и цвет строго следует за силой: 100% — зелёный, 50% — оранжевый, 25/15/0% — красный. Парсер отдаёт класс как `tone`, ничего не переосмысливая.

## 1. Балади и джаградади

| Планета | Балади (по возрасту) | Сила | Джаградади (по пробуждённости) | Сила |
|---|---|---|---|---|
| Su Sun | Young | 50% | Dreaming | 50% |
| Mo Moon | Old | 15% | Awake | 100% |
| Ma Mars | Dead | 0% | Dreaming | 50% |
| Me Mercury | Adult | 100% | Dreaming | 50% |
| Ju Jupiter | Old | 15% | Dreaming | 50% |
| Ve Venus | Adult | 100% | Sleeping | 0% |
| Sa Saturn | Child | 25% | Awake | 100% |
| Ra Rahu | Child | 25% | Awake | 100% |
| Ke Ketu | Child | 25% | Awake | 100% |

## 2. Авастхи по настроению

Диптади и Ладжджитади приходят двумя параллельными колонками: состояние и причина. Причина называет виновников, и коды планет и знаков в ней остаются латиницей на обоих языках — парсер вытаскивает их точным совпадением. Солнце этой карты:

| Состояние | Тон | Причина | Планеты | Знаки |
|---|---|---|---|---|
| Relaxed, inspired, open and supported | green | Benefic influence: Ju | Ju | — |
| Calm, good-natured, clean and satisfied | green | Friend sign or friend/Jupiter influence: Cn Mo Ma Ju | Mo, Ma, Ju | Cn |
| Vicious, vile, malicious and confused | red | Malefic sign | — | — |
| Crippled, tense, pinched and embarrassed | red | Malefic influence: Mo Ma Sa | Mo, Ma, Sa | — |
| Suffering, sad, unhappy and hungry | red | Enemy sign or enemy/Saturn influence: Sa | Sa | — |

## 3. Шаянади-авастхи

_Note: to determine the strength of Shayanadi Avastha, the first syllable of the name is used, where ` - alveolar, `` - dental, ``` - palatal sounds_

Поэтому сила приходит не одним числом, а по всем пяти группам слогов — выбирать нужную должен тот, кто знает имя:

| Планета | Состояние | a bh chh d` dh`` k v | dh` i j kh m n`` sh``` | g jh p sh` t u y | e gh ph r s t` th`` | b ch d`` h l o th` |
|---|---|---|---|---|---|---|
| Su | Gaining | 50% | 100% | 15% | 50% | 100% |
| Mo | Resting | 50% | 100% | 15% | 50% | 100% |
| Ma | Seated | 50% | 100% | 15% | 50% | 100% |
| Me | Eating | 50% | 100% | 15% | 50% | 100% |
| Ju | Gaining | 50% | 100% | 15% | 50% | 100% |
| Ve | Aspiring | 100% | 15% | 50% | 100% | 15% |
| Sa | Eating | 50% | 100% | 15% | 50% | 100% |
| Ra | Eating | 100% | 15% | 50% | 100% | 15% |
| Ke | Gaining | 15% | 50% | 100% | 15% | 50% |

Запись одной планеты целиком:

```json
{
  "state": "Gaining",
  "tone": "red",
  "effect": "Problems from enemies, fickleness, exhaustion, arrogance, malevolent and not following dharma",
  "by_letter_group": [
    {
      "letters": [
        "a",
        "bh",
        "chh",
        "d`",
        "dh``",
        "k",
        "v"
      ],
      "strength_percent": 50,
      "tone": "orange"
    },
    {
      "letters": [
        "dh`",
        "i",
        "j",
        "kh",
        "m",
        "n``",
        "sh```"
      ],
      "strength_percent": 100,
      "tone": "green"
    },
    {
      "letters": [
        "g",
        "jh",
        "p",
        "sh`",
        "t",
        "u",
        "y"
      ],
      "strength_percent": 15,
      "tone": "red"
    },
    {
      "letters": [
        "e",
        "gh",
        "ph",
        "r",
        "s",
        "t`",
        "th``"
      ],
      "strength_percent": 50,
      "tone": "orange"
    },
    {
      "letters": [
        "b",
        "ch",
        "d``",
        "h",
        "l",
        "o",
        "th`"
      ],
      "strength_percent": 100,
      "tone": "green"
    }
  ]
}
```

## 4. Легенда шаянади

Перечислены только состояния, встретившиеся в этой карте; число в скобках — сколько планет в этом состоянии (в сумме ровно 9 — все планеты):

| Состояние | Планет | Тон | Описание |
|---|---|---|---|
| Resting | 1 | red | The planet is inactive, it lacks the initiative and energy to get things done. It is aware of its goals and desires, but is not able to fully realize them, since it cannot use all its useful and active abilities. Avastha is unfavorable, only Rahu and Ketu in certain signs are favorable here |
| Seated | 1 | red | The planet is in a waiting state. Avastha is unfavorable, especially for male initiating planets, only Venus and Mercury as a benefic are favorable here |
| Gaining | 3 | red | The planet is in a state of balancing the results of life in the material world. It usually experiences crises and fractures, and indicates the need for lessons. Malefics are especially unfavorable here, when benefics in goodness (Jupiter and Moon) and Mercury bring good |
| Eating | 3 | red | The planet is experiencing emotional starvation and suffering from a lack of happiness for a long time. Malefic are especially unfavorable here, devouring the house in which they are located. Only benefics in goodness (Jupiter and Moon) bring good here, since they are most inclined to a state of contentment |
| Aspiring | 1 | green | The planet is eager to gain the fruition of its beneficial indications. Avastha is very favorable and indicates the greatest achievements, so any planet here gives its beneficial results very quickly and confidently. Only Rahu and Ketu are unfavorable here |

## 5. Русский ответ

| Поле | en | ru |
|---|---|---|
| Балади | Young | Юная |
| Джаградади | Dreaming | Мечтающая |
| Шаянади | Gaining | Обретающая |
| Сила (совпадает) | 50% | 50% |
| Группы слогов (совпадают) | a bh chh d` dh`` k v | a bh chh d` dh`` k v |

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
