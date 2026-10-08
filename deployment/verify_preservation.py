"""Verify historical accounting files plus explicit approved source extensions."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(check_database=True):
    manifest = json.loads((ROOT / 'documentation/accounting-preservation.json').read_text())
    overlay_path = ROOT / 'documentation/super-admin-preservation.json'
    overlay = json.loads(overlay_path.read_text()) if overlay_path.is_file() else {}
    approved = overlay.get('approved_existing_accounting_files', {})
    if set(approved) - set(manifest['files']):
        raise RuntimeError('Unexpected original-file override in Step 1 manifest.')
    for relative, historical in manifest['files'].items():
        expected = approved.get(relative, {}).get('sha256', historical)
        path = ROOT / 'accounting-software' / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Accounting source changed outside recorded scope: ' + relative)
    database = ROOT / 'accounting-software' / manifest['database']['relative_path']
    if check_database and hashlib.sha256(database.read_bytes()).hexdigest() != manifest['database']['sha256']:
        raise RuntimeError('Accounting database differs from original received baseline. Use --source-only after an approved migration or legitimate data changes.')
    results = {'accounting_files_verified': len(manifest['files']), 'historical_baseline': manifest['baseline_commit'],
        'approved_source_extension': overlay.get('scope'), 'approved_existing_changes': sorted(approved),
        'database_hash_matches_original_received': check_database,
        'nested_git_directories': [str(path) for path in ROOT.rglob('.git') if path != ROOT / '.git']}
    if results['nested_git_directories']:
        raise RuntimeError('Nested Git repository found.')
    if check_database:
        with sqlite3.connect(database.as_uri() + '?mode=ro', uri=True) as connection:
            results['integrity'] = connection.execute('PRAGMA integrity_check').fetchone()[0]
            if results['integrity'] != 'ok':
                raise RuntimeError('Database integrity failed.')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-only', action='store_true', help='Use after approved schema/data changes; original business source and recorded extensions still must match.')
    args = parser.parse_args()
    print(json.dumps(verify(not args.source_only), indent=2))
