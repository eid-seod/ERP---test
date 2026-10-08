# Private-server deployment guide

## What this delivery is

One source repository and one deployment definition for Eid Saeed Mahmoud's Arabic portfolio plus the existing accounting app. This is a **portable package**, not a claim that your production server/domain has already been configured. The existing repository target remains `eid-seod/ERP---test`; no new repository/domain/server/database has been provisioned.

Production topology: one Linux server → one HTTPS domain → one Nginx proxy → two private WSGI services. Two application processes are modular separation within one deployment, not two production environments. Only accounting uses SQLite. Portfolio has no database or login. Accounting retains its original screens, language, branding, routes, roles and workflows.

## 1. Restore the single Git repository

The source ZIP is convenient for upload; the accompanying `.bundle` contains the **one consolidated repository's history**, including the preserved accounting history and imported portfolio history. Do not run `git init` separately inside either module.

```bash
git clone /path/to/Eid-Saeed-Mahmoud.bundle eid-saeed-mahmoud
cd eid-saeed-mahmoud
# The bundle clone initially has a local-file origin; point this one repo back to the existing target.
git remote set-url origin https://github.com/eid-seod/ERP---test.git
```

The bundle and Git do not contain database data or secrets. The release ZIP additionally includes the received `accounting-software/database.db`. Use it only if this received demonstration database is the database you intend to preserve. **Never replace a live database with the demonstration database.** If you already operate accounting elsewhere, use that existing database after confirming version compatibility and backing it up.

To upload the finished source to GitHub after restoring authorized access:

```bash
git fetch origin main
# Inspect any remote advances and integrate them normally; do not reset or force-push.
git log --oneline --left-right main...origin/main
git push origin main
```

Access was initially invalid and was restored during this task. The final commit and remote verification are recorded in the release evidence. The old managed portfolio source is not a second source of truth for this release. Do not keep maintaining it separately.

## 2. Server prerequisites

Use your existing private Linux server and domain. Install Docker Engine and the Docker Compose plugin using the distribution's official instructions. Permit inbound HTTPS (443) and HTTP (80 for redirection), and restrict administration appropriately. Do not expose the WSGI services directly. Ensure you have sufficient disk for images, logs and backups; no server sizing has been verified because production access was not provided.

Supply an existing valid TLS certificate and key for your domain. This package does not register domains or request certificates. Certificate renewal remains your existing server administration responsibility.

## 3. Preserve the database before cutover

Stop the old accounting writer before moving the database into its durable location; do not run old and new production accounting instances against it simultaneously. Take a SQLite-consistent backup before any cutover. The portable release database was moved within the workspace using the same inode and remained hash-identical:

```text
SHA-256: 35a670d9bf59d97c21db14e735054fa3a25422361308cc5bf5680aa30504cc9f
```

`ACCOUNTING_DATA_DIR` must be an **existing absolute directory containing `database.db`**. It is mounted at `/data`; the original app reads `sqlite:////data/database.db`. Do not create a fresh database or run migration scripts to make an arbitrary database match this version. The deployment guard checks existing tables/integrity and refuses to start on a missing or incompatible file.

Grant container UID/GID **10001:10001** write access to the existing database file and its directory (SQLite needs journal-file access). On a dedicated database directory, review ownership first, then apply only necessary permissions. Do not recursively change unrelated application/server directories. No role/permission changes inside the accounting software are made by this package.

After legitimate accounting transactions, its data hash will naturally change. `python3 deployment/verify_preservation.py --source-only` still verifies the protected application source. The recorded database hash is proof of packaging preservation, not a requirement to keep future business data frozen.

## 4. Configure one environment

