# Step 3 — company chart of accounts

This release adds **only** the composed, bilingual company chart of accounts. It does not add journals, entries, company invoices, reports, subscriptions or mail. Existing platform users/login/roles/settings/audit and invoices/clients remain in the original main SQLite file, untouched.

## What was added

- One **composed** chart per company: a shared **base pack** + exactly one **activity pack** (by company type) + exactly one **legal-form layer** (by legal form). It is never six separate charts and never a stored per-company copy.
- Bilingual account names: **Arabic is the primary (displayed) name**, English is the secondary name.
- The catalog and composition live in `accounting-software/companies/chart_config.py` (pure, dependency-free, unit-tested).
- Owner-only read: `GET /companies/<id>/chart-of-accounts` (JSON) and a native section on the existing company workspace page `/companies/<id>`.

## Why no new table and no schema bump

The chart is composed **on demand** from the company's own stored `type` and `legal_form` in `company_settings`. This keeps the accepted "composed, never six separate charts" decision literal, adds no per-company chart copy, and leaves the existing company `schema_meta`/`company_settings` schema and its exact two-table set unchanged (so no company-file migration and no schema-version bump are needed). Existing provisioning, health check and workspace behavior are unchanged.

## Access boundaries

- Only the active standard `user` who is the active `owner` of an active company can read its chart (same member-checked opener as the workspace).
- Super Admin, legacy admin, other users and unauthenticated visitors are denied (403/302). Super Admin still cannot read any company settings or financial data; only its read-only `schema_meta` health exception remains.
- All company routes stay CSRF-protected and `no-store`.

## Verification

`python deployment/run_checks.py` runs portfolio, accounting-software and deployment in isolated interpreters. New Step 3 tests are in `accounting-software/tests/test_chart_of_accounts.py` (composition from the three layers, bilingual Arabic-primary names, activity/legal layers differ, invalid type/legal form rejected, owner-only read, other-user/Super Admin/anonymous denial).

## Next step (not started)

Journals/entries, company invoices and reports remain unimplemented. No financial calculation, VAT rate or report is added here.
