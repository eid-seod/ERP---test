# Unified Eid Saeed Mahmoud project

## Approved direction

The latest request supersedes the separate-portfolio architecture. Consolidate into the **existing `eid-seod/ERP---test` Git repository**, retaining accounting and portfolio history, with top-level `portfolio/`, `accounting-software/`, `shared-assets/`, `documentation/`, and `deployment/`. No new Git repository, brand, custom domain, database, hosting project, or production environment is created. Target deployment is the owner's future private server, not a new Manus publication.

Move existing accounting files into `accounting-software/` without editing their contents. Preserve the current baseline `551f23d49e75cb296cbf61e7162fc04fe7c730bc`, including its current branding/language. The existing SQLite file is relocated by a filesystem move, not recreated; record and verify its hash. Record hashes for every tracked accounting file. Existing authentication, modules, permissions, route paths, workflows, and calculations remain unchanged. No historical branding rollback or security patch is included. Infrastructure cookie flags, TLS, and private service binding belong to deployment, not changes to application source or role logic.

The public portfolio is Arabic and RTL, with English accounting/ERP terminology embedded in bidirectional-safe spans. Specific preservation of the accounting app takes precedence over translating its protected screens. Actual screenshots remain unaltered; Arabic captions describe them. Public identity: **عيد سعيد محمود / Eid Saeed Mahmoud**, **مدير حسابات | متخصص مالي / Accounts Manager | Finance Professional**. No invented employment dates, credentials, metrics, email, portrait, or country code. Supplied public phone: `01000062838`.

Navigation: الرئيسية، نبذة عني، الخدمات المهنية، المشاريع، البرنامج المحاسبي، المدونة، تواصل معي. Accounting Software is one professional project/solution; clicking its access button opens existing `/login` on the same origin. No iframe, copy, rewrite, product rename, or separate brand. Add meaningful Arabic blog content with actual article pages, no invented publication history.

## Implementation and serving

- `portfolio/`: Flask SSR, Arabic content, vanilla JS, responsive CSS, `/`, `/blog/<slug>`, `/health`, `/manus-routes.json`, `/robots.txt`, `/sitemap.xml`, `/portfolio-assets/*`.
- `accounting-software/`: original Flask/SQLAlchemy/SQLite app unchanged, same original routes `/login`, `/dashboard`, `/invoices`, `/clients`, `/users`, `/invoice/*`, `/me`, `/register`, `/logout`, `/static/*`.
- `shared-assets/`: self-hosted Tajawal Arabic fonts and their license; portfolio-only blue personal monogram. No accounting assets moved out of the protected app.
- `documentation/`: setup, architecture, known production risks, accounting preservation manifest, final verification and plan/TODO.
- `deployment/`: two production WSGI service definitions and one Nginx reverse proxy; Docker Compose installs all from this one repository on one private server. Only Nginx exposes ports 80/443; one supplied domain and existing TLS certificate. Existing SQLite file is a bind-mounted persistent file/directory, never an anonymous fresh database volume. No portfolio database.

The proxy sends `/` and blog/contact/portfolio assets to portfolio; original accounting path prefixes and `/static/*` go to accounting. Upstream paths are not prefixed or rewritten. Portfolio's asset prefix is distinct. A local same-origin preview uses the same routing definitions, private backends, and the existing preview origin; it is not a new production environment.

Keep accounting dependencies unmodified. Deployment separately adds pinned Gunicorn. Startup preflight verifies an existing database and required settings before loading accounting; no new database is silently created. Document known inherited risks rather than patch frozen accounting. Native Nginx will be tested locally; Compose/container execution is reported honestly if Docker is unavailable.

Deliver a portable ZIP, one Git history bundle, and clear private-server instructions. GitHub push to the existing repository is attempted only after access is restored; do not create a replacement repository. The old portfolio project is no longer maintained as a separate source; do not erase historical repositories or independently deployed hosting without a dedicated approved removal.

## Design

