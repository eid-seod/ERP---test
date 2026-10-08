# Step 2 — registration and company setup

This release adds only signup, basic company setup and Super Admin metadata visibility. Existing platform users/login/roles/settings/audit and invoices/clients remain in the original main SQLite file. Company files contain only their own version history and settings; no chart of accounts, account packs, journal entries, company invoices/reports/subscriptions or mail.

## Windows / VS Code existing demo

From the repository root, use your existing `.venv` interpreter. Stop all servers/writers first. Retain a consistent backup outside Git of your platform file. Never replace or delete it to bypass a startup error.

```powershell
git pull --ff-only origin main
.\.venv\Scripts\python.exe -m pip install -r accounting-software\requirements.txt -r portfolio\requirements.txt
# Your previously created demo: run existing Step 1 only if not already applied.
.\.venv\Scripts\python.exe accounting-software\migrations\super_admin.py --database ".\runtime\local-demo.db"
.\.venv\Scripts\python.exe accounting-software\migrations\companies.py --database ".\runtime\local-demo.db"
$env:COMPANY_DATA_DIR = Join-Path $env:LOCALAPPDATA 'EidSaeedMahmoud\company-data'
.\.venv\Scripts\python.exe deployment\run_local.py --demo
```

For real platform data, replace the migration paths with your actual EXISTING database file and start using `--database "C:\path\to\existing\database.db"` instead of `--demo`. The platform file is not moved/split. A reused old demo needs explicit migration; a genuinely fresh `--demo` initializes current metadata using the original app. Stop if any migration or Git update fails, rather than forcing/deleting records.

On an existing platform file, Step 2 startup skips the inherited `init_db`/financial backfill path entirely and refuses missing seed administrator instead of creating one. Schema/limit guards fail closed; explicit migration validates existing registry structure, not only table names. No company settings are inserted or rewritten during startup.

**Portfolio:** http://127.0.0.1:8000/ · **Original login:** http://127.0.0.1:8000/login · **Company setup:** http://127.0.0.1:8000/companies/new · **Super Admin:** http://127.0.0.1:8000/super-admin.

No default Super Admin password exists. If none was created, use the interactive existing first-only command in [Step 1 guide](super-admin-step1.md), selecting the SAME migrated platform file. Do not send or commit a password. The original demo admin email/password are not automatically changed.

## Enable registration for a demo

Login using your existing Super Admin identity. Open `/super-admin/settings` and switch **public registration** to ON; save the audited form. The default remains OFF in code/migrations. In another/private browser visit `/register`, enter name/email/password, then login using the new credentials. All public accounts receive the existing `user` role; a submitted role/permission override is ignored. The native dashboard has a **شركتي** link; `/companies/new` starts the native wizard. Do not use the Super Admin account for company workspace access: that role manages metadata only.

Signup uses the existing minimum-eight-character hashing policy. Form submits require session CSRF; the pre-existing JSON registration API remains available for same-origin integrations with its original response shape and no CORS permission for foreign origins. Successful signup is audited with the new user as actor. There is **no email verification** and no delivery claim; users should enter their real address but the app cannot prove ownership yet.

## Company setup and storage

Choose exactly industrial/contracting/trading, sole_proprietorship/joint_stock, one of EGP/USD/EUR/SAR/AED, fiscal month1–12 and optional tax ID. Egypt is fixed. Currency options and labels are centralized in `accounting-software/companies/config.py`; Egyptian VAT context does not implement VAT rules/rates/calculations now. Base currency is snapshotted into the company file with `currency_locked=false`; no change UI or future accounting logic is introduced.

Company registry and owner membership live in the same platform database. Default `max_companies_per_user=1`; Super Admin settings can change this via an audited integer form (1–100). Existing companies are not deleted if the limit decreases. Membership schema supports future multi-user use, but only active owner is implemented now. Suspended/deleted users and suspended companies cannot open a workspace.

`COMPANY_DATA_DIR` configures a private directory, not a public URL. Default is `~/.local/share/eid-saeed-mahmoud/companies`, outside source. On Windows the command above selects LocalAppData. Use local NTFS storage with hard-link support; Linux uses a local filesystem. UUID filenames are never derived from submitted names. Relative names only are stored in the registry; file traversal/absolute/symlink/non-UUID paths are rejected. Files are ignored in Git even if the owner selects an internal directory; nonetheless keep them outside source and ensure Windows ACLs restrict the service user (POSIX mode flags alone do not enforce Windows ACLs).

