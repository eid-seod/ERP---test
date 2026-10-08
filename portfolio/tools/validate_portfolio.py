"""Read-only Arabic portfolio interaction checks through the unified proxy."""
from playwright.sync_api import sync_playwright
BASE = 'http://127.0.0.1:3000'

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE); page.wait_for_load_state('networkidle')
    assert page.locator('html').get_attribute('lang') == 'ar'
    assert page.locator('html').get_attribute('dir') == 'rtl'
    assert 'عيد سعيد' in page.locator('h1').inner_text()
    assert page.locator('.software-link').get_attribute('href') == '/login'
    assert page.locator('.service-row').count() == 12
    assert page.locator('.article-list article').count() == 3
    assert page.locator('.contact-phone').get_attribute('href') == 'tel:01000062838'
    page.locator('.screenshot-button').click()
    assert page.locator('#screenshot-dialog').evaluate('el => el.open')
    page.locator('.dialog-close').click()
    page.locator('#inquiry-service').select_option(index=1)
    page.locator('#inquiry-message').fill('أحتاج إلى دعم محاسبي وتنظيم التقارير المالية لنشاطي.')
    page.locator('.inquiry-button').click()
    assert 'عيد سعيد محمود' in page.locator('#inquiry-draft').input_value()
    assert 'لم يتم إرسال أو تخزين' in page.locator('#inquiry-feedback').inner_text()
    for width in [1440, 1024, 960, 768, 390, 360, 320]:
        page.set_viewport_size({'width': width, 'height': 900})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {width}px'
    page.locator('.menu-toggle').click()
    assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'true'
    page.locator('.main-nav a[href="/#about"]').click()
    assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'false'
    page.set_viewport_size({'width': 390, 'height': 900}); page.goto(BASE); page.wait_for_load_state('networkidle')
    page.screenshot(path='/tmp/eid-unified-arabic-mobile.png')
    page.set_viewport_size({'width': 1440, 'height': 1000}); page.goto(BASE); page.wait_for_load_state('networkidle')
    page.screenshot(path='/tmp/eid-unified-arabic-desktop.png')
    page.locator('.article-list h3 a').first.click(); page.wait_for_load_state('networkidle')
    assert page.locator('.article-body section').count() == 3
    assert not errors, errors
    browser.close()
    print('PASS: Arabic RTL, 12 services, three articles, same-origin link, seven responsive widths, dialog, mobile navigation, Arabic inquiry feedback; no JavaScript errors.')
