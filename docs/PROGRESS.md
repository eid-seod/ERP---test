# Step 2 — user registration and company setup

Existing Step 1 ledger is `../PROGRESS.md`; actual migration guide is `../documentation/super-admin-step1.md`. No names were assumed or those files renamed.

Baseline main `b8964abe18094a48c96016d74753f382371a1f00`: portfolio 9, accounting 38, deployment 27 all passed before changes. Annotated `baseline-before-step-02` pushed at that commit. Raw baseline/final/push outputs are delivered in the verification report.

## Outcomes

- [x] Existing /register when enabled: native name/email/password form and standard user only; OFF remains 404/default; case-insensitive uniqueness/password policy; audited signup; per-IP/per-email login/signup throttle; no email verification.
- [x] Explicit safe platform migration adds companies(id/name/type/form/currency/fiscal start/tax ID/status/owner/relative DB name/schema version/date), owner memberships and max_companies_per_user default1. Platform file/users/settings/audit/current financial data not split or moved; no auto-upgrade.
- [x] Logged-in user-only native wizard supports exactly industrial/contracting/trading, sole_proprietorship/joint_stock, currencies EGP/USD/EUR/SAR/AED in one place, fixed Egypt/VAT context, fiscal month1–12 and optional tax ID. Clear validation/success/failure; redirect to workspace.
- [x] Single provisioning entry point: temporary generated file, versioned two-table schema, settings/version, final move, atomic active registry/membership+audit. Handled failure at every step removes partial files and rolls back or marks registry; safe failure audit; limits enforced under write lock.
- [x] COMPANY_DATA_DIR defaults outside Git; only generated relative UUID filenames; traversal/symlink protection. Only member-checked opener accesses company settings. Workspace reads its own settings only, denied access audited; guessing ids, other users, admin/super-admin, revoked users or suspended company cannot access.
- [x] Native Super Admin user table adds has-company and registration date; metadata-only companies search/type/status/pagination/owner link/health/schema/date list and detail. Suspend/reactivate audited; health only reads schema_meta; no company settings/financial reads. Existing Step1 guards remain.
- [x] Tests: flag ON/OFF, all role/route guards, uniqueness, limits/concurrency, enumerations, distinct minimal DBs/isolation, all provisioning faults/cleanup, traversal, user/company suspension, metadata-only admin access, migration copy/idempotence, all old regressions.
- [x] Documentation: exact edit reasons, limitations, external data path, Windows explicit migration/run/setup, how demo Super Admin enables signup, accepted DECISIONS, next step listed but NOT implemented. Existing root folders/branding/native styles unchanged; no heavy dependencies/.db/.env/secrets/business records committed.

## Existing-file edit ledger

Recorded after implementation from actual Git diff; new files preferred.

## Limitations and release status

No email verification/email sending, financial company tables, billing/reporting or later steps. Live received database remains untouched; fixtures outside Git. Production cutover is not performed. In-app limiter is process-local and reset on restart, not a distributed protection service. Deployment continues one existing server/domain; company files are private storage, not separate hosting.

## Implementation notes and limitations

Public registration creates the standard existing `user` role. Owner membership and separate settings files are created only by the wizard service. Existing invoices/clients remain in the original platform database. No company-specific financial module or mail/verification exists.

Migration is explicit on existing databases, including old demos and empty users tables. App startup skips inherited financial migration/backfill code for existing platform files and rejects missing original admin rather than seeding. Truly fresh explicit demo/test initialization retains original setup behavior. Default signup remains OFF. The first-only Super Admin CLI stays unchanged; use that existing identity to enable signup through native settings.

The Windows-compatible local launcher now imports the in-app throttle at module load while the accounting path is available. A real HTTP check caught the initial lazy-import failure; it was fixed and a permanent isolated-interpreter launcher regression was added. New-area pages extend the real dashboard/login templates and existing CSS, not a new design system.

`COMPANY_DATA_DIR` defaults to `~/.local/share/eid-saeed-mahmoud/companies`; Windows users may set LocalAppData using the exact commands in `documentation/step02-companies.md`. Keep platform and company files outside Git and use owner-only NTFS ACLs/POSIX permissions. Company filenames are generated UUID names stored only relatively; no submitted filename is accepted. Production adds one private storage bind mount to the same accounting service—no new server/domain.

