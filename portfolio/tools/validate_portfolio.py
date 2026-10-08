"""Validate only the public portfolio. No accounting application writes or interaction."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:3000"
SOFTWARE_URL = "https://5051-ii9x7ilv6lmzhug9n1g1o-684bafc5.sg2.manus.computer/login"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(BASE)
    page.wait_for_load_state("networkidle")
    assert page.locator("h1").inner_text() == "Eid Saeed\nMahmoud."
    assert page.locator(".software-link").get_attribute("href") == SOFTWARE_URL
    assert page.locator(".software-link").get_attribute("target") == "_blank"
    assert page.locator(".contact-phone").get_attribute("href") == "tel:01000062838"
    page.locator(".screenshot-button").click()
    assert page.locator("#screenshot-dialog").evaluate("el => el.open")
    page.locator(".dialog-close").click()
    assert not page.locator("#screenshot-dialog").evaluate("el => el.open")
    page.locator("#inquiry-service").select_option(label="Remote Accounting")
    page.locator("#inquiry-message").fill("I would like to discuss accounting support for my business.")
    page.locator(".inquiry-button").click()
    assert "Remote Accounting" in page.locator("#inquiry-draft").input_value()
    assert "Nothing has been sent or stored" in page.locator("#inquiry-feedback").inner_text()
    for width in [1440, 1024, 960, 768, 390, 360]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), f"Horizontal overflow at {width}px"
    page.locator(".menu-toggle").click()
    assert page.locator(".menu-toggle").get_attribute("aria-expanded") == "true"
    page.locator(".main-nav a[href='#about']").click()
    assert page.locator(".menu-toggle").get_attribute("aria-expanded") == "false"
    page.goto(BASE)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/tmp/eid-portfolio-mobile.png", full_page=True)
    page.set_viewport_size({"width": 1440, "height": 1000})
    page.goto(BASE)
    page.wait_for_load_state("networkidle")
    page.screenshot(path="/tmp/eid-portfolio-desktop.png", full_page=True)
    assert not errors, errors
    print("PASS: responsive layout at six widths, phone, external link, mobile navigation, screenshot dialog, inquiry preparation, and no JavaScript errors.")
    browser.close()
