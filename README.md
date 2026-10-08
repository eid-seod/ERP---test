# Eid Saeed Mahmoud — Arabic portfolio + existing accounting application

**Canonical repository: https://github.com/eid-seod/ERP---test — branch `main`.** One repository, one private-server deployment configuration, one public domain. The Arabic RTL blue-and-white portfolio is the public homepage; the existing accounting app is one featured professional solution, not copied, rebuilt or renamed. The authorized **Step 1 Super Admin** extension changes only user administration/authentication metadata and native navigation; invoice/client business logic and existing branding/styles remain unchanged.

```text
/
├── portfolio/             # Arabic homepage, services, projects, blog, contact
├── accounting-software/   # Existing accounting + scoped Super Admin user administration
├── shared-assets/         # Self-hosted Arabic fonts/license and personal monogram
├── documentation/         # Architecture, deployment and preservation evidence
└── deployment/            # Local launcher + one production Compose/Nginx configuration
```

## 1. Verify or update your clone

Run in the repository folder, not its `accounting-software` subfolder:

```powershell
git remote -v
git fetch origin
git switch main
git pull --ff-only origin main
git log --oneline -5
git ls-tree --name-only HEAD
```

Expected remote: `https://github.com/eid-seod/ERP---test.git`. You should see the five folders above. The unified history includes commit `346e6bf` (portfolio/accounting consolidation) and `dcdf2c6` (verified delivery record); later commits add local-run improvements. A checkout showing only the old root `app.py`, `models` and `routes` is not the current unified `main`.

If Git reports local changes or cannot fast-forward, **stop and preserve your work**; do not use `reset --hard`, `clean`, force-push, or overwrite any existing database. An ignored old root `database.db` is not automatically moved by pulling Git. Keep it and pass its actual path with `--database` as explained below.

## 2. Windows + VS Code — exact local steps

Prerequisites: Git, Python **3.11+** (installed with PATH enabled), and VS Code with the Python extension. Use `python`, **not `py`**; the Windows `py` launcher is not required. Check `python --version` first. If it is unavailable, select/install your real Python executable before proceeding.

For a fresh clone, open PowerShell:

```powershell
git clone https://github.com/eid-seod/ERP---test.git
cd ERP---test
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r accounting-software\requirements.txt -r portfolio\requirements.txt
```

Open this **root folder** in VS Code using **File → Open Folder → ERP---test** (or `code .` if the command is available). Run **Python: Select Interpreter** from the Command Palette and choose `.venv\Scripts\python.exe`. Open **Terminal → New Terminal**, using PowerShell, and run one of the two options below from the root folder. Explicitly calling the venv Python avoids PowerShell activation/execution-policy problems.

### Option A — use your EXISTING compatible database (recommended for existing users)

Replace the quoted path with the real file you already use; leave it where it is:
**For an existing pre-Super-Admin database, first stop writers, back up outside Git and run the explicit additive migration in [Step 1 instructions](documentation/super-admin-step1.md).** The launcher refuses an unmigrated file; it does not silently upgrade it.

```powershell
.\.venv\Scripts\python.exe deployment\run_local.py --database "C:\Users\Eid - PC\Documents\ERP - test\database.db"
```

The launcher points the original app at that exact file. It does not copy, move, reset, seed or automatically upgrade it. A read-only preflight refuses missing/incompatible tables/columns, pending original backfills or missing seed administrator before importing the original app. If refused, back up and review compatibility separately; **do not point it to a different empty file to hide the error**. Original app startup still executes inherited initialization after preflight, so stop competing writers and retain a backup. Existing passwords and business data are not intentionally changed.

### Option B — explicit disposable DEMO for a fresh clone with no database

Git deliberately contains **no database**. To try both modules without supplying real business data:

```powershell
.\.venv\Scripts\python.exe deployment\run_local.py --demo
```

