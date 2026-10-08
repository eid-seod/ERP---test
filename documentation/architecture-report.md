# Unified architecture and verification report

## Outcome and truthful status

| Requested result | Status | Evidence / limitation |
| --- | --- | --- |
| ✅ One Git repository **in deliverable** | Verified | Consolidated into original ERP repository with imported portfolio history; `portfolio/` and `accounting-software/` are ordinary folders, not nested repositories. Access is restored; final push/commit check is in the release evidence. |
| ✅ One server architecture | Configured and preview-verified | One Compose project, Nginx + private app services on one server; same-origin Sandbox proxy worked. The owner's private production server is **not deployed or inspected**. |
| ✅ One domain ecosystem | Configured | One owner-supplied `DOMAIN` parameter and one Nginx public site; no domain was created. Owner's real DNS/TLS are still required. |
| ✅ One accounting database | Preserved locally | Existing SQLite file moved with identical bytes and inode; portfolio has no database, no new database volume. No production database was connected. |
| ✅ Accounting software unchanged | Verified | All 22 tracked original files exactly match baseline SHA manifest. Its schema and data hash match; no app routes, screens, auth, roles, modules or branding were edited. |
| ✅ Portfolio connected | Verified in preview | Arabic portfolio at `/`; button opens original `/login` on the same origin. Authenticated original read routes worked through proxy. |
| ✅ Arabic public website | Verified | RTL `lang=ar`, Arabic nav/content/articles/inquiry messages, English accounting/ERP terminology preserved. The protected accounting UI remains unchanged and is not translated. |
| ✅ Blue-and-white identity | Verified in portfolio | Corporate cobalt/white styling and personal-name identity; no new brand. Original accounting branding intentionally unchanged. |

## Repository and processes

Original repository retained: `eid-seod/ERP---test`. Original accounting baseline commit `551f23d49e75cb296cbf61e7162fc04fe7c730bc`; portfolio Git history imported by `git subtree add --prefix=portfolio` (no squashing). Accounting files were `git mv`-relocated into `accounting-software/` without editing. An initial credential failure was resolved; fetching remote main confirmed it is an ancestor of the consolidated history, so no force-push or replacement repository is needed. The final remote SHA is recorded in the delivered release evidence alongside the ZIP and one repository bundle.

The separate managed portfolio from the previous task may remain published independently as a **legacy environment**. This request does not authorize silently deleting existing hosting or Git history. It is not referenced by this release and should be retired after owner-controlled cutover. The one-production-environment goal is thus **prepared**, not yet a fact of the current world.

Private-server design: `deployment/compose.yml` defines `web` (Nginx, only ports 80/443 exposed), `portfolio` (private WSGI), `accounting` (private original WSGI). This is one server, one Compose project, one domain. Application separation is necessary to preserve the accounting code and its original root-level URLs. Nginx routes public root and blog to portfolio, original accounting paths to the original app; no path rewriting. TLS and proxy cookie flags belong to deployment, not accounting code.

## URL and data boundaries

| Route | Service |
| --- | --- |
| `/`, `/#about`, `/#services`, `/#projects`, `/#accounting-software`, `/#blog`, `/#contact` | Arabic portfolio |
| `/blog/<slug>`, `/portfolio-assets/*`, `/shared-assets/*`, `/health` | Arabic portfolio |
| `/login`, `/logout`, `/register`, `/me`, `/dashboard`, `/users*`, `/clients*`, `/invoices*`, `/invoice/*`, `/static/*` | Original accounting app, unchanged |

SQLite contains original tables `users`, `clients`, `invoices`, `invoice_items`, `invoice_audit_trail`; `PRAGMA integrity_check=ok` and `PRAGMA foreign_key_check` found zero violations in the received file. Existing business data remains solely in that database. `documentation/accounting-preservation.json` records source/data hashes; `deployment/verify_preservation.py` checks them read-only. The database is excluded from Git and Docker image builds. During deployment use your existing database directory; do **not** replace live records with the received demo file.

## Verification performed

Nine portfolio unit tests, six unchanged accounting regression tests, and eight deployment guard tests passed in separate module test processes. JavaScript syntax passed; one proxy served Arabic homepage and original login/read routes at the same HTTPS preview origin; database stayed hash-identical. Portfolio interaction checks passed at 320–1440 px, including mobile navigation, genuine screenshot dialog, blog, same-origin link and an Arabic inquiry that is never sent. Nginx syntax and Compose model validated. The independent review identified inherited startup migrations/seeding: deployment-only checks now reject known schema/backfill/seed requirements before importing the frozen app; its original startup logic is still present and requires a quiescent backed-up database. HTTP and public embedded-HTTPS cookie modes are separate. Docker image build, host TLS, live DNS and real private-server cutover were not executed here.

## Before public cutover

Use this **same original repository** without force-pushing; follow `documentation/deployment-guide.md`; use your existing server/domain/certificates; select and back up the real existing accounting database; check filesystem permissions, rotate default admin credentials, evaluate public registration, review security and tax behavior of the **frozen** accounting app, and test login/roles/invoicing on a staging copy before exposing production. Do not modify the frozen app as an unreviewed side effect of consolidation. Once the new private server is live and verified, retire the old independently hosted portfolio through its authorized management controls. Until then, do **not** assert that one production environment already exists.
