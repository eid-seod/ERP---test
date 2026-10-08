"""Generate a local Nginx config; no production host/domain is provisioned."""
import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configuration(port, directory, plain_http=False):
    directory.mkdir(parents=True, exist_ok=True)
    cookie_flags = 'httponly samesite=lax' if plain_http else 'secure httponly samesite=none'
    return f'''worker_processes 1;
pid {directory}/nginx.pid;
error_log {directory}/error.log;
events {{ worker_connections 1024; }}
http {{
    access_log {directory}/access.log;
    client_body_temp_path {directory}/client-body;
    proxy_temp_path {directory}/proxy-temp;
    fastcgi_temp_path {directory}/fastcgi-temp;
    uwsgi_temp_path {directory}/uwsgi-temp;
    scgi_temp_path {directory}/scgi-temp;
    upstream accounting_backend {{ server 127.0.0.1:5051; }}
    upstream portfolio_backend {{ server 127.0.0.1:5052; }}
    server {{
        listen 0.0.0.0:{port};
        server_name _;
        client_max_body_size 2m;
        proxy_cookie_flags session {cookie_flags};
        include {ROOT}/deployment/routing.conf;
    }}
}}
'''


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--nginx', required=True)
    parser.add_argument('--port', type=int, default=3000)
    parser.add_argument('--config-only', action='store_true')
    parser.add_argument('--plain-http', action='store_true', help='Local HTTP only; never use for public HTTPS embedded Preview.')
    args = parser.parse_args()
    directory = Path('/tmp/eid-unified-preview')
    path = directory / 'nginx.conf'
    path.write_text(configuration(args.port, directory, args.plain_http))
    subprocess.run([args.nginx, '-t', '-c', str(path), '-p', str(directory)], check=True)
    if not args.config_only:
        subprocess.run([args.nginx, '-c', str(path), '-p', str(directory), '-g', 'daemon off;'], check=True)