This explicitly creates/reuses **ignored `runtime/local-demo.db`**, never an existing real database. On first creation, choose a local demo administrator password (at least 12 characters) in the terminal prompt. Login email is `admin@example.com`; use that chosen password. On subsequent runs, it reuses the demo and existing credentials. The original app performs its own normal initial setup; the launcher does not implement a second accounting system. Do not use demo mode for production or business records. Passwords are never written to Git or printed by the launcher.

**If a previously created demo refuses startup after the Super Admin update:** do not delete/reset the file. Stop the app and keep a consistent backup outside Git first. For a file created with `--demo`, run from this root folder:

```powershell
.\.venv\Scripts\python.exe accounting-software\migrations\super_admin.py --database ".\runtime\local-demo.db"
.\.venv\Scripts\python.exe accounting-software\migrations\companies.py --database ".\runtime\local-demo.db"
.\.venv\Scripts\python.exe deployment\run_local.py --demo
```

This explicit migration adds only the Super Admin user metadata/tables/index, preserving existing credentials and financial rows. It does not resolve unrelated missing financial tables or automatically merge duplicate emails. If migration fails or startup still refuses, stop and review that exact error; do not replace the database with an empty file. See [the complete migration/first-admin guide](documentation/super-admin-step1.md).

Step 2's separate `companies.py` command adds the company registry/memberships and numeric company limit to that SAME platform file. Existing invoice/client tables are not moved or changed. [Step 2 Windows/storage/setup guide](documentation/step02-companies.md) explains the external company-data directory and registration toggle.

### URLs to open

Keep the terminal running and open:

- **Arabic portfolio:** http://127.0.0.1:8000/
- **User/legacy admin login:** http://127.0.0.1:8000/login
- **Super Admin login:** http://127.0.0.1:8000/super-admin/login
- **User registration (when enabled):** http://127.0.0.1:8000/register
- **Accounting Dashboard after login:** http://127.0.0.1:8000/dashboard
- **Example Arabic article:** http://127.0.0.1:8000/blog/cash-flow-planning

If 8000 is busy, append `--port 8001` and use that port consistently. Press **Ctrl+C** to stop. The launcher is loopback-only, no debug/reloader, and intended for local development—not production. Do **not** run `accounting-software/app.py` alone when you expect the portfolio: the accounting app's own original `/` route redirects to its login/Dashboard. The combined launcher routes `/` to portfolio and `/login` to accounting without editing either app's route handlers.

Linux/macOS equivalent after creating/installing a virtualenv:

```bash
.venv/bin/python deployment/run_local.py --database /absolute/path/to/existing/database.db
# Or explicitly: .venv/bin/python deployment/run_local.py --demo
```

## 3. Where the portfolio files and routes are

| Purpose | Tracked source / route |
| --- | --- |
| Arabic homepage | `portfolio/templates/index.html`, layout `portfolio/templates/base.html` |
| Handler for `/` | `portfolio/app.py`: `@app.get('/')`, `home()` → `render_template('index.html', ...)` |
| CSS, JavaScript and real software screenshots | `portfolio/static/css/portfolio.css`, `portfolio/static/js/portfolio.js`, `portfolio/static/images/` |
| `/portfolio-assets/*` | Flask's **URL prefix**, configured by `static_url_path='/portfolio-assets'`; physical files are under `portfolio/static/`, not another root folder |
| Arabic blog pages | `portfolio/templates/article.html`, content in `portfolio/content.py`, handler `/blog/<slug>` |
| Local same-origin routing | `deployment/run_local.py`; forwards original paths without stripping or rewriting them |
| Production same-origin routing | `deployment/routing.conf`; `/` goes to portfolio, original `/login`, `/dashboard`, `/invoice/*`, APIs and `/static/*` go to accounting |