**Movement:** executive modernism and Arabic editorial typography.
**Principles:** personal authority, clear service taxonomy, generous white space, evidence through actual project screenshots.
**Colors:** corporate cobalt blue `#1459C7`, deep navy `#102B50`, white `#FFFFFF`, pale blue `#EFF5FF`; blue conveys financial clarity and confidence. Remove green from portfolio-only assets/styles.
**Layout:** right-aligned Arabic hero with large personal identity; offset professional-focus sidebar; horizontal numbered service groups; asymmetric project/software narrative and screenshot composition. Blog uses clean editorial teasers.
**Signatures:** a thin cobalt rule, numbered section markers, a typographic ع س monogram.
**Interactions:** predictable anchors, visible software access, accessible dialog and mobile menu, local inquiry preparation with truthful Arabic feedback.
**Animation:** subtle 180ms hover/focus transitions, no scroll-jacking or hidden content, reduced-motion support.
**Typography:** locally served Tajawal 400/500/700, system sans fallback, Latin terminology in isolated LTR spans. Arabic headings 56–76px desktop / 38–50px mobile; body 16–18px.
**Brand essence:** عيد سعيد محمود يجمع الخبرة المالية مع الأنظمة العملية لخدمة الأعمال. Professional, precise, approachable.
**Voice:** direct Arabic: «وضوح مالي. قرارات أفضل.» and «خبرتي المالية في خدمة أعمالك.»
**Wordmark:** personal Arabic name with secondary proper-name Latin line, not a software-company identity.

## Windows local-run clarification (8 October 2026)

Retain this same repository and its existing Nginx production topology. Add only `deployment/run_local.py`: two original Flask app objects are loaded under distinct module names, and a WSGI selector dispatches unchanged accounting path prefixes or public portfolio paths on loopback port 8000. Do not copy, patch, rename or rewrite accounting routes. The README gives exact PowerShell/VS Code commands using `.venv\\Scripts\\python.exe`, not the unavailable `py` launcher. Existing compatible database is selected explicitly with `--database` and preflighted read-only; no silent replacement/migration. A fresh clone contains no database, so an explicit optional `--demo` can create/reuse a separate ignored disposable local demo with a terminal-entered password; never executed implicitly and never committed. This is local development only, not another production environment. `portfolio-assets` is an existing URL namespace for tracked `portfolio/static`, not a missing physical root directory. Git command transcripts and an independently opened GitHub commit URL resolve remote-publication claims with actual evidence.

## Step 1 only — Super Admin (8 October 2026)

Baseline is remote `main` commit `6520a315bae99bf9b6a49a08341ff5be70c73828`, tagged `baseline-before-super-admin` after the complete baseline suite passed. Add only a `super_admin` role and `/super-admin` area: user administration, user-only audit, one registration setting, dashboard counts and interactive bootstrap CLI. No companies, tenancy, new databases per company, financial modules, auth provider replacement or dependency changes.

Existing `User.is_active` and 8-character password policy are reused. Add nullable deletion/last-login timestamps and an integer session epoch; reject inactive/deleted/revoked sessions on their next accounting request. Add separate user audit and settings tables, never invoice audit or financial data queries. SQLite write transactions use `BEGIN IMMEDIATE` so last-active-super-admin guards and audit writes are atomic. Legacy admin endpoints cannot create/change/delete a super_admin. Preserve normal admin/user behavior except the explicitly requested default-OFF registration flag and session revocation.

The accounting app has no base layout file, but its existing `dashboard.html` is the actual native shell. Introduce inert Jinja blocks in that file and extend it for new Super Admin pages; preserve its default markup, CSS and original scripts. New pages override the content and scripts, reuse current CSS/components and add only scoped RTL spacing styles; they never load financial dashboard JavaScript. Portfolio/login/invoice pages and existing accounting CSS/JS remain unchanged. Navigation link is server-rendered only for active super_admin identities.

Add an idempotent migration touching only users/new user-audit/settings structures, plus explicit standalone migration instructions. Tests and visual checks use disposable databases outside Git; do not migrate or create a Super Admin in the live received database. Production/local preflight remains fail-closed until the explicit migration is run. Preserve the historical accounting manifest, adding a transparent authorized source-change overlay for Step 1. All existing edits and reasons are recorded in root PROGRESS.md.

Existing lockout/rate limiting and mandatory-password-change flows do not exist. Do not invent them: locked count is explicitly unavailable/zero; no unlock or forced-change controls. Bootstrap CLI takes interactive/environment credentials, applies the existing policy/hashing, supports first creation only and never prints passwords. Generated temporary passwords appear in a single no-store response, never audit, cookies or documentation.
