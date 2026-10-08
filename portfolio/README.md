# Eid Saeed Mahmoud — Professional Portfolio

A separate public portfolio built with Python, Flask, HTML, CSS, and vanilla JavaScript. It introduces Eid Saeed Mahmoud as Accounts Manager, Finance Professional, and Accounting Systems Specialist, with About Me, Experience, Professional Services, Projects, Financial Systems, and Contact sections.

## Accounting application preservation

This repository **does not contain, copy, rebuild, rename, import, proxy, or modify the existing accounting application**. The featured project links externally to the existing application, unchanged. Real screenshots show its empty demo dashboard and existing invoice form; no accounting records were added for screenshots.

The pre-implementation accounting baseline is commit `551f23d49e75cb296cbf61e7162fc04fe7c730bc` in the separate existing `ERP---test` repository. Previous branding changes predate this portfolio implementation; no rollback or additional modification has been performed.

The current link points to a temporary software preview. Set `ACCOUNTING_SOFTWARE_URL` to the real production URL when supplied. This only changes the portfolio's link, not software URLs or routes. Earlier monorepo/shared-auth proposals are not implemented.

## Local use

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`. Do not start this application in the accounting application's directory. Keep both applications as separate processes.

## Contact

The owner supplied the public phone number **01000062838**. The portfolio displays it and uses `tel:01000062838`. No country code or WhatsApp account has been assumed. Optional email and LinkedIn links appear only when `CONTACT_EMAIL` and `LINKEDIN_URL` are explicitly configured with real supplied details.

The inquiry tool prepares text locally and lets visitors copy it; it does **not** send, store, or claim delivery of a message. No portfolio database or shared authentication is introduced. No portrait, employment dates, employers, certifications, client counts, or outcome statistics have been invented.

## Deployment

The independent Dockerfile runs Gunicorn on port 3000 (or `PORT`). Health check: `GET /health`. The only public page is `/`, with in-page section anchors. `GET /manus-routes.json` declares it. There is no `/app`, `/login`, or `/invoices` route in this portfolio. A server/reverse proxy can serve the portfolio at the public root while leaving the existing software at its current host, but no live server or domain configuration has been altered.

Set `PUBLIC_ORIGIN` to the actual public portfolio origin after a domain is configured. Until then, no fabricated canonical domain is emitted. See `.env.example` for portfolio-only settings. The application reads environment variables; it does not automatically load `.env` files.

## Checks

```bash
pytest -q
node --check static/js/portfolio.js
```

`tools/capture_software.py` is a read-only demo screenshot utility that refuses capture if client/invoice lists contain records. `tools/validate_portfolio.py` checks the portfolio's mobile menu, screenshots, inquiry preparation, layout, and external link; it does not submit data to the accounting application.

Fonts: Instrument Serif and DM Sans, obtained from Google Fonts and included under their SIL Open Font License; see `static/fonts/` license files. No additional identity or company brand is created.
