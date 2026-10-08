"""Public Arabic portfolio only; imports no accounting application modules."""
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, render_template, send_from_directory, Response
from markupsafe import Markup, escape

from content import SERVICES, EXPERTISE, SOFTWARE_FEATURES, ARTICLES

ROOT = Path(__file__).resolve().parents[1]


def create_app(test_config=None):
    app = Flask(__name__, static_url_path='/portfolio-assets')
    app.config.update(PUBLIC_ORIGIN=os.getenv('PUBLIC_ORIGIN', '').rstrip('/'), CONTACT_PHONE=os.getenv('CONTACT_PHONE', '01000062838'))
    if test_config:
        app.config.update(test_config)
    if app.config['PUBLIC_ORIGIN']:
        parsed = urlparse(app.config['PUBLIC_ORIGIN'])
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password or parsed.path not in {'', '/'}:
            raise ValueError('PUBLIC_ORIGIN must be the supplied public HTTP(S) origin.')

    @app.template_filter('terms')
    def isolate_terms(value):
        parts = re.split(r'([A-Za-z][A-Za-z0-9]*(?:[ \t&]+[A-Za-z][A-Za-z0-9]*)*)', str(value))
        return Markup('').join(Markup('<bdi dir="ltr" lang="en">') + escape(part) + Markup('</bdi>') if re.match(r'^[A-Za-z]', part) else escape(part) for part in parts)

    @app.context_processor
    def context():
        return {'public_origin': app.config['PUBLIC_ORIGIN'], 'phone': app.config['CONTACT_PHONE'], 'software_url': '/login', 'articles': ARTICLES}

    @app.get('/')
    def home():
        return render_template('index.html', services=SERVICES, expertise=EXPERTISE, features=SOFTWARE_FEATURES)

    @app.get('/blog/<slug>')
    def article(slug):
        item = next((item for item in ARTICLES if item['slug'] == slug), None)
        if item is None:
            abort(404)
        return render_template('article.html', article=item)

    @app.get('/shared-assets/<path:filename>')
    def shared_assets(filename):
        return send_from_directory(ROOT / 'shared-assets', filename)

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'portfolio'})

    @app.get('/manus-routes.json')
    def route_manifest():
        routes = [{'path': '/', 'title': 'عيد سعيد محمود — الملف المهني'}]
        routes += [{'path': '/blog/' + item['slug'], 'title': item['title']} for item in ARTICLES]
        routes += [{'path': '/login', 'title': 'تسجيل الدخول للنظام المحاسبي'}, {'path': '/dashboard', 'title': 'Dashboard'}, {'path': '/invoice/new', 'title': 'الفاتورة الجديدة'}, {'path': '/invoice/:invoice_id/edit', 'title': 'عرض الفاتورة'}]
        routes += [{'path': '/super-admin/login', 'title': 'تسجيل دخول Super Admin'}, {'path': '/register', 'title': 'إنشاء حساب مستخدم'}]
        return jsonify({'routes': routes})

    @app.get('/robots.txt')
    def robots():
        lines = ['User-agent: *', 'Disallow: /login', 'Disallow: /dashboard', 'Disallow: /invoice', 'Disallow: /clients', 'Disallow: /users', 'Disallow: /me', 'Disallow: /register']
        if app.config['PUBLIC_ORIGIN']:
            lines.append('Sitemap: ' + app.config['PUBLIC_ORIGIN'] + '/sitemap.xml')
        return Response('\n'.join(lines) + '\n', mimetype='text/plain')

    @app.get('/sitemap.xml')
    def sitemap():
        origin = app.config['PUBLIC_ORIGIN']
        if not origin:
            return Response('لم يتم إعداد عنوان الموقع العام بعد.\n', status=503, mimetype='text/plain')
        paths = ['/', *['/blog/' + item['slug'] for item in ARTICLES]]
        items = ''.join('<url><loc>' + str(escape(origin + path)) + '</loc></url>' for path in paths)
        return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + items + '</urlset>', mimetype='application/xml')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5052')), debug=False)
