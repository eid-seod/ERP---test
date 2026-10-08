"""Run module checks in isolated interpreters; never merge incompatible app imports."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
    subprocess.run([sys.executable, str(ROOT / 'deployment/verify_preservation.py')], check=True)
