"""Настоящие сборки dbt на отдельных копиях: успех, повтор, отказы, восстановление."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import lab


def copy_project(destination: Path) -> None:
    """Копируем только код и конфигурацию; пользовательский workspace не читаем."""
    for name in ['models', 'tests', 'profiles', 'scripts']:
        shutil.copytree(lab.ROOT / name, destination / name, ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(lab.ROOT / 'dbt_project.yml', destination / 'dbt_project.yml')


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='dbt-orders-smoke-') as directory:
        root = Path(directory)
        copy_project(root)
        lab.prepare(root)
        first = lab.build(root)
        assert first['order_rows'] == 6
        assert (first['gross_cents'], first['refunded_cents'], first['net_cents']) == (85000, 8000, 77000)
        assert [r['net_cents'] for r in first['daily']] == [20000, 7000, 15000, 35000]
        assert lab.build(root) == first, 'Повтор изменил логический результат'
        # После неудачной новой сборки прежние таблицы могут остаться, но report запрещён.
        input_path = root / 'workspace/seeds/raw_refunds.csv'
        original = input_path.read_bytes()
        input_path.write_bytes(original.replace(b'2000', b'20000'))
        try:
            lab.report(root)
        except ValueError:
            pass
        else:
            raise AssertionError('Изменённый вход разрешил старый отчёт')
        try:
            lab.build(root)
        except subprocess.CalledProcessError:
            pass
        else:
            raise AssertionError('Превышенный возврат принят')
        results = json.loads((root / 'workspace/target/run_results.json').read_text())['results']
        failed = [r['unique_id'] for r in results if r['status'] == 'fail']
        assert any('refunds_within_paid_order' in name for name in failed)
        assert any(r['unique_id'].endswith('.mart_daily_channel') and r['status'] == 'skipped' for r in results)
        try:
            lab.report(root)
        except ValueError:
            pass
        else:
            raise AssertionError('Неуспешная сборка разрешила отчёт')
        input_path.write_bytes(original)
        assert lab.build(root) == first, 'Восстановление после отказа не совпало'
        subprocess.run(lab.dbt_command(root, 'docs'), cwd=root, env=lab.dbt_env(root), check=True, timeout=180)
        for name in ['index.html', 'manifest.json', 'catalog.json']:
            assert (root / 'workspace/target' / name).is_file(), name
        for case in ['duplicate-order', 'unknown-order', 'bad-status', 'fractional-amount']:
            case_root = root / case
            case_root.mkdir()
            copy_project(case_root)
            lab.prepare(case_root, case)
            try:
                lab.build(case_root)
            except subprocess.CalledProcessError:
                state = json.loads((case_root / 'workspace/last_build.json').read_text())
                assert state['status'] == 'failed'
            else:
                raise AssertionError('Плохой сценарий принят: ' + case)
        empty_root = root / 'empty-input'
        empty_root.mkdir()
        copy_project(empty_root)
        lab.prepare(empty_root)
        (empty_root / 'workspace/seeds/raw_orders.csv').write_text('order_id,order_date,channel,status,amount_cents\n')
        (empty_root / 'workspace/seeds/raw_refunds.csv').write_text('refund_id,order_id,amount_cents\n')
        empty = lab.build(empty_root)
        assert empty['order_rows'] == 0 and empty['daily'] == []
        assert (empty['gross_cents'], empty['refunded_cents'], empty['net_cents']) == (0, 0, 0)
    print(json.dumps({'smoke': 'passed', 'builds': 9, 'net_cents': 77000,
                      'repeat_equal': True, 'recovered': True, 'rejected_cases': 5, 'docs_generated': True}))


if __name__ == '__main__':
    main()
