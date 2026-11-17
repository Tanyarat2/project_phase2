import base64
import getpass
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta, timezone


API_DIR = Path(__file__).resolve().parent
SETTINGS = {
    'WC_SHOP_USERNAME': 'Shop username (for example itcs386-g02): ',
    'WC_SHOP_API_PASSWORD': 'Shop API password (from the accounts sheet): ',
}


def main():
    env = os.environ.copy()
    if sys.stdin.isatty():
        for name, prompt in SETTINGS.items():
            if not env.get(name, '').strip():
                read_value = input if name == 'WC_SHOP_USERNAME' else getpass.getpass
                env[name] = read_value(prompt).strip()

    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    env['COLUMNS'] = '120'
    username = env.get('WC_SHOP_USERNAME', '').strip()
    password = env.get('WC_SHOP_API_PASSWORD', '').strip()
    secrets = []
    if password:
        encoded = base64.b64encode(f'{username}:{password}'.encode('latin-1', errors='replace')).decode()
        secrets = [password, encoded]
    started = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
    missing = [name for name in SETTINGS if not env.get(name, '').strip()]
    command = [sys.executable, '-m', 'pytest', '-vv', '--tb=short', '-ra', '-p', 'no:cacheprovider', '.']

    with (API_DIR / 'results.txt').open('w', encoding='utf-8') as log:
        def write(line):
            print(line, end='', flush=True)
            log.write(line)
            log.flush()

        write(f'Choice 1 WooCommerce API testing\nStarted: {started}\n')
        if missing:
            write(f'Live run blocked. Missing settings: {", ".join(missing)}\n')
        write('\n')

        with subprocess.Popen(
            command, cwd=API_DIR, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            encoding='utf-8', errors='replace',
        ) as run:
            for line in run.stdout:
                for secret in secrets:
                    line = line.replace(secret, '[redacted]')
                write(line)
            exit_code = run.wait()

        if missing and exit_code == 0:
            exit_code = 2
        write(f'\nRunner exit code: {exit_code}\n')
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
