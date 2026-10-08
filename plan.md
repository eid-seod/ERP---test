# Eid Saeed Mahmoud — Portfolio plan

## Approved scope and boundaries

Build a public portfolio for Eid Saeed Mahmoud, positioned as Accounts Manager, Finance Professional, and Accounting Systems Specialist. Home page sections: About Me, Experience, Professional Services, Projects, Contact; a Financial Systems / Accounting Software featured project has screenshots, features, benefits, and an **Open Software** external link. Services cover remote accounting, financial management, Odoo & Zoho Books implementation, accounting system setup, and financial assessment & improvement.

The existing accounting application at `/home/ubuntu/ERP---test` is not part of this implementation. Its baseline commit is `551f23d49e75cb296cbf61e7162fc04fe7c730bc`. Do not edit its files, brand, database, routes, authentication, workflow, permissions, Git history, or repository structure. Capture read-only screenshots of empty demo screens only. Do not seed data, copy its code, iframe it, proxy it, or recreate its UI in the portfolio.

The current external software link is `https://5051-ii9x7ilv6lmzhug9n1g1o-684bafc5.sg2.manus.computer/login`, clearly identified as a temporary preview. `ACCOUNTING_SOFTWARE_URL` can replace that link in the portfolio only when a real production URL is supplied. No software route is changed. The latest instruction supersedes earlier monorepo and shared-auth plans.

The owner supplied public phone **01000062838** during implementation. Display the exact number with `tel:01000062838`. No country code, WhatsApp account, email, LinkedIn URL, or portrait was provided, so do not invent any of them. The inquiry helper prepares a message only; the supplied phone is the direct contact method.

## Implementation

A standalone Flask-rendered public website with vanilla JavaScript and CSS; no database, no portfolio authentication, no calls from visitors to private accounting APIs. Static screenshots are portfolio assets captured with read-only demo access. Only route `/` renders the public page, with section anchor navigation. `/health` is deployment readiness; `/manus-routes.json` declares the public page route. Contact uses only configured, supplied contact details. Until supplied, visitors can prepare and copy an inquiry; nothing is silently sent or stored. No made-up employers, tenure, achievements, certificates, email, phone, partnerships, or person images.

Project structure:
- `app.py` — portfolio app factory, server-rendered home, health, routes manifest
- `content.py` — truthful user-supplied roles, services, and featured project content
- `templates/index.html` — public page, semantic sections, metadata, inquiry preparation
- `static/css/portfolio.css` — responsive editorial design
- `static/js/portfolio.js` — mobile navigation, screenshot viewer, inquiry copy behavior
- `static/images/` — actual read-only software screenshots, initials favicon
- `tests/` — route, copy, external-link, security, isolation checks
- `tools/` — read-only screenshot and validation utilities
- `Dockerfile`, `requirements.txt`, `.env.example` — independent Flask/Gunicorn serving configuration

Production uses Gunicorn on port 3000 (honors PORT), serves SSR and static files, and is configured independently of the software. Save a Manus checkpoint only; do not publish to a live domain or reconfigure a production server without a request. No existing server credentials or actual personal domain are available.

## Design direction

**Design movement:** contemporary editorial / Swiss typographic discipline with warm paper surfaces.
**Core principles:** person-first hierarchy; confident negative space; clear functional access; evidence without invented credentials.
**Color philosophy:** ivory and deep ink convey professionalism without corporate coldness; forest-green highlights signal considered financial judgment; muted bronze supports supporting labels.
**Layout paradigm:** left-aligned oversized two-column hero, an offset numbered expertise ledger on the right, horizontal service rows and asymmetric project narrative/screenshot treatment; no repetitive all-card layout.
**Signature elements:** large serif headline, thin editorial rules, numbered section markers, small green outlined labels.
**Interaction philosophy:** simple anchor navigation; one unmistakable external software button; honest contact feedback. Screenshots open in an accessible native dialog.
**Animation:** 180–250ms hover/focus transitions; subtle CSS hero entrance; no scroll-jacking; reduced-motion respects accessibility settings.
**Typography:** locally served Google Fonts assets if accessible: DM Sans for body/navigation, Instrument Serif for display headings. System sans/Georgia fallbacks. Display name approximately 76px desktop / 46px mobile; body 16–18px.
**Brand essence:** Eid Saeed Mahmoud connects accounting expertise with practical systems for clearer business decisions. Precise, approachable, dependable.
**Brand voice:** direct, first-person and service-oriented: “Financial clarity. Practical systems.” and “Explore a solution from my professional practice.” No fake metrics or promises.
**Wordmark:** typographic personal name next to a simple ES initials mark; no independent software logo or new brand name.
**Signature brand color:** forest green `#24644B`.