All normal company opening requires active standard user/session/owner membership and active company. Super Admin does not open settings/workspaces, even with a membership. Health's exception is read-only schema_meta only. User soft deletion/deactivation and company suspension deny access immediately on the next request. Legacy admin hard-delete remains for ordinary non-company users; newly linked owners are protected against orphaning and require existing soft-delete controls.

The limiter is bounded, in-process and independent by transport-IP/normalized-email; no dependency added. It resets on restart/eviction and is not distributed. The proxy's transport address may group visitors; trusted production edge limits are recommended, not forged forwarded headers.

Handled provisioning exceptions roll back registry and remove owned temp/final files; failure/denial audits never include credentials/paths/raw exceptions. A hard crash/power loss between final placement and registry commit can leave an orphan file, not an active partial company. Filesystem/DB cannot provide a distributed atomic transaction; after such a crash, stop writers and reconcile private files against registry with backup protection. Storage failures may prevent audit/cleanup; no impossible guarantee is made. No automated destructive cleanup is added.

The next step may design company accounting setup but has NOT been started; no journals/account packs/company invoices/reports/subscriptions.

## Actual existing-file edits and reasons

New files own the companies package, versioned company schema/migration, throttle, native signup/wizard/workspace/company-admin pages, tests and setup docs. Existing edits below are integration only; no invoice/client model/route, existing app.css/app.js, portfolio/shared assets or dependency manifest was changed.

| Existing file | Required reason |
| --- | --- |
| `.gitignore` | Ignore provisioning temporary files and optional internal company storage directories. |
| `README.md` | Add the explicit Step2 migration next to demo startup and link setup/decisions/ledger. |
| `PROGRESS.md` | Preserve Step1 history and point to the requested new Step2 tracker. |
| `accounting-software/app.py` | Import/register new metadata/blueprints, validate existing schema before startup, initialize only truly fresh schemas; no legacy financial backfill or admin seeding on existing files. |
| `accounting-software/routes/auth.py` | Existing flag-gated /register GET/form plus compatibility JSON, standard-only signup/audit/input checks; basic login/signup throttle; protect newly linked company owner from legacy hard-delete orphaning. Login form/API/destination/roles otherwise remain. |
| `accounting-software/super_admin/__init__.py` | Apply existing revoked-session rejection to company routes and record denied workspace audit without opening any company file. |
| `accounting-software/super_admin/models.py` | Add nullable integer_value to the existing settings row model; preserve existing Boolean registration setting. |
| `accounting-software/super_admin/service.py` | Extend audit action allowlist with registration/company lifecycle/denial/limit events; existing guards/mutations unchanged. |
| `accounting-software/super_admin/views.py` | Add has-company metadata and numeric maximum to existing users/settings responses, using platform queries only. |
| `accounting-software/templates/dashboard.html` | Add standard-user-only native company menu link; all original financial components/scripts remain. |
| `accounting-software/templates/login.html` | Inert reusable blocks for native signup page; defaults preserve original login form/script/branding; conditional registration link and success feedback only. |
| `accounting-software/templates/super_admin/base.html` | Add native Companies navigation item. |
| `accounting-software/templates/super_admin/users.html` | Add has-company and registration-date columns without redesign. |
| `accounting-software/templates/super_admin/settings.html` | Add separate audited numeric company-limit form with existing native CSRF/styles. |
| `deployment/.env.example` | Declare private external COMPANY_DATA_DIR without secrets. |
| `deployment/accounting-schema.json` | Add only company/membership/numeric-setting expected metadata; original financial definitions preserved. |
| `deployment/accounting_entrypoint.py` | Explicit Step2 diagnostics and numeric-setting validation; no automatic file creation/migration. |
| `deployment/compose.yml` | One additional private storage bind and version label inside the existing accounting service; original platform mount/server/domain unchanged. |
| `deployment/routing.conf` | Add only companies prefix to existing accounting proxy; no URI rewrite. |
| `deployment/run_local.py` | Add only companies prefix to the existing same-origin dispatcher. |
| `deployment/tests/test_deployment.py` | Migrate only disposable copies through Step2, retain all previous assertions and verify old-demo needs explicit Step2. |
| `deployment/tests/test_local.py` | Add company paths to the existing nonrewriting dispatch assertions. |
| `deployment/verify_preservation.py` | Layer the authorized Step2 hashes over historical/Step1 evidence instead of erasing prior manifests. |
| `documentation/plan.md` | Append accepted Step2 architecture without rewriting earlier plan history. |

