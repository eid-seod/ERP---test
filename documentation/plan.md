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
