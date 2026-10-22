# Фактические технологии

22.10.2026, версия 0.1.0. Окружение Python 3.12; локально 3.12.15.
Главный новый инструмент — **dbt Core**. DuckDB используется как локальный движок,
не как повтор предыдущей задачи про SQL-файлы: здесь учимся ref/DAG, материализациям
и тестам dbt. Python обёртка управляет примером и безопасным снимком.

| Компонент | Версия / стандарт | Назначение и официальная ссылка |
| --- | --- | --- |
| Python | 3.12.x; локально 3.12.15 | CLI, генератор, снимок, unittest: https://docs.python.org/3.12/ |
| uv | 0.13.1 | .venv и полный lock: https://docs.astral.sh/uv/ |
| dbt Core | 1.12.3 | DAG и build: https://docs.getdbt.com/reference/commands/build |
| dbt-duckdb | 1.11.0 | Адаптер: https://github.com/duckdb/dbt-duckdb |
| DuckDB | 1.5.0 | Локальный файл и SQL: https://duckdb.org/docs/stable/ |
| SQL / Jinja | диалект DuckDB; Jinja2 ниже | Модели и ref: https://docs.getdbt.com/reference/dbt-jinja-functions/ref |
| YAML / CSV / JSON | UTF-8 | Конфигурации, пример и снимок: https://docs.python.org/3.12/library/csv.html |
| unittest / mock | стандартная библиотека | Мастерская и упаковка: https://docs.python.org/3.12/library/unittest.html |
| SHA-256 / ZIP | hashlib / zipfile | Fingerprint и релиз по allowlist: https://docs.python.org/3.12/library/zipfile.html |
| Git | локально 2.43.0 | Отдельная история и ветка codex/: https://git-scm.com/docs |
| GitHub Actions | Ubuntu / Windows, состояние в VALIDATION | CI: https://docs.github.com/ru/actions |
| actions/checkout | v4, SHA в ci.yml | Получить исходники без сохранения credentials: https://github.com/actions/checkout |
| actions/setup-python | v5, SHA в ci.yml | Python 3.12 на runner: https://github.com/actions/setup-python |
| actions/upload-artifact | v4, SHA в ci.yml | Архив и checksum: https://github.com/actions/upload-artifact |
| VS Code / debugpy | необязательная конфигурация | Задачи и отладка Python: https://code.visualstudio.com/docs/python/debugging |
| Mermaid | разметка NOTES.md | Схема графа: https://mermaid.js.org/ |

Стандартная библиотека: argparse, csv, hashlib, json, os, pathlib, subprocess,
sys, tempfile, shutil, importlib, unittest, tomllib и zipfile. Внешнего планировщика,
базы-сервера, облачного SDK и dbt-пакетов из Hub нет. pip в bootstrap служит только
установке локального uv. Библиотеки проекта закреплены в pyproject.toml и uv.lock.

## Все Python-зависимости

Прямые: dbt-core==1.12.3, dbt-duckdb==1.11.0, duckdb==1.5.0.
Полный universal lock: **60 сторонних пакетов**, 59 установлены на Linux;
tzdata условный для Windows. В uv.lock есть маркеры ОС, URL и хэши артефактов.
Таблица ниже включает прямые и все транзитивные зависимости. Наличие HTTP/телеметрии
в транзитивном стеке не означает сетевой источник данных; usage stats отключены.