```bash
cp deployment/.env.example deployment/.env
chmod 600 deployment/.env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Edit `deployment/.env` locally. Do not send private keys, passwords or secrets through chat. Required values:

| Setting | Required value |
| --- | --- |
| `DOMAIN` | Your existing domain hostname only, without scheme/path |
| `SECRET_KEY` | The newly generated strong random value, stable across restarts |
| `ADMIN_PASSWORD` | Strong original-app seed fallback, at least 12 characters; it does not rotate existing passwords |
| `ACCOUNTING_DATA_DIR` | Existing absolute persistent directory with `database.db` |
| `TLS_CERT_FILE` | Existing absolute path to full certificate chain |
| `TLS_KEY_FILE` | Existing absolute path to matching private key |

The supplied public phone `01000062838` is configured in Compose. No email, country code, WhatsApp account, portrait or employer history is invented. `PUBLIC_ORIGIN` is derived from your supplied domain for portfolio SEO only, not from a request Host header.

## 5. Start both modules from this one source

From repository root:

```bash
docker compose --env-file deployment/.env -f deployment/compose.yml config --quiet
docker compose --env-file deployment/.env -f deployment/compose.yml up -d --build
docker compose --env-file deployment/.env -f deployment/compose.yml ps
docker compose --env-file deployment/.env -f deployment/compose.yml logs --tail=100
```

Nginx waits for healthy upstreams. Accounting uses one Gunicorn worker, suitable for the preserved SQLite setup; portfolio uses two. The deployment guard runs before the accounting import and refuses missing settings/database, missing or mismatched required columns, missing original seed administrator, and records that would trigger known timestamp/item-name backfills. The original app still runs its inherited `init_db()` and admin-check logic; it is not bypassed or patched. The guard prevents those known migration/seed branches for a compatible quiescent database; stop the old writer first, retain a backup, and do not claim protection against concurrent changes. A database needing migration is rejected for separately approved review, not silently upgraded. The configured strong `ADMIN_PASSWORD` avoids a predictable fallback if the original seed path were inadvertently reached, but never changes an existing user's password. No new database volume or separate server is created. Build images exclude databases, `.env`, certificates and Git metadata.

Expected URLs on your supplied domain:

| URL | Owner/purpose |
| --- | --- |
| `/` | Arabic personal portfolio |
| `/#about`, `/#services`, `/#projects`, `/#accounting-software`, `/#blog`, `/#contact` | Portfolio sections |
| `/blog/financial-reporting-clarity` | Arabic financial-reporting article |
| `/blog/cash-flow-planning` | Arabic cash-flow article |
| `/blog/erp-implementation-foundations` | Arabic systems article |
| `/login` | Original accounting login |
| `/dashboard` | Original authenticated accounting Dashboard |
| `/invoice/new`, `/invoice/<id>/edit` | Original invoice screens |
| `/invoices`, `/clients`, `/users`, `/me`, `/register`, `/logout` | Original accounting routes/APIs |
| `/static/*` | Original accounting assets |
| `/portfolio-assets/*`, `/shared-assets/*` | Public portfolio-only assets |
| `/health` | Portfolio health |

Original accounting URLs are forwarded without a prefix/URI rewrite. Its existing login JavaScript navigates to `/dashboard`, so replacing the public root does not interrupt that flow. Login/register/logout and invoice logic are unchanged. TLS/cookie flags and noindex/no-store headers are applied by the proxy; they do not grant permissions or replace accounting authentication.

The optional local `deployment/start_preview.py` helper defaults to an **HTTPS public embedded-preview** context and adds `Secure; SameSite=None` to session cookies. When testing directly over plain local HTTP instead, pass `--plain-http` to omit Secure and use SameSite=Lax. Never use that option for the public embedded Preview. The delivered public same-origin authenticated check used HTTPS, not local HTTP.

## 6. Production verification and risk decisions

Verify portfolio Arabic/RTL, assets, article links, and contact behavior. Verify accounting login/roles and business workflows against a proper test database **before** using production data. Nine portfolio tests, same-origin read-only demo login/API checks, preservation checks, responsive checks and native proxy/Compose configuration checks are supplied; Docker image execution and your private-server/TLS/domain checks still need to occur on the target server.

The instruction to freeze accounting source means inherited issues are **not silently fixed**. Before broad public access, rotate the seeded/default administrator credentials through the existing administration process, review public registration exposure, add login rate limiting at your perimeter if appropriate, review original CSRF exemptions and client-delete cascades, review fiscal/tax treatment and permissions, and test concurrent invoice creation/edits. Source changes for such improvements require a separately agreed scope; do not assume TLS alone solves application security.

Keep encrypted off-server backups and test restoration. Schedule any backup jobs using your own server administration process; this package does not provision unattended tasks. Do not run the old managed deployment and the new server as two active production sources. After successful cutover, retire the legacy independently published portfolio through its authorized hosting controls. It has not been deleted here.

## Known validation boundary

Docker Engine is unavailable in the task Sandbox. The Compose model was validated with the official standalone Compose plugin, and native Nginx served the actual same-origin preview. **A parsed Compose file is not a successful container rollout.** Your domain, certificate and server access were not supplied; they remain deployment inputs. No new cloud publication was triggered.
