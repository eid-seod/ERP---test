# Step 1 — Super Admin only

## Baseline

- Repository: `https://github.com/eid-seod/ERP---test`, `main`.
- Tested HEAD: `6520a315bae99bf9b6a49a08341ff5be70c73828`.
- Full baseline: portfolio **9 passed**, accounting **6 passed**, deployment **20 passed**; syntax and preservation checks passed. Exact console output is in the task's verification report.
- Annotated tag `baseline-before-super-admin` pushed; tag object `2c6d2e4fb82c320e40e642245ec742d637626e95`, peeled target the tested HEAD. No backup/data/secret committed.

## Outcomes

- [x] Native `/super-admin` dashboard: total/active/inactive/locked support status, users by role, logins in last seven days, ten latest user audit events, app version and environment.
- [x] Only active `super_admin` can enter; admin/user receive 403, unauthenticated users redirect to existing login. Link visible only to super_admin. Existing layout, colors, fonts, components/navigation, login and portfolio remain native and unchanged apart from that conditional link.
- [x] User management: name/email search, role/status filters, safe sorting/pagination, create with supplied/generated temporary password shown once, edit profile/role, activate/deactivate with immediate next-request session rejection, reset password, soft delete/restore, detail and user audit history. Emails unique and original minimum-eight-character password policy preserved.
- [x] Server safety and tests: no self-deactivation/deletion/demotion; no removal/demotion/deactivation of last active super_admin; no admin/user creation/change of super_admin; all new writes require CSRF and POST/PUT/DELETE. Transactional guards and audit commit together.
- [x] Separate user-only audit table and browse filters actor/action/date/pagination. Actor/action/target, changed before/after fields, UTC time/IP recorded; passwords/hashes never recorded. Super Admin requests and scripts do not query financial tables/APIs.
- [x] Minimal settings: `public_registration_enabled` OFF by default; existing `/register` respects it; only super_admin toggles and action audited.
- [x] First-only bootstrap CLI prompts for email/password or reads env; no default/hardcoded/printed secret. Additive idempotent migration, documentation, real full-suite output and independent read-only review.

## Deliberately unsupported existing capabilities

There is no lockout/rate-limit mechanism or mandatory-password-change flow. Step 1 does not invent either: locked count explicitly shows unavailable/zero; unlock and must-change controls are omitted with explanations. All existing credential examples in the unchanged login/template/tests predate this step; no new real credentials were added.

## Existing-file edit ledger

All **15** actual existing-file edits are listed below. New files contain the new blueprint, services, models, migrations, templates, scoped CSS/JS, tests, documentation and authorized preservation overlay. No existing file/directory was renamed, moved or deleted.

| Existing file | Reason for unavoidable edit |
| --- | --- |
| `README.md` | Link explicit migration/first bootstrap/Windows instructions; correct outdated whole-app source-identical claims for the authorized extension. |
| `accounting-software/app.py` | Register new blueprint/session hooks/CLI and validate an existing users schema BEFORE original initialization; fresh demo/test initialization retained. |
| `accounting-software/models/user.py` | Add only deleted/login timestamps and session epoch, plus normalized email unique index; reuse active flag, existing fields and password methods. |
| `accounting-software/routes/auth.py` | Default-OFF registration; login date/audit/epoch; reject invalid sessions; protect Super Admin from legacy writes; hide soft-deleted users; consistent email case lookup; preserve audit refs on retained normal-user legacy delete. |
| `accounting-software/templates/dashboard.html` | Make the actual native shell reusable via inert Jinja blocks; retain original defaults/components/scripts and add a role-only Super Admin link. New templates replace only their own content/scripts. |
| `accounting-software/tests/test_app.py` | Explicit registration opt-in in the existing registration-dependent fixture; retain every original regression assertion. |
| `deployment/accounting-schema.json` | Add only required new users/audit/settings metadata so preflight rejects unmigrated existing files. Financial definitions unchanged. |
| `deployment/compose.yml` | Supply correct production environment label and optional release version; topology/volumes/domains unchanged. |
| `deployment/routing.conf` | Add only `super-admin` to the existing accounting path rule; no existing path stripping or changes. |
| `deployment/run_checks.py` | Prevent app-import initialization against live data by using an external disposable bootstrap DB; keep isolated processes and check new script syntax. |
| `deployment/run_local.py` | Add only the new accounting prefix to the same-origin Windows/local dispatcher. |
| `deployment/tests/test_deployment.py` | Exercise existing preflight assertions on migrated temporary copies outside Git, not an unmigrated live file. |
| `deployment/tests/test_local.py` | Add dispatch coverage for the four new Super Admin prefixes. |
| `deployment/verify_preservation.py` | Preserve the historical manifest; transparently allow only five recorded authorized accounting-source changes instead of claiming the entire app is untouched. Original DB byte check retained. |
| `documentation/plan.md` | Append the user-authorized Step 1 scope and native-template reuse decisions; retain earlier plan history. |

