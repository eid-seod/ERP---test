"""Run module checks in isolated interpreters; never merge incompatible app imports."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    for module in ['portfolio', 'accounting-software', 'deployment']:
        print('Checking:', module, flush=True)
        subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT / module, check=True)
    subprocess.run(['node', '--check', str(ROOT / 'portfolio/static/js/portfolio.js')], check=True)
    subprocess.run([sys.executable, str(ROOT / 'deployment/verify_preservation.py')], check=True)
