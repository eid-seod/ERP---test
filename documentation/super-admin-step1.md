# Step 1 — Super Admin

Only the user-administration area was added. Repository, five module directories, portfolio, login markup, existing accounting CSS/JS and invoice/client business logic remain in place. Baseline tag: `baseline-before-super-admin` at `6520a315bae99bf9b6a49a08341ff5be70c73828`.

## What is included

- `/super-admin`: user counts, per-role counts, successful logins recorded in the last seven days, latest ten user audit events, release/environment labels.
- `/super-admin/users`: name/email search, role/status filters, allowlisted sorting and pagination.
- Create/edit roles and profiles; activate/deactivate, password reset, soft delete/restore; detail with UTC dates and user audit history.
- `/super-admin/audit`: actor/action/date range filters and pagination. User-only table, no financial data or password/hash values.
- `/super-admin/settings`: only `public_registration_enabled`; default OFF. Both GET and POST `/register` return 404 when OFF. The original POST registration behavior returns when enabled; no new registration page.
- Active Super Admin only. Existing admin/user roles receive 403; unauthenticated visitors use the unchanged `/login`.

The native shell is the existing accounting `templates/dashboard.html`, extended with inert Jinja blocks. Original defaults and styling are retained. New pages extend that shell, use `static/css/app.css`, and load only `super_admin.js`, never the financial dashboard script. The Super Admin link appears only for that role.

## Deliberately unsupported

The existing app has no lockout/rate-limit concept and no mandatory-password-change flow. Locked count explicitly reports **0 / unsupported**; there is no unlock button or invented must-change flow. Temporary passwords use the existing minimum-eight-character policy and Werkzeug hashing. Generated passwords appear only in the immediate no-store response, not cookies, later profiles or audit. Manually supplied passwords are not echoed.

## Explicit migration of YOUR existing database

The received database was **not migrated in place** during implementation. Tests use disposable files outside Git. Do not replace any business database with a fixture or demo.

1. Stop all writers and retain a consistent backup **outside the repository**.
2. Use the database already compatible with this repository's accounting version. The migration does not fix old invoice/client schemas or populate financial tables.
3. From the repository root, run the idempotent standalone migration. Replace the path with YOUR real existing file:

```powershell
.\.venv\Scripts\python.exe accounting-software\migrations\super_admin.py --database "C:\path\to\existing\database.db"
```

Linux equivalent:

```bash
.venv/bin/python accounting-software/migrations/super_admin.py --database /absolute/path/to/existing/database.db
```

The migration requires an existing file/users table. It adds only `users.deleted_at`, `users.last_login_at`, `users.session_epoch`, `user_audit_events`, `platform_settings`, user-audit indexes and a unique `lower(email)` index. Existing user fields/credentials and all financial rows are retained. Existing case-insensitive duplicate emails cause a refusal before schema changes; the owner must review them—no account is merged, renamed or deleted automatically. Running migration twice is safe. The deployment/local preflight and direct application initialization reject an unmigrated existing users schema before original initialization; they never silently migrate it. Fresh explicit demo/test initialization retains the original new-database behavior and creates the current schema; reused old demo files need this migration.

## Create the FIRST Super Admin (Windows / VS Code)

Use the same venv documented in root README. Open PowerShell in the repository root. Set the existing database URL using its resolved path and generate non-default runtime secrets locally; generated values are not committed or included below:

```powershell
$db = (Resolve-Path "C:\path\to\existing\database.db").Path.Replace('\','/')
$env:DATABASE_URL = 'sqlite:///' + $db
$env:SECRET_KEY = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))")
$env:ADMIN_PASSWORD = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(24))")
$env:APP_ENV = 'development'
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'deployment'); from accounting_entrypoint import preflight; preflight()"
.\.venv\Scripts\python.exe -m flask --app accounting-software/app.py create-super-admin
```

Enter your email and password in the interactive prompts; password input is hidden and confirmation is requested. No default is supplied/printed. Optional protected environment inputs: `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD`, `SUPER_ADMIN_NAME`. Clear the password environment variable when finished. Never put these values in README, test files, command history literals or a tracked `.env`.

CLI creates a new account only and refuses duplicate email or an already existing Super Admin. It does not promote/rotate an existing user silently. All subsequent Super Admin creation/role changes use the authenticated Super Admin area. Bootstrap is audited with its new identity as actor/target.

Run both modules on the original local origin:

```powershell
.\.venv\Scripts\python.exe deployment\run_local.py --database "C:\path\to\existing\database.db"
```

Open **http://127.0.0.1:8000/** for the unchanged Arabic portfolio; **http://127.0.0.1:8000/login** for the original accounting form. Enter the NEW Super Admin email/password instead of the inherited demo values prefilled by that unchanged form. Its existing successful-login destination remains `/dashboard`; use the Super Admin navigation link or **http://127.0.0.1:8000/super-admin**.

## Safety and compatibility

All new writes require a nonempty valid existing CSRF token and POST/PUT/DELETE; GET/PATCH cannot perform an administrative mutation. Server-side transactions enforce no self-deactivation/deletion/demotion and preservation of the last active Super Admin. The actor is revalidated inside the SQLite write lock. Concurrent cross-deactivations cannot remove both administrators.

Deactivation, soft delete, password reset and role change revoke old sessions on the next request using a session epoch. The user must sign in again after reset/role changes. Restoring a deleted user leaves it inactive; activate explicitly in a separately audited action. Deleted emails remain reserved for their existing record.

Legacy admin/user permissions remain intact for their existing operations, except the requested registration setting, immediate disabled/revoked-session rejection and protection of Super Admin identities. The pre-existing admin endpoint can still hard-delete an ACTIVE ordinary user; it cannot hard-delete a Super Admin or an already soft-deleted user. New Super Admin management **never hard-deletes**. User audit references are detached safely if that retained legacy action removes a normal account; historical actor labels/events remain.

No Super Admin request queries invoices, invoice items, clients or invoice audit. The existing financial pages/routes remain outside this new area and are not rebuilt. Successful-login history starts with this release; it is not inferred or fabricated for earlier sessions. IP is Flask's available transport address; untrusted forwarded-header values are not substituted automatically.

## Production update

Use the existing single Compose deployment, existing domain and same SQLite file. Stop writers, back up outside Git, explicitly migrate, bootstrap the first Super Admin against the same file, then start the existing services. Production composition supplies `APP_ENV=production`; optional `APP_VERSION` overrides `super-admin-step1`. In the built accounting image the explicit migration is `/app/accounting-software/migrations/super_admin.py`, and the first-creation command is `python -m flask --app app.py create-super-admin` (interactive one-off container, same mounted DB/environment, not a second database). Docker image execution/private-server cutover were not performed during this task.

## Checks

```powershell
.\.venv\Scripts\python.exe deployment\run_checks.py
.\.venv\Scripts\python.exe deployment\verify_preservation.py --source-only
```

Use the isolated full-suite runner, not root-level bare pytest (the portfolio/accounting both use `app.py`). The accounting bootstrap database is isolated outside Git. Received-data deployment regressions use migrated temporary copies outside Git and still require the original compatible received fixture in this workspace; a source-only fresh clone has no bundled business database. Preservation retains the historical manifest and transparently permits only the five recorded Step 1 accounting-source edits. After your approved migration or normal business use, choose `--source-only`; original byte identity is intentionally no longer expected for a legitimately changed database.