The historical accounting manifest is retained at baseline `551f23d49e75cb296cbf61e7162fc04fe7c730bc`. Authorized Step 1/Step 2/login-interface overlays retain precise change evidence; this is not whole-app source identity. Invoice/client business logic, financial accounting CSS/JS, branding and portfolio content are unchanged. Login interfaces are now separately authorized: user/admin at `/login`, Super Admin at `/super-admin/login`. Public phone is the supplied `01000062838`. Inquiry preparation sends/stores nothing; no other personal details or country code are invented.

## 4. Private-server production deployment

Follow [the deployment guide](documentation/deployment-guide.md) and [architecture report](documentation/architecture-report.md). Supply your existing domain/TLS, strong secret/admin fallback, and existing persistent SQLite directory in ignored `deployment/.env`:

```bash
docker compose --env-file deployment/.env -f deployment/compose.yml config --quiet
docker compose --env-file deployment/.env -f deployment/compose.yml up -d --build
```

Only Nginx exposes 80/443; two private WSGI services run on that one server. Portfolio has no database and no separate authentication. Local launcher does not replace production Compose. Rotate demo credentials and review inherited application risks before public use. No private production server/DNS/TLS deployment or new domain provisioning has been performed here. Any previous independent managed portfolio is legacy and should be retired after verified private-server cutover.

## 5. Data and secrets are NOT committed

Root `.gitignore` includes `*.db`, `.env`, `.env.*`, `runtime/`, certificates and local artifacts; only blank `.env.example` templates are versioned. Database files/real business data are not in Git or images. Preserve/back up your existing database; never replace live data with a demonstration file. Check:

```powershell
git ls-files "*.db" ".env" "*/.env"
git status
```

The first command should return no files. Source verification (no database needed in a fresh clone):

```powershell
.\.venv\Scripts\python.exe deployment\verify_preservation.py --source-only
```

Module tests run in separate processes to avoid `app.py` import-name collisions; existing-data tests require the received compatible database. See `deployment/run_checks.py` and the deployment documentation.

## 6. Step 1 — Super Admin only

See [migration, bootstrap and Windows instructions](documentation/super-admin-step1.md) and [exact existing-file edit ledger](PROGRESS.md). `/super-admin` manages users, roles, user audit and one registration flag; no financial queries, company/tenancy modules or new dependencies. Public registration defaults **OFF**; the original login remains unchanged. The first Super Admin is created interactively with `python -m flask --app accounting-software/app.py create-super-admin` after selecting the existing migrated database and runtime environment. No default Super Admin password exists. Lockout/unlock and mandatory-password-change controls are unsupported and deliberately omitted.

## 7. Step 2 — registration and company setup only

**Current login interfaces:** regular user/legacy admin: `/login`; Super Admin: `/super-admin/login`; user signup: `/register` when enabled. Super Admin signs in only through its dedicated portal and lands at `/super-admin`; users/admins land at `/dashboard`. See [separate login Windows guide](documentation/separate-login-guide.md). This interface release needs no additional database migration; the earlier Step 2 migration is still required if missing. The historical Step 1 unchanged-login note above describes that release, not this new interface update.

Public `/register` is available only when the existing Super Admin setting is ON (still OFF by default). New accounts are standard users. `/companies/new` creates one generated external SQLite file with only company settings/schema history, and `/companies/<id>` is owner-only. Super Admin `/super-admin/companies` sees registry metadata and schema-only health, not company settings/data. Existing invoices/clients stay in the original platform database. No company financial modules, subscription or email verification is included.

Follow [Step 2 exact Windows rollout and limitations](documentation/step02-companies.md), [accepted decisions](docs/DECISIONS.md) and [the complete Step 2 edit ledger](docs/PROGRESS.md). Set `COMPANY_DATA_DIR` outside source (for Windows, `$env:COMPANY_DATA_DIR = Join-Path $env:LOCALAPPDATA 'EidSaeedMahmoud\company-data'`). In production add this existing private directory to ignored `deployment/.env`; it is a second storage mount inside the same accounting service, not another server/domain. Fresh explicit demos use the current schema; existing files require explicit Step1 then Step2 migrations.