## Independent review and resolution

Read-only review found two edge cases, both fixed and tested:

1. **Implicit migration on direct imports:** removed automatic upgrading. Existing users schemas missing new columns/tables/index are rejected before original `init_db`; standalone migration is explicit. Fresh app demo/test initialization retains its original creation behavior. Regression proves an unmigrated existing database's bytes/tables are unchanged after rejected startup.
2. **Mixed-case email duplicates:** a unique `lower(email)` index is added without rewriting rows, and original login/duplicate checks use consistent lower-case matching. Existing case-insensitive duplicates cause migration refusal/rollback, not automatic merging. Tests cover duplicate creation/edit/public registration, mixed-case login and rejection without database changes.

## Validation and deployment status

- Complete final supported suite: portfolio **9 passed**, accounting **38 passed** (all original six plus new tests), deployment **24 passed**. No skip/xfail. Exact output available in the verification report.
- Concurrency test proves cross-deactivations leave an active Super Admin; session tests cover deactivation/delete/reset/role changes on the next request.
- Request SQL instrumentation confirms no invoice/client/invoice-item/invoice-audit query from Super Admin pages/actions. No financial dashboard script is loaded there.
- Actual local one-origin HTTP integration: portfolio `/` 200, original `/login` 200, unauthenticated Super Admin 302 to login, authenticated new pages 200, default registration 404, CSRF-authorized create 201. All fixture data is disposable/outside Git.
- Original financial routes/models, database helper, existing CSS/JS, login/invoice templates, requirements, portfolio and shared assets compare unchanged against the pushed baseline tag. The received database's original hash still matches; integrity `ok`.
- Python compile, both script syntax checks, whitespace, Compose model and Nginx syntax pass. One unsupported root-level bare pytest discovery initially failed due pre-existing module import collisions; the supported isolated runner passes. The first optional validator path was stale; after discovering the installed binary the actual checks pass.
- No new heavy dependency, company/tenant/chart-of-accounts/per-company database, new repo/domain or production provisioning. All five existing module folders retained.
- **The received/live database is NOT migrated in place, and no real Super Admin identity/password is created.** Owner must follow `documentation/super-admin-step1.md` for explicit backup/migration/interactive creation against their existing database. Docker image execution/private-server cutover are not performed here. New Super Admin management soft-deletes only; the original active-normal-user admin hard-delete endpoint is deliberately retained to preserve its existing behavior and cannot delete a Super Admin or already soft-deleted user.

## Follow-up — existing demo startup refusal (2026-10-08)

`--demo` intentionally reuses ignored `runtime/local-demo.db`; it never resets a file or silently upgrades an older schema. An older pre-Super-Admin demo can lack the new user metadata/tables/index and must use the existing explicit migration.

| Existing file edited in this follow-up | Reason |
| --- | --- |
| `deployment/accounting_entrypoint.py` | List missing tables, give a quoted explicit upgrade command only for recognized Super Admin schema gaps, and detect a missing normalized email index before import. Preserve read-only fail-closed behavior. |
| `deployment/tests/test_deployment.py` | Reproduce the old-demo refusal on an external temporary copy; verify rejected startup writes nothing, explicit migration passes while all original row values/password hashes remain intact, unrelated missing financial tables are not mislabelled, and missing index is detected. |
| `README.md` | Put the Windows migration/restart commands beside `--demo`, with backup/no-reset guidance. |
| `PROGRESS.md` | Record this follow-up transparently; Step 1 historical evidence above remains unchanged. |

Full isolated rerun: portfolio **9 passed**, accounting **38 passed**, deployment **27 passed**. No accounting application, migration implementation, UI, portfolio, financial logic or live database was changed in this follow-up. The received database still matches its original byte hash and integrity is `ok`. Only disposable test files were migrated outside Git. No real data, secrets or database files are committed.

## Step 2 — company setup follow-up

The user-authorized Step2 outcome/edit ledger is now `docs/PROGRESS.md`; accepted decisions are `docs/DECISIONS.md`, and explicit Windows/storage/migration guidance is `documentation/step02-companies.md`. This does not rename/remove Step1 history. The platform database stays in place; separate company settings files are created only on authorized company creation. Existing financial workflows and portfolio remain untouched. Refer to the Step2 tracker for final tests/review/release status rather than interpreting the older Step1 totals as current.
