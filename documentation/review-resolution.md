# Independent read-only review resolution

The reviewer verified 22 unchanged accounting files, database hash/integrity and absence of nested `.git`; it did not start services or alter either app. Findings were resolved as follows.

| Finding | Resolution / actual verification |
| --- | --- |
| New layout not yet committed at review time | Final delivery requires commit and normal push to original `eid-seod/ERP---test`, then bundle/ZIP from that exact tree. Remote SHA is recorded in the release evidence. |
| Deployment guide/root README missing during concurrent documentation work | Both now exist, covering one repository, existing database directory/ownership, one supplied domain/TLS, Compose commands, security decisions and cutover. |
| Secure session cookie incompatible with direct local HTTP preview | HTTPS public preview uses Secure/SameSite=None and an authenticated same-origin HTTPS check passed. An explicit `--plain-http` option supports local HTTP only; unit test verifies the separate modes. Production remains HTTPS/Secure. |
| Original startup executes migrations/backfills/admin check | Original app is deliberately unchanged. Deployment preflight now checks required schema columns/types and integrity and rejects missing seed admin or known backfill requirements. No bypass/patch is applied to app logic. Stop old writers and back up; do not claim the guard prevents concurrent mutations. Negative read-only tests cover these rejection paths. |
| Default seed password fallback | Deployment requires a strong `ADMIN_PASSWORD` in the already-supported original environment setting, while preflight rejects a missing seed administrator. Existing passwords are not modified; user must rotate existing demo credentials separately before production. |
| Container/production execution not demonstrated | Accurate boundary: native Nginx routed the actual HTTPS preview, public accounting login/read routes passed, Compose model parsed, and module tests passed. No Docker daemon, target-server login, production TLS, DNS or actual production rollout was used. |

Review did not identify an accounting code change. Current UI language and branding remain preserved even though the public portfolio is Arabic/RTL. The prior independent managed portfolio is legacy and must be retired after a verified owner-controlled cutover, not silently deleted during packaging.
