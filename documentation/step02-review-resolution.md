# Step 2 independent review and corrections

A read-only review inspected authorization, signup, registry migration, file provisioning, native template reuse and private deployment; no received/live database was opened for mutation.

| Finding | Resolution / status |
| --- | --- |
| New throttle imported lazily after Windows launcher removes its temporary module path | Fixed by loading the existing new throttle at auth module initialization. Real one-origin HTTP verification passes; permanent isolated-interpreter launcher regression added. |
| Old startup called inherited legacy migrations/backfills on an existing platform file | App now initializes only truly fresh empty schemas. Existing files pass read-only schema/backfill checks; missing users/seed admin refuse instead of creating/replacing data. Legacy migration regression retains all original financial assertions but explicitly upgrades its disposable fixture. |
| Existing company tables/settings could be malformed despite names existing | New migration hardening validates registry columns/constraints/indexes and numeric limit rather than trusting table presence; existing malformed data must fail without writes. Final malformed-schema/limit/migration-copy tests passed. |
| Malformed schema version / failed connect could escape safe error handling | New company schema runner now normalizes failures and close only initialized connections; malformed-version/connect regressions verify safe unavailable response. |
| Conditional writable-directory path replacement could race company opening/cleanup | Storage hardening uses file identity checks/guarded opening and ownership-aware cleanup. Private directory permissions remain required, especially Windows ACLs. Tests/report describe platform-specific limits instead of claiming universal filesystem security. |
| A filename collision could cause accidental deletion of preexisting data | Final-file ownership tracked; collision cleanup may remove only files owned by this provisioning attempt. Tested with a generated-name collision. |
| Legacy hard-delete could orphan a newly linked owner | Original admin hard-delete rejects only users owning registered companies; ordinary nonowner deletion remains. Existing Super Admin soft-delete retains company metadata and revokes access. |

No changes to original invoice/client implementation/models, accounting CSS/JS, portfolio/shared assets, dependency manifests or real data. No future accounting features, email verification/sending, distributed limiter or production cutover are claimed.

Final review fixes passed the full isolated suite (9 portfolio,97 accounting,31 deployment). POSIX read-only opener pins verified descriptor/inode and rejects symlinks; Windows uses identity checks and requires trusted ACLs. Cleanup compares recorded file identity before removal and never deletes unowned replacement paths. Unexpected unowned objects are left for owner review rather than destructively removed. No universal protection against a privileged local attacker or arbitrary same-service filesystem mutation is claimed.
