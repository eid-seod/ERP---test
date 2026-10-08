# Login interface outcomes

- [x] Dedicated native Arabic RTL Super Admin login at /super-admin/login, Super Admin role only, successful fixed redirect to system administration dashboard /super-admin. No public Super Admin registration.
- [x] Separate native regular-user login at /login, successful fixed redirect to /dashboard. Preserve existing admin-account login/access in that portal. No Super Admin acceptance through this login.
- [x] User registration at /register, standard-role only and existing OFF-by-default flag retained, clear login/register navigation. No password reset, credential defaults or email verification invented.
- [x] Same hashing/sessions/audit/throttle and native CSS; form CSRF, safe fixed redirects, existing company/data/financial modules and DB structure untouched; no secrets/DB versioned.
- [x] Protected Super Admin unauthenticated/revoked/logout paths return to its dedicated login; company/user paths return to user login. Same-domain reverse proxy handles new path through existing super-admin prefix.
- [x] Tests validate all new UI/roles/forms/CSRF/redirects/flag controls and existing regressions; preserve scope evidence and provide tested Windows URLs/update instructions plus opened GitHub commit.

Verified:9portfolio/122accounting/31deployment tests passed; actual native HTTP tested both portals and signup. Received DB hash unchanged. Independent review session/logout fixes passed; financial JS differs ONLY in logout function. No new schema/data/dependency/server/domain. Git delivery is confirmed separately in release report after push and opening the exact commit.