The only regular data opener verifies current active user/session, owner membership and active company before opening the read-only database. Workspace values come only from its own `company_settings`. The minimal per-company schema has exactly `schema_meta` and `company_settings`; dedicated versioned migrations are run only during provisioning. Super Admin list/detail/status views use platform metadata; only the health function can read `schema_meta` to check existence/readability/version. It cannot read settings or financial data. Health does not mean a complete financial audit.

## Provisioning integrity and failure handling

One service `provision_company` handles the wizard. SQLite `BEGIN IMMEDIATE` serializes owner/limit validation and registry writes. Temporary private file → company migration → settings/version → exclusive atomic placement → active registry/membership/audit commit. Handled failures remove owned temporary/final files, roll back registry and record a safe failure audit. Collision cleanup never deletes a pre-existing destination. Five fault hooks are tested; filenames/path/SQL/passwords are not exposed in responses/audit.

A SQL transaction and filesystem cannot form a distributed atomic commit. A hard process/power failure between file placement and platform commit can leave an orphan (never an active half-created registry row); unavailable storage can also prevent cleanup or failure-audit persistence. Stop writers and reconcile registry against UUID files before production restart after a crash, retaining backups; do not auto-delete unknown files. These limitations are not claimed away. No unattended reconciliation/extra environment is introduced. Keep platform+company backups consistent while writers are stopped.

## Throttle and role boundaries

Basic independent transport-IP and normalized-email attempt buckets cover login and signup using a bounded thread-safe in-app limiter. Defaults: login100/IP and30/email in300seconds; signup20/IP and5/email in3600seconds. Responses use429 and Retry-After. `AUTH_ATTEMPT_LIMITS` allows controlled app configuration. No dependency is added. Buckets are per process, reset on restart and may be evicted under high cardinality; they are not a distributed or durable brute-force defense. Behind the existing proxy the transport IP may represent the proxy, so do not trust arbitrary X-Forwarded-For headers; production needs trusted edge rate limits before broad public signup.

Existing admin/user invoices/clients remain unchanged. Original login destination remains `/dashboard`; company setup is accessed through the new link, not by rewriting login. Legacy admin can hard-delete ordinary users without companies as before; a newly linked owner is blocked from hard deletion to prevent orphaning company ownership. Use existing Super Admin soft-delete, which also revokes workspace access while retaining registry/membership.

## Private-server rollout

Use existing Compose/Nginx/domain. Add `COMPANY_DATA_DIR` in ignored `deployment/.env` pointing at an existing external private directory. Compose mounts that directory at `/company-data` in the same accounting service; the original platform `/data/database.db` mount is unchanged. Prepare owner-only filesystem permissions, stop writers/back up, explicitly apply Step1/Step2 to the existing platform file, then use the existing one-server deployment. Company files are never shipped in source/image, and portfolio remains database-free. No actual private-server deployment/DNS/TLS provisioning was performed here.

## Verification and next step

Full tests run using `python deployment/run_checks.py` in separate interpreters and external temporary fixtures; baseline and final real outputs/commit link are included in the release verification report. Historical preservation manifests remain and a Step2 overlay records authorized source integrations instead of claiming whole-app source identity.

See `docs/PROGRESS.md` for exact existing-file edits and limitations; `docs/DECISIONS.md` for the fixed decisions. The next step may define company accounting setup, but it has **not been started**. No financial tables/reports/company invoices are added.

### Legacy regression compatibility

One inherited regression expected automatic invoice timestamp migration on startup. Step2 explicitly prohibits that behavior. Its original financial preservation/idempotence assertions remain; the test now proves startup refusal, then explicitly runs the unchanged legacy migration helper against its disposable fixture. `companies/platform_guard.py` validates original financial schema/backfill readiness read-only. Existing platform app startup skips inherited init_db entirely; production preflight remains fail-closed. No business/migration implementation is changed.

### Linux private-server storage permissions

The existing accounting image runs as UID/GID10001. Create the private company-data directory manually outside source, assign it to that service user and restrict permissions before Compose (replace the path with your real intended directory):

```bash
sudo mkdir -p /srv/eid-private/company-data
sudo chown 10001:10001 /srv/eid-private/company-data
sudo chmod 700 /srv/eid-private/company-data
```

This directory must not be shared with public web uploads or untrusted writers. Set its path in ignored deployment/.env. Keep the original platform database ownership/mount unchanged. Company storage checks may refuse wrong-owner/symlink directories; fix permissions deliberately instead of making it globally writable.
