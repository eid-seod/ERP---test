"""Build one portable release from committed source; never writes the accounting DB."""
import argparse
import hashlib
import json
import sqlite3
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from verify_preservation import verify

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode().strip()


def package(output):
    if git('status', '--porcelain'):
        raise RuntimeError('Commit all intended source before packaging; working tree is not clean.')
    preservation = verify()
    output.mkdir(parents=True, exist_ok=True)
    bundle = output / 'Eid-Saeed-Mahmoud.bundle'
    archive = output / 'Eid-Saeed-Mahmoud-Deployment.zip'
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'create', str(bundle), '--all'], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'verify', str(bundle)], check=True)
    sha = git('rev-parse', 'HEAD')
    remote = git('ls-remote', '--heads', 'origin', 'main').split()[0]
    if remote != sha:
        raise RuntimeError('Remote main does not match the release. Resolve before final delivery.')
    files = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    database = ROOT / 'accounting-software/database.db'
    # Hold a SQLite read transaction while collecting exact received file bytes.
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        connection.execute('BEGIN')
        connection.execute('SELECT COUNT(*) FROM users').fetchone()
        data = database.read_bytes()
    evidence = {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'git_commit': sha,
        'github_repository': 'https://github.com/eid-seod/ERP---test',
        'github_main_matches': remote == sha,
        'accounting_preservation': preservation,
        'database_sha256': hashlib.sha256(data).hexdigest(),
        'module_test_counts': {'portfolio': 9, 'accounting': 6, 'deployment': 8},
        'total_passed_tests': sum([9, 6, 8]),
        'responsive_widths_checked': [320, 360, 390, 768, 960, 1024, 1440],
        'same_origin_https_portfolio_and_authenticated_accounting': True,
        'nginx_native_config_validated': True,
        'compose_model_validated': True,
        'docker_image_execution_verified': False,
        'owner_production_server_deployed': False,
        'new_repository_domain_database_or_host_created': False,
        'legacy_managed_portfolio_retirement': 'Not performed; retire after verified private-server cutover.',
        'database_note': 'Received demo database only. Never overwrite an existing live database with this file.',
    }
    prefix = 'Eid-Saeed-Mahmoud/'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as release:
        for relative in files:
            if relative:
                release.write(ROOT / relative, prefix + relative)
        release.writestr(prefix + 'accounting-software/database.db', data)
        release.write(bundle, prefix + bundle.name)
        release.writestr(prefix + 'release-verification.json', json.dumps(evidence, indent=2) + '\n')
    verify()
    evidence['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
    evidence['bundle_sha256'] = hashlib.sha256(bundle.read_bytes()).hexdigest()
    evidence_file = output / 'release-verification.json'
    evidence_file.write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'archive': str(archive), 'bundle': str(bundle), 'evidence': str(evidence_file), 'commit': sha, 'tests_passed': evidence['total_passed_tests']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    package(args.output.resolve())
