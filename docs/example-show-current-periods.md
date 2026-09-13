# Пример данных: `show-current-periods`

Всё ниже — настоящий ответ сайта, распарсенный тулами. Карта:
**Ss, 07.08.1983 23:00:00, UTC+4, 55°45' N 37°37' E** (Москва).

```sh
vedic-parser show-current-periods --name Ss --date 07.08.1983 --time 23:00:00 \
    --latitude 55.45 --longitude 37.37 --timezone +4 --moment 13.09.2026
```

Какие периоды идут в конкретный момент — сразу по нескольким системам, одной строкой. `--moment` по умолчанию «сейчас».

Весь ответ сайта — вот столько:

```html
<span>13.09.2026</span>&nbsp;&nbsp;&nbsp;&nbsp;
<b title="Vimshottari dasha">VD: </b><span class="Ve">Ve</span>-<span class="Mo">Mo</span>-<span class="Ra">Ra</span>
<b title="Chara dasha (K.N. Rao)">CD: </b>Sg-Le-Cp
```

## 1. Что получается

```json
{
  "date": "2026-09-13",
  "date_label": "13.09.2026",
  "dashas": [
    {
      "dasha": "vimshottari",
      "title": "Vimshottari dasha",
      "abbr": "VD",
      "kind": "planet",
      "lords": [
        "Ve",
        "Mo",
        "Ra"
      ]
    },
    {
      "dasha": "yogini",
      "title": "Yogini dasha",
      "abbr": "YD",
      "kind": "planet",
      "lords": [
        "Me",
        "Sa",
        "Ve"
      ]
    },
    {
      "dasha": "chara_rao",
      "title": "Chara dasha (K.N. Rao)",
      "abbr": "CD",
      "kind": "sign",
      "lords": [
        "Sg",
        "Le",
        "Cp"
      ]
    },
    {
      "dasha": "narayana",
      "title": "Narayana dasha",
      "abbr": "ND",
      "kind": "sign",
      "lords": [
        "Ta",
        "Cn",
        "Pi"
      ]
    }
  ]
}
```

## 2. Момент меняет всё

| Система | Вид | на 07.08.1983 | на 13.09.2026 |
|---|---|---|---|
| Vimshottari dasha | planet | Sa-Me-Ra | Ve-Mo-Ra |
| Yogini dasha | planet | Ju-Me-Ve | Me-Sa-Ve |
| Chara dasha (K.N. Rao) | sign | Ar-Ta-Ar | Sg-Le-Cp |
| Narayana dasha | sign | Li-Le-Cn | Ta-Cn-Pi |

Цепочка — маха-антар-пратьянтар. Сверено с `show-dasha`: период, который там накрывает этот момент, совпадает с первыми двумя звеньями (и для планетных систем, и для знаковых).

## 3. Ключи систем

И сокращение (`VD:`), и подпись в `title` переводятся, поэтому система опознаётся по таблице подписей — тех же самых, что стоят в селекторе даш. Незнакомую подпись парсер не угадывает: `dasha` станет `null`, а текст сохранится.

| `dasha` | en `abbr` | en `title` | ru `abbr` | ru `title` |
|---|---|---|---|---|
| `vimshottari` | VD | Vimshottari dasha | ВД | Вимшоттари даша |
| `yogini` | YD | Yogini dasha | ЙД | Йогини даша |
| `chara_rao` | CD | Chara dasha (K.N. Rao) | ЧД | Чара даша (К.Н. Рао) |
| `narayana` | ND | Narayana dasha | НД | Нарайана даша |

**Важное отличие от `show-dasha`:** знаковые системы (Чара, Нарайана) здесь приходят **кодами знаков** (`Sg-Le-Cp`), а не локализованными названиями. Это единственное место, где знаковую дашу можно читать не глядя на язык.

## 4. Про параметр момента

Сайт понимает и `13.09.2026`, и `13.9.2026 12:0`, и даже `2026-09-13`. А вот на то, что распарсить не смог, он не ругается — молча отдаёт подпись первой системы и пустую цепочку. Поэтому `api.show_current_periods` форматирует момент сам, ровно так же, как это делает JavaScript сайта.

---

Файл сгенерирован из записанных ответов в `tests/fixtures/`; обновить — `python scripts/example_md.py`.
