# Eid Saeed Mahmoud — unified portfolio and existing accounting application

A single portable Git repository for a personal Arabic RTL portfolio and the **unchanged existing accounting application**, ready to configure on the owner's private server. No new product identity, custom domain, database, or hosting environment is created.

```text
/
├── portfolio/             # Arabic public homepage, services, project showcase, blog, contact
├── accounting-software/   # Original accounting files unchanged; existing SQLite stays private
├── shared-assets/         # Portfolio's Arabic fonts/license and blue personal monogram
├── documentation/         # Architecture, deployment, preservation and verification evidence
└── deployment/            # One Compose environment, Nginx, production WSGI and safety checks
```

## Key guarantees

All 22 original tracked accounting files are byte-identical to baseline `551f23d49e75cb296cbf61e7162fc04fe7c730bc`. Its existing database was moved, not recreated. Original Git history is retained, and portfolio history was merged under `portfolio/`. No nested Git repository or submodule. Current accounting branding and UI language are deliberately preserved; Arabic/RTL applies to the public portfolio.

Public URL `/` introduces **عيد سعيد محمود**. The featured software button opens the existing `/login` on the **same origin**. Original routes `/dashboard`, `/invoice/*`, `/invoices`, `/clients`, `/users`, `/me`, `/register`, `/logout`, and `/static/*` remain owned by accounting. Portfolio assets are `/portfolio-assets/*`; shared assets are `/shared-assets/*`. No portfolio database or shared-login rebuild is introduced.

## Deployment

Use **[the deployment guide](documentation/deployment-guide.md)** and **[architecture report](documentation/architecture-report.md)**. Supply your own existing domain, TLS certificate, strong secret and persistent existing SQLite directory in `deployment/.env`, then from this repository root:

```bash
docker compose --env-file deployment/.env -f deployment/compose.yml config --quiet
docker compose --env-file deployment/.env -f deployment/compose.yml up -d --build
```

Only Nginx exposes 80/443. Portfolio and accounting are private services on that one server. The existing SQLite directory is a bind mount; startup refuses to silently create a fresh database. Back up before cutover. Never overwrite a live database with a demonstration database.

## Source and publication status

Retained GitHub repository: `https://github.com/eid-seod/ERP---test`. Authorized access was restored during consolidation; source history is preserved and normal non-force Git updates use this same repository. The portable release and one Git history bundle contain the consolidated tree. The accompanying release verification records the exact final commit and remote check; never create another repository or force-push.

The local combined preview is not the owner's production server. No new production publication or domain provisioning occurred. A prior managed portfolio deployment, if still online, is legacy and outside this self-hosted release; retire it after successful private-server cutover rather than maintaining a second source/deployment.

## Preservation and checks

```bash
python3 deployment/verify_preservation.py
(cd portfolio && pytest -q)
node --check portfolio/static/js/portfolio.js
```

`--source-only` checks code after legitimate business data changes. The release includes the received demo SQLite file for continuity; it is excluded from Git and Docker images. Original application security risks are documented, not silently patched against the instruction to keep accounting unchanged. Review them before public production use.