The actual count/list is verified against Git before commit. No existing file was renamed/moved/deleted. All new test fixtures/database outputs remain outside Git; no actual business records or secrets are versioned.

### Additional existing regression edit

`accounting-software/tests/test_app.py`: one legacy test previously expected startup to auto-add/backfill invoice timestamps, which directly conflicts with Step2's no-automatic-migration requirement. All original invoice counts/IDs/totals/timestamp/idempotence assertions are retained. The test now first asserts read-only startup refusal, then explicitly invokes the unchanged inherited migration helper **only on its disposable fixture**. No business/migration implementation is rewritten. New `companies/platform_guard.py` validates original financial schema/backfill readiness without writes at startup.

` .dockerignore ` (root file): add `**/*.db.tmp`, `company-data`, and `company_data` to exclude provisioning remnants/internal storage from image build contexts. Existing .db/.env/SQLite exclusions remain; no image includes records.

## Final validation before push

Baseline: portfolio9/accounting38/deployment27 passed, annotated baseline tag pushed. Final: portfolio9/accounting97/deployment31 passed (real full-suite output is delivered in the external verification report). Received platform hash matches the original baseline; integrity ok; no nested Git repositories. Native same-origin HTTP signup→login→wizard→workspace→Super Admin metadata→suspension guards passed on disposable fixtures. Compose/Nginx syntax passed without production deployment. All26 existing-file edits are documented; no existing renames/deletions. New owner-only storage opening, malformed schema/limits, collision cleanup and safe-error cases passed. Original financial implementation/UI/assets/dependencies are unchanged. Push/release tag remain pending until verified by their actual outputs and opened GitHub commit link.

## Step 3 — company chart of accounts

**Done:** the composed, bilingual company chart of accounts. One chart per company = shared base pack + exactly one activity pack (by company type) + exactly one legal-form layer (by legal form) — never six separate charts, never a stored per-company copy. Account names are Arabic (primary) + English. Catalog/composition is the new `companies/chart_config.py`; the owner-only read is `GET /companies/<id>/chart-of-accounts` plus a native section on the existing workspace page. The chart is composed on demand from the company's own stored `type`/`legal_form`, so no new company table and no schema-version bump: existing `schema_meta`/`company_settings` behavior is unchanged. Super Admin/admin/other/anonymous access is denied; only the active owner reads their own chart. New tests: `companies/tests` → `tests/test_chart_of_accounts.py`.

**Existing files edited (reason):**

| Existing file | Reason |
| --- | --- |
| `accounting-software/companies/storage.py` | Add `read_company_chart` (member-checked) that composes the chart from stored settings. |
| `accounting-software/companies/views.py` | Add the owner-only chart JSON route and pass the composed chart to the workspace page. |
| `accounting-software/templates/companies/workspace.html` | Add the native bilingual chart section (existing shell/CSS only). |
| `deployment/run_checks.py` | Run preservation `--source-only` when the untracked received DB is absent (fresh clone); unchanged when present. |
| `docs/DECISIONS.md` | Record the Step 3 chart/account decisions. |

**New files:** `companies/chart_config.py`, `tests/test_chart_of_accounts.py`, `deployment/tests/conftest.py`, `documentation/step03-chart-of-accounts.md`.

**Checks:** `python deployment/run_checks.py` → portfolio **9 passed**, accounting **132 passed**, deployment **31 passed**; preservation `ok`. No `.db`/`.env`/secrets committed.

**Next part (NOT started):** journal entries / company invoices / reports.
