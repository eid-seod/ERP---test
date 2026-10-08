"""Verify file identity and SQLite identity without importing the accounting app."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(check_database=True):
    manifest = json.loads((ROOT / 'documentation/accounting-preservation.json').read_text())
    for relative, expected in manifest['files'].items():
        path = ROOT / 'accounting-software' / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Accounting source changed: ' + relative)
    database = ROOT / 'accounting-software' / manifest['database']['relative_path']
    if check_database and hashlib.sha256(database.read_bytes()).hexdigest() != manifest['database']['sha256']:
        raise RuntimeError('Accounting database differs from packaging baseline.')
    results = {'accounting_files_verified': len(manifest['files']), 'baseline': manifest['baseline_commit'], 'database_hash_matches': check_database, 'nested_git_directories': [str(path) for path in ROOT.rglob('.git') if path != ROOT / '.git']}
    if results['nested_git_directories']:
        raise RuntimeError('Nested Git repository found.')
    if check_database:
        with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
            results['integrity'] = connection.execute('PRAGMA integrity_check').fetchone()[0]
            if results['integrity'] != 'ok':
                raise RuntimeError('Database integrity failed.')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-only', action='store_true', help='Use after legitimate accounting data changes; source still must match.')
    args = parser.parse_args()
    print(json.dumps(verify(not args.source_only), indent=2))
