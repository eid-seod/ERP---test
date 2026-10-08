# Separate Super Admin and User sign-in

The two portals use the SAME existing SQLite identities, password hashes, sessions, login audit, CSRF policy and shared throttle. No new database, repository, server, domain or role is created. One cookie means one signed-in account per browser session; use a private window or browser profile for simultaneous roles. This is interface and server-side role separation, not a new authentication system.

| Page | URL on your local server | Roles/destination |
| --- | --- | --- |
| User login | http://127.0.0.1:8000/login | Existing user and legacy admin accounts → /dashboard |
| Super Admin login | http://127.0.0.1:8000/super-admin/login | Existing super_admin accounts only → /super-admin |
| User registration | http://127.0.0.1:8000/register | Only standard user creation; available when existing public registration setting is ON |
| Portfolio | http://127.0.0.1:8000/ | Same Arabic public homepage |

User login links to registration if enabled and to the separate Super Admin portal. Administration login has no registration option. Form controls are Arabic RTL/native app.css, credentials empty, no financial app.js. Successful native login works without JavaScript. Wrong role returns the same generic invalid-credentials response and establishes no new authenticated session. Identity/role/status/password checks occur inside the existing SQLite write-transaction pattern before successful audit. Native form POSTs use session CSRF. Existing JSON /login clients retain user and csrf_token fields and now receive a fixed redirect_url; Super Admin API integrations MUST switch to POST /super-admin/login. Both portals reject foreign Origin headers and share the same login throttle buckets. No submitted role/next URL can grant permissions or change destinations.

Anonymous/revoked administration pages redirect to /super-admin/login; user/company pages to /login. Super Admin logout returns to its portal; company pages sharing the native sign-out script still return to user login. Original role permissions, finance routes/calculations, company access guards and user provisioning are unchanged. No default Super Admin password or public Super Admin signup. Use existing credentials; don't send passwords in messages.

## Windows / VS Code

Stop the running server. From the repository root:

```powershell
git pull --ff-only origin main
$env:COMPANY_DATA_DIR = Join-Path $env:LOCALAPPDATA 'EidSaeedMahmoud\company-data'
.\.venv\Scripts\python.exe deployment\run_local.py --demo
```

No NEW migration is needed for this login-interface release. If the existing file STILL lacks the Step2 companies tables, first back up it with all writers stopped, then apply the migration you already received:

```powershell
.\.venv\Scripts\python.exe accounting-software\migrations\companies.py --database ".\runtime\local-demo.db"
```

Do not recreate/delete/replace the database. Step1 must already be applied. For real data continue using your existing --database path instead of --demo.

Public signup remains OFF by default; this release does not change your setting. Login as your existing Super Admin at /super-admin/login, open /super-admin/settings and deliberately switch public registration ON if wanted. Then a regular user can open /register, create an account and sign in at /login. No email verification/delivery is implemented. Company setup still uses /companies/new; no subsequent accounting modules were added.

## Exact existing-file edit scope

| Existing path | Required change |
| --- | --- |
| accounting-software/routes/auth.py | Delegate POST /login to shared user-role service |
| accounting-software/app.py | Register dedicated public portal and prepare login CSRF |
| accounting-software/templates/login.html | Native Arabic user interface; empty credentials; portal links |
| accounting-software/super_admin/views.py | Dedicated anonymous/revoked administration redirect |
| accounting-software/super_admin/__init__.py | Clear stale session without blocking public portal; administration re-login destination |
| accounting-software/static/js/super_admin.js | Use fixed verified-server logout destination |
| accounting-software/static/js/app.js | Logout function ONLY honors verified-server destination when Super Admin visits original dashboard; finance logic unchanged |
| accounting-software/tests/test_super_admin.py | Sign-in helpers/anonymous redirects select correct portal; all legacy permission/audit assertions retained |
| accounting-software/tests/test_companies.py | Same portal-helper/anonymous expectations; original isolation assertions retained |
| deployment/tests/test_company_local_integration.py | Actual isolated Windows-compatible dispatch covers native Super Admin portal |
| deployment/verify_preservation.py | Transparent authorized login overlay; historical and Step1/Step2 records retained |
| portfolio/app.py | Route-manifest entries only; public homepage/design unchanged |
| README.md | Local URL/update guide link |

New files: login_portals.py, templates/super_admin/login.html, tests/test_login_portals.py and scoped planning/setup/preservation notes. No source copy, financial calculations/app.css changes, schema upgrade, records or secrets included.

### Reviewed edge cases

Rejected credential/role attempts clear prior authentication and issue fresh CSRF for native forms; invalid CSRF does not clear a valid account session. Logout selects its fixed destination on the server from the verified current user before clearing the cookie. Both native administration/company and original dashboard scripts honor only /login or /super-admin/login; submitted redirect targets are ignored. This required changing only the logout function in original app.js, not its invoice/client/calculation functions.
