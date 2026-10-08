"""Capture existing empty demo screens. No software code or accounting records are changed."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:5051"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    context = browser.new_context(viewport={"width": 1440, "height": 980}, device_scale_factor=1)
    response = context.request.post(BASE + "/login", data={"email": "admin@example.com", "password": "Admin123!"})
    if response.status != 200:
        raise RuntimeError("Demo login failed")
    for endpoint, key in [("/clients", "clients"), ("/invoices", "invoices")]:
        response = context.request.get(BASE + endpoint)
        if response.status != 200 or response.json().get(key):
            raise RuntimeError("Capture stopped: demo must be empty to avoid disclosing accounting records")
    page = context.new_page()
    for route, name in [("/dashboard", "accounting-dashboard.png"), ("/invoice/new", "accounting-invoice.png")]:
        page.goto(BASE + route)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(ROOT / "static" / "images" / name), full_page=True)
        print("Captured existing screen:", name)
    browser.close()
