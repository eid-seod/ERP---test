"""Run module checks in isolated interpreters; never merge incompatible app imports."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _received_database_is_original():
    """True only when the tracked baseline database is present byte-for-byte.

    A fresh clone legitimately contains no database (SQLite files are gitignored
    and never committed).  Database-byte identity is only claimed when the
    original received file is actually present.
    """
    try:
        manifest = json.loads((ROOT / 'documentation/accounting-preservation.json').read_text())
        expected = manifest['database']['sha256']
    except Exception:
        return False
    database = ROOT / 'accounting-software' / manifest['database']['relative_path']
    if not database.is_file():
        return False
    return hashlib.sha256(database.read_bytes()).hexdigest() == expected


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='eid-accounting-test-bootstrap-') as temporary:
        for module in ['portfolio', 'accounting-software', 'deployment']:
            print('Checking:', module, flush=True)
            environment = os.environ.copy()
            if module == 'accounting-software':
                environment['DATABASE_URL'] = 'sqlite:///' + (Path(temporary) / 'bootstrap.db').as_posix()
            subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT / module, env=environment, check=True)
    subprocess.run(['node', '--check', str(ROOT / 'portfolio/static/js/portfolio.js')], check=True)
    subprocess.run(['node', '--check', str(ROOT / 'accounting-software/static/js/super_admin.js')], check=True)
    preservation = [sys.executable, str(ROOT / 'deployment/verify_preservation.py')]
    if not _received_database_is_original():
        # No committed database in a fresh clone: verify recorded source scope
        # without claiming the original database bytes are present.
        preservation.append('--source-only')
    subprocess.run(preservation, check=True)

