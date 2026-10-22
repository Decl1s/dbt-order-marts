"""Учебный вход: подготовить синтетику, запустить dbt и прочитать проверенный снимок."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ORDERS = [
    ['O0001', '2026-10-01', 'web', 'paid', 10000],
    ['O0002', '2026-10-01', 'store', 'paid', 20000],
    ['O0003', '2026-10-01', 'web', 'cancelled', 5000],
    ['O0004', '2026-10-02', 'web', 'paid', 30000],
    ['O0005', '2026-10-02', 'store', 'paid', 15000],
    ['O0006', '2026-10-02', 'web', 'paid', 10000],
]
REFUNDS = [['R0001', 'O0001', 2000], ['R0002', 'O0001', 1000], ['R0003', 'O0004', 5000]]
CASES = ('baseline', 'duplicate-order', 'unknown-order', 'over-refund', 'bad-status', 'fractional-amount')


def prepare(root: Path = ROOT, case: str = 'baseline') -> None:
    """Создать новый набор. Существующие файлы пользователя никогда не перезаписываются."""
    if case not in CASES:
        raise ValueError('Неизвестный учебный сценарий.')
    folder = root / 'workspace/seeds'
    folder.parent.mkdir(parents=True, exist_ok=True)
    # mkdir без exist_ok отказывает даже на пустой существующей папке.
    folder.mkdir()
    orders = [r.copy() for r in ORDERS]
    refunds = [r.copy() for r in REFUNDS]
    if case == 'duplicate-order':
        orders.append(orders[0].copy())
    elif case == 'unknown-order':
        refunds[0][1] = 'O9999'
    elif case == 'over-refund':
        refunds[0][2] = 20000
    elif case == 'bad-status':
        orders[0][3] = 'unknown'
    elif case == 'fractional-amount':
        refunds[0][2] = '2000.5'
    for name, header, rows in [
        ('raw_orders', ['order_id', 'order_date', 'channel', 'status', 'amount_cents'], orders),
        ('raw_refunds', ['refund_id', 'order_id', 'amount_cents'], refunds),
    ]:
        with (folder / (name + '.csv')).open('x', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(header)
            writer.writerows(rows)


def fingerprint(root: Path = ROOT) -> str:
    """Связать снимок с байтами входа и SQL/config, включая имена файлов.

    Документы не влияют на результат. CSV ограничены учебным размером; хэш не является
    заменой проверки контракта. Правила содержимого и связи проверяет сам dbt.
    """
    paths = [root / 'dbt_project.yml', root / 'profiles/profiles.yml', root / 'scripts/lab.py']
    paths += sorted((root / 'models').rglob('*')) + sorted((root / 'tests').rglob('*.sql'))
    seeds = sorted((root / 'workspace/seeds').glob('*.csv'))
    if {p.name for p in seeds} != {'raw_orders.csv', 'raw_refunds.csv'}:
        raise ValueError('Нужны ровно два учебных CSV; сначала выполните prepare.')
    for p in seeds:
        if p.stat().st_size > 1_000_000:
            raise ValueError('Учебный CSV превышает 1 000 000 байт.')
    paths += seeds
    digest = hashlib.sha256()
    for path in sorted(p for p in paths if p.is_file()):
        data = path.read_bytes()
        digest.update(path.relative_to(root).as_posix().encode() + b'\0')
        digest.update(str(len(data)).encode() + b'\0' + data)
    return digest.hexdigest()


def save_state(root: Path, state: dict) -> None:
    """Записать один JSON заменой соседнего файла; при сбое старый файл не обрывается."""
    folder = root / 'workspace'
    folder.mkdir(exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=folder,
                                         prefix='.state-', suffix='.json', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
        os.replace(temporary, folder / 'last_build.json')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def dbt_command(root: Path, command: str) -> list[str]:
    executable = Path(sys.executable).parent / ('dbt.exe' if os.name == 'nt' else 'dbt')
    if not executable.is_file():
        raise ValueError('dbt отсутствует в окружении Python; выполните uv sync --frozen.')
    return [str(executable), '--no-use-colors', '--log-path', str(root / 'workspace/logs'),
            *(['docs', 'generate'] if command == 'docs' else [command]),
            '--project-dir', str(root), '--profiles-dir', str(root / 'profiles'),
            *(['--full-refresh'] if command == 'build' else [])]


def dbt_env(root: Path) -> dict[str, str]:
    """Настройки только дочернего процесса: не трогаем пользовательские профили dbt."""
    return {**os.environ, 'DBT_SEND_ANONYMOUS_USAGE_STATS': 'false',
            'DBT_LAB_DB': str(root / 'workspace/orders.duckdb'),
            'DBT_PARTIAL_PARSE': 'false', 'PYTHONUTF8': '1',
            'DBT_TARGET_PATH': str(root / 'workspace/target')}


def read_database(root: Path) -> dict:
    """Снять результаты после полного успеха build; сортировка делает JSON устойчивым."""
    import duckdb
    with duckdb.connect(str(root / 'workspace/orders.duckdb'), read_only=True) as con:
        facts = con.execute('select count(*), sum(gross_cents), sum(refunded_cents), sum(net_cents) from fct_orders').fetchone()
        cursor = con.execute('select * from mart_daily_channel order by order_date, channel')
        names = [d[0] for d in cursor.description]
        rows = [dict(zip(names, row)) for row in cursor.fetchall()]
        for row in rows:
            row['order_date'] = str(row['order_date'])
    return {'order_rows': facts[0], 'gross_cents': facts[1], 'refunded_cents': facts[2],
            'net_cents': facts[3], 'daily': rows}


def build(root: Path = ROOT) -> dict:
    """dbt строит DAG и выполняет data tests. Только полный успех разрешает снимок.

    Вся база не охвачена общей транзакцией: ошибка может оставить часть новых таблиц.
    Поэтому последующий report читает опубликованный снимок, а не частичную базу.
    """
    save_state(root, {'status': 'building'})
    try:
        before = fingerprint(root)
        subprocess.run(dbt_command(root, 'build'), cwd=root, env=dbt_env(root),
                       check=True, timeout=180)
        if before != fingerprint(root):
            raise ValueError('Вход или SQL изменился во время build; повторите запуск.')
        report = read_database(root)
        state = {'status': 'success', 'fingerprint': before, 'report': report}
        save_state(root, state)
        return report
    except BaseException:
        save_state(root, {'status': 'failed'})
        raise


def report(root: Path = ROOT) -> dict:
    """Не выдавать старый снимок за результат новых/отвергнутых данных."""
    state = json.loads((root / 'workspace/last_build.json').read_text(encoding='utf-8'))
    if state.get('status') != 'success' or state.get('fingerprint') != fingerprint(root):
        raise ValueError('Нет успешного снимка для текущих данных/SQL; выполните build.')
    return state['report']


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare', help='Создать синтетические CSV без перезаписи')
    prep.add_argument('--case', choices=CASES, default='baseline', help='Учебный набор входных данных')
    commands.add_parser('build', help='Построить и проверить модели через dbt')
    commands.add_parser('report', help='Показать последний проверенный снимок текущего входа')
    commands.add_parser('docs', help='Сгенерировать документацию dbt, не запускать сервер')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            prepare(case=args.case)
            print('Созданы два синтетических CSV в workspace/seeds.')
        elif args.command == 'build':
            print(json.dumps(build(), ensure_ascii=False, indent=2))
        elif args.command == 'report':
            print(json.dumps(report(), ensure_ascii=False, indent=2))
        else:
            subprocess.run(dbt_command(ROOT, 'docs'), cwd=ROOT,
                           env=dbt_env(ROOT), check=True, timeout=180)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        # Не включаем строки подключения или входные строки в сообщение своего CLI.
        print('Ошибка: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
