# Accepted Step 2 decisions

- One canonical repository `eid-seod/ERP---test`, main; one private-server/domain ecosystem. Existing portfolio/branding/native accounting UI unchanged.
- Existing main/platform SQLite remains the users/settings/audit/companies registry database. Existing invoices/clients stay in it untouched.
- Only types: `industrial`, `contracting`, `trading`.
- Only legal forms: `sole_proprietorship`, `joint_stock`.
- Base currencies: `EGP`, `USD`, `EUR`, `SAR`, `AED`, configurable in one companies configuration module.
- Country fixed to Egypt; Egyptian VAT context assumed. No tax engine/VAT rates/calculations implemented at this step.
- Fiscal year start month chosen1–12; optional tax ID.
- Registration uses the same standard existing `user` role with owner membership of their own company. No personalized permission set at signup.
- Public registration stays OFF by default, controlled only by the existing Super Admin setting; no fake email verification.
- Every company gets one generated-name separate SQLite file at creation. Only `schema_meta` and `company_settings` now. Versioned migrations live in a dedicated folder.
- Membership schema supports future multiple users, but only `owner` is implemented now.
- `max_companies_per_user` default1; company provisioning uses one common service for current wizard and future admin creation.
- Company data directory configurable by `COMPANY_DATA_DIR`, outside tracked source by default; platform database is never relocated.
- Super Admin uses platform metadata only. Sole company-file exception is read-only schema_meta health; no settings or financial access.
- Step 3 implements **only** the company chart of accounts. Journals, invoices-per-company, reports, subscriptions and mail remain unimplemented future steps.
- Account names are bilingual: Arabic (primary/displayed) + English (secondary).
- One company chart is **composed**: a base pack (shared) + exactly one activity pack (by company type) + exactly one legal-form layer (by legal form). Never six separate charts and never a stored per-company chart copy.
- The chart is composed on demand from the company's own stored `type`/`legal_form`; no new company table and no company schema-version bump. Existing `schema_meta`/`company_settings` behavior is unchanged.