| Пакет | Версия | Назначение и официальный источник поставки |
| --- | --- | --- |
| agate | 1.9.1 | Табличный разбор seed CSV: https://pypi.org/project/agate/1.9.1/ |
| annotated-types | 0.8.0 | Метаданные ограничений типов: https://pypi.org/project/annotated-types/0.8.0/ |
| attrs | 26.1.0 | Модели объектов зависимостей: https://pypi.org/project/attrs/26.1.0/ |
| babel | 2.18.0 | Локали и форматирование: https://pypi.org/project/babel/2.18.0/ |
| certifi | 2026.10.19 | Корневые сертификаты HTTP-клиента: https://pypi.org/project/certifi/2026.10.19/ |
| charset-normalizer | 3.5.2 | Определение кодировок HTTP: https://pypi.org/project/charset-normalizer/3.5.2/ |
| click | 8.5.0 | Разбор CLI dbt: https://pypi.org/project/click/8.5.0/ |
| colorama | 0.4.6 | Цветной вывод на Windows: https://pypi.org/project/colorama/0.4.6/ |
| daff | 1.4.2 | Сравнение таблиц: https://pypi.org/project/daff/1.4.2/ |
| dbt-adapters | 1.24.5 | Базовые классы и фабрика адаптеров: https://pypi.org/project/dbt-adapters/1.24.5/ |
| dbt-common | 1.39.0 | Общие контракты dbt: https://pypi.org/project/dbt-common/1.39.0/ |
| dbt-core | 1.12.3 | DAG, компиляция SQL, build и data tests: https://pypi.org/project/dbt-core/1.12.3/ |
| dbt-core-experimental-parser | 2.0.8 | Парсер проекта, транзитивная зависимость Core: https://pypi.org/project/dbt-core-experimental-parser/2.0.8/ |
| dbt-duckdb | 1.11.0 | Адаптер Core к DuckDB: https://pypi.org/project/dbt-duckdb/1.11.0/ |
| dbt-extractor | 0.6.0 | Извлечение зависимостей Jinja: https://pypi.org/project/dbt-extractor/0.6.0/ |
| dbt-protos | 1.0.607 | Схемы технических событий dbt: https://pypi.org/project/dbt-protos/1.0.607/ |
| deepdiff | 8.6.2 | Сравнение структур конфигурации: https://pypi.org/project/deepdiff/8.6.2/ |
| duckdb | 1.5.0 | Встроенная SQL-база и чтение результатов: https://pypi.org/project/duckdb/1.5.0/ |
| idna | 3.20 | Международные доменные имена HTTP: https://pypi.org/project/idna/3.20/ |
| importlib-metadata | 9.0.1 | Метаданные установленных пакетов: https://pypi.org/project/importlib-metadata/9.0.1/ |
| isodate | 0.7.2 | ISO даты и интервалы: https://pypi.org/project/isodate/0.7.2/ |
| jinja2 | 3.1.6 | Шаблоны SQL и ref: https://pypi.org/project/jinja2/3.1.6/ |
| jsonschema | 4.26.0 | Проверка JSON-схем артефактов: https://pypi.org/project/jsonschema/4.26.0/ |
| jsonschema-specifications | 2025.9.1 | Стандартные JSON-схемы: https://pypi.org/project/jsonschema-specifications/2025.9.1/ |
| leather | 0.4.1 | Транзитивные табличные представления agate: https://pypi.org/project/leather/0.4.1/ |
| markupsafe | 3.0.4 | Безопасные строковые типы Jinja: https://pypi.org/project/markupsafe/3.0.4/ |
| mashumaro | 3.17 | Сериализация dataclass: https://pypi.org/project/mashumaro/3.17/ |
| metricflow | 0.213.0 | Семантические компоненты dbt; в нашем SQL явно не используются: https://pypi.org/project/metricflow/0.213.0/ |
| more-itertools | 10.8.0 | Утилиты итераторов: https://pypi.org/project/more-itertools/10.8.0/ |
| msgpack | 1.2.3 | Бинарная сериализация кэша dbt: https://pypi.org/project/msgpack/1.2.3/ |
| networkx | 3.7 | Граф зависимостей: https://pypi.org/project/networkx/3.7/ |
| opentelemetry-api | 1.45.1 | API технической наблюдаемости зависимостей: https://pypi.org/project/opentelemetry-api/1.45.1/ |
| orderly-set | 5.5.0 | Упорядоченные множества сравнения: https://pypi.org/project/orderly-set/5.5.0/ |
| packaging | 26.3 | Версии и спецификаторы пакетов: https://pypi.org/project/packaging/26.3/ |
| parsedatetime | 2.6 | Разбор дат agate: https://pypi.org/project/parsedatetime/2.6/ |
| pathspec | 1.0.4 | Сопоставление путей проекта: https://pypi.org/project/pathspec/1.0.4/ |
| protobuf | 6.33.6 | Сериализация событий: https://pypi.org/project/protobuf/6.33.6/ |
| pydantic | 2.14.1 | Валидация моделей конфигурации: https://pypi.org/project/pydantic/2.14.1/ |
| pydantic-core | 2.50.1 | Нативный движок Pydantic: https://pypi.org/project/pydantic-core/2.50.1/ |
| python-dateutil | 2.9.0.post0 | Разбор календарных значений: https://pypi.org/project/python-dateutil/2.9.0.post0/ |
| python-dotenv | 1.2.4 | Поддержка env-файлов зависимостей; секретный env здесь не нужен: https://pypi.org/project/python-dotenv/1.2.4/ |
| python-slugify | 9.1.3 | Нормализация имён: https://pypi.org/project/python-slugify/9.1.3/ |
| pytimeparse | 1.1.10 | Разбор временных интервалов: https://pypi.org/project/pytimeparse/1.1.10/ |
| pytz | 2026.5 | Часовые пояса agate: https://pypi.org/project/pytz/2026.5/ |
| pyyaml | 6.0.3 | Разбор YAML конфигураций: https://pypi.org/project/pyyaml/6.0.3/ |
| rapidfuzz | 3.14.6 | Сопоставление строк: https://pypi.org/project/rapidfuzz/3.14.6/ |
| referencing | 0.37.0 | Ссылки JSON Schema: https://pypi.org/project/referencing/0.37.0/ |
| requests | 2.34.2 | HTTP-клиент зависимостей; вход проекта локальный: https://pypi.org/project/requests/2.34.2/ |
| rpds-py | 2026.9.1 | Неизменяемые структуры JSON Schema: https://pypi.org/project/rpds-py/2026.9.1/ |
| six | 1.17.0 | Совместимость транзитивных библиотек: https://pypi.org/project/six/1.17.0/ |
| snowplow-tracker | 1.1.0 | Транзитивная телеметрия dbt; отправка usage stats отключена: https://pypi.org/project/snowplow-tracker/1.1.0/ |
| sqlglot | 30.24.0 | SQL AST семантических компонентов: https://pypi.org/project/sqlglot/30.24.0/ |
| sqlparse | 0.6.0 | Разбор/форматирование SQL: https://pypi.org/project/sqlparse/0.6.0/ |
| tabulate | 0.10.0 | Табличный текст CLI: https://pypi.org/project/tabulate/0.10.0/ |
| text-unidecode | 1.3 | Транслитерация slugify: https://pypi.org/project/text-unidecode/1.3/ |
| typing-extensions | 4.16.0 | Совместимость аннотаций типов: https://pypi.org/project/typing-extensions/4.16.0/ |
| typing-inspection | 0.4.4 | Инспекция типов: https://pypi.org/project/typing-inspection/0.4.4/ |
| tzdata | 2026.5 | Условные данные часовых поясов Windows: https://pypi.org/project/tzdata/2026.5/ |
| urllib3 | 2.8.0 | HTTP транспорт requests: https://pypi.org/project/urllib3/2.8.0/ |
| zipp | 4.1.2 | Чтение ZIP-метаданных пакетов: https://pypi.org/project/zipp/4.1.2/ |

Версии проверены по официальному PyPI и восстановлены uv. Закреплённая связка
проходит фактические проверки; она не объявляется самой новой. dbt v2 уже доступен,
DuckDB 2.0 — новая основная ветка; обновление нужно делать отдельным изменением
с повтором позитивных и негативных сценариев. Реальная проверка ОС — в VALIDATION.
