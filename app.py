"""Public portfolio only; never imports or modifies the accounting application."""
import os
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template

from content import SERVICES, EXPERIENCE, SOFTWARE_FEATURES, SOFTWARE_BENEFITS

DEFAULT_SOFTWARE_URL = "https://5051-ii9x7ilv6lmzhug9n1g1o-684bafc5.sg2.manus.computer/login"


def validated_url(value, setting_name):
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL without credentials.")
    return value


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SOFTWARE_URL=os.getenv("ACCOUNTING_SOFTWARE_URL", DEFAULT_SOFTWARE_URL),
        PUBLIC_ORIGIN=os.getenv("PUBLIC_ORIGIN", "").rstrip("/"),
        CONTACT_PHONE=os.getenv("CONTACT_PHONE", "01000062838"),
        CONTACT_EMAIL=os.getenv("CONTACT_EMAIL", ""),
        LINKEDIN_URL=os.getenv("LINKEDIN_URL", ""),
    )
    if test_config:
        app.config.update(test_config)
    validated_url(app.config["SOFTWARE_URL"], "ACCOUNTING_SOFTWARE_URL")
    if app.config["PUBLIC_ORIGIN"]:
        validated_url(app.config["PUBLIC_ORIGIN"], "PUBLIC_ORIGIN")
    if app.config["LINKEDIN_URL"]:
        validated_url(app.config["LINKEDIN_URL"], "LINKEDIN_URL")

    @app.get("/")
    def home():
        software_url = app.config["SOFTWARE_URL"]
        return render_template(
            "index.html",
            services=SERVICES,
            experience=EXPERIENCE,
            features=SOFTWARE_FEATURES,
            benefits=SOFTWARE_BENEFITS,
            software_url=software_url,
            software_is_preview="manus.computer" in urlparse(software_url).hostname,
            phone=app.config["CONTACT_PHONE"],
            email=app.config["CONTACT_EMAIL"],
            linkedin=app.config["LINKEDIN_URL"],
            public_origin=app.config["PUBLIC_ORIGIN"],
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "personal-portfolio"})

    @app.get("/manus-routes.json")
    def route_manifest():
        return jsonify({"routes": [{"path": "/", "title": "Eid Saeed Mahmoud — Professional Portfolio"}]})

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")), debug=False)
