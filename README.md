# Витрины заказов и возвратов на dbt Core

Учебный проект начинающего дата-инженера, 22.10.2026. Два синтетических CSV превращаются
в факт заказов и дневную витрину. dbt связывает SQL через `ref`, строит зависимости
и выполняет 22 проверки данных. Несколько возвратов одного заказа не умножают выручку.

Начни с [карты кода](START_HERE.md), затем прочитай [конспект](NOTES.md),
[решения](DECISIONS.md) и [5 заданий](EXERCISES.md). Коммерческий опыт не заявляется.

## Быстрый запуск

Нужны Python 3.12 и uv 0.13.1. Команды выполняются в корне **этого** проекта.
Linux, если uv ещё нет:

```bash
python3.12 -m venv .tools/bootstrap
.tools/bootstrap/bin/python -m pip install uv==0.13.1
.tools/bootstrap/bin/uv sync --frozen --no-dev
.venv/bin/python scripts/lab.py prepare
.venv/bin/python scripts/lab.py build
.venv/bin/python scripts/lab.py report
```

Windows PowerShell:

```powershell
py -3.12 -m venv .tools/bootstrap
.tools/bootstrap/Scripts/python.exe -m pip install uv==0.13.1
.tools/bootstrap/Scripts/uv.exe sync --frozen --no-dev
.venv/Scripts/python.exe scripts/lab.py prepare
.venv/Scripts/python.exe scripts/lab.py build
.venv/Scripts/python.exe scripts/lab.py report
```

При наличии uv 0.13.1 достаточно `uv sync --frozen --no-dev`, затем тех же команд
через Python из `.venv`. Менеджер и библиотеки не устанавливаются глобально.
Интернет нужен для установки, обработка локальная. DuckDB — файл внутри процесса,
отдельная служба, Docker, аккаунт dbt и платное облако не нужны.

## Что должно получиться

`prepare` создаёт `workspace/seeds/raw_orders.csv` (6 заказов) и `raw_refunds.csv`
(3 возврата). Существующую папку seeds команда не перезаписывает. `build` запускает
настоящий `dbt build`: 2 seeds, 5 моделей и 22 data tests. Успех: `PASS=29`,
`ERROR=0`, `SKIP=0`. Затем CLI выводит проверенный снимок:

- `order_rows=6`, оплаченных заказов в витрине — 5, отменённый — 1.
- `gross_cents=85000`, `refunded_cents=8000`, `net_cents=77000`.
- По `(дата, канал)`: 01.10 store=20000, web=7000; 02.10 store=15000, web=35000 копеек net.

Повтори `build`: логические значения останутся теми же, таблицы пересобираются.
Байты файла БД и технические даты dbt не обязаны совпадать.
`report` читает снимок `workspace/last_build.json`, а не произвольное содержимое БД.
Если CSV/SQL изменён или последний build неуспешен, старый отчёт не выдаётся за новый.

## Потрогать руками

Открой `workspace/seeds/raw_refunds.csv`, измени первый возврат `2000` на `4000`.
Запусти `build`, затем `report`: ожидается `net_cents=75000`, для 01.10 web — 5000.
Теперь замени сумму на `20000`: проверка `refunds_within_paid_order` завершится FAIL,
зависимая витрина будет пропущена, `build` и `report` дадут exit 1. Верни `2000`
и повтори `build`: снова 77000. Для точного повтора примера используй новую копию
проекта; удалять прежние учебные изменения не требуется.

`prepare --case ...` умеет создавать новый плохой набор: `duplicate-order`,
`unknown-order`, `over-refund`, `bad-status`, `fractional-amount`. Он также откажется
заменить существующие CSV. Применяй в отдельной распакованной копии.

## Проверки и документация

```bash
.venv/bin/python -m unittest discover -s checks -v
.venv/bin/python scripts/smoke.py
.venv/bin/python scripts/lab.py docs
.venv/bin/python scripts/check_public.py
.venv/bin/python scripts/package_release.py
```

В Windows замени `.venv/bin/python` на `.venv/Scripts/python.exe`.
Smoke делает **9 настоящих сборок dbt** на временных копиях: успех, повтор,
пять плохих наборов, восстановление после превышенного возврата и пустой вход. Его итог —
`smoke: passed`, `net_cents: 77000`. FAIL/SKIP в отрицательных сценариях ожидаемы;
успех всей проверки определяется финальным JSON и кодом 0.
Команда `docs` генерирует `workspace/target/index.html`, `manifest.json` и `catalog.json`,
сервер не запускает. SQL после Jinja ищи в `workspace/target/compiled`.
Подготовлены шесть задач VS Code и одна конфигурация отладки Python.

## Контракт и ограничения

Единица orders — один уникальный непустой `order_id`, дата заказа, канал `web/store`,
статус `paid/cancelled`, сумма в целых положительных копейках от 1 до 9999999.
Единица refunds — уникальный непустой `refund_id`, существующий `order_id` и такая же
положительная сумма. Несколько возвратов заказа разрешены; их сумма не превышает
цену, возвраты отменённых заказов запрещены. Пустые refunds допустимы.
День возврата не хранится: деньги относятся к **дате заказа**, это не кассовый отчёт.

Проверки — утверждения над таблицами dbt, а не ограничения доступа в БД. `dbt build`
не является общей транзакцией всех моделей: при отказе часть таблиц может обновиться,
а прежняя витрина сохраниться. Пользовательский снимок разрешается только после
полного успешного build. Одновременные писатели, непрерывная загрузка, production-роли,
миграции и авария питания не поддержаны. Один CSV ограничен 1 000 000 байт.
Публикуем исходники по `PUBLIC_FILES.txt`; CSV, БД, логи, target, окружения и результаты
не входят в Git/ZIP. Все примеры генерируются из констант без реальных персональных данных.
Фактические проверки и состояние публикации — [VALIDATION.md](VALIDATION.md).

## GitHub

[Публичные исходники](https://github.com/Decl1s/dbt-order-marts),
[запуски CI](https://github.com/Decl1s/dbt-order-marts/actions),
[релиз v0.1.0 с исходным ZIP и SHA256SUMS](https://github.com/Decl1s/dbt-order-marts/releases/tag/v0.1.0).
