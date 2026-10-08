# Arabic personal portfolio — Eid Saeed Mahmoud

This is the public-facing module of the single repository, not an independent product or separately managed website. Main identity: **عيد سعيد محمود — مدير حسابات | متخصص مالي** (Eid Saeed Mahmoud — Accounts Manager | Finance Professional).

The portfolio is Flask-rendered Arabic RTL with vanilla JavaScript, self-hosted Tajawal, blue-and-white executive design, twelve professional services, an existing-software project showcase, three Arabic blog articles, and the supplied phone number `01000062838`. The inquiry tool only prepares/copies a local message; it does not send or store visitors' data.

The Accounting Software access button uses **`/login` on the same origin**. The repository's reverse proxy forwards that request to `accounting-software/`. This module never imports the accounting app, creates a database, duplicates its screens, or changes its authentication. Screenshots are genuine unchanged empty-demo screens; Arabic captions surround them. The accounting application itself retains its original UI language and branding as requested.

Use the single deployment definition in `../deployment/compose.yml`; there is intentionally no separate portfolio Dockerfile or external software URL setting. For public-origin SEO, deployment supplies the owner's actual domain; none is invented. Development and production instructions are in `../documentation/deployment-guide.md`.

Tests run from this folder: `pytest -q` and `node --check static/js/portfolio.js`. `tools/validate_portfolio.py` performs read-only portfolio interactions through the unified port-3000 proxy; it does not modify accounting data.
