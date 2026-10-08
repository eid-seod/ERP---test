# Implementation references

Tajawal: official font family at https://fonts.google.com/specimen/Tajawal; its Arabic/Latin family supplies weights 400, 500 and 700 used by the portfolio. Font files are self-hosted in `shared-assets/fonts`; the SIL Open Font License is included as `Tajawal-OFL.txt`. No external font request is required in the deployed website.

Nginx proxy contract: https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass. A `proxy_pass` with no URI suffix preserves upstream request paths. `deployment/routing.conf` uses that behavior so the existing accounting frontend's absolute `/login`, `/dashboard`, `/invoices`, `/clients`, and `/static` URLs do not need application edits.

Odoo's official accounting description: https://www.odoo.com/app/accounting. Zoho Books: https://www.zoho.com/us/books/. Portfolio service copy mentions implementation support, not an official partnership, certification, or feature implemented in the custom accounting app.

Local validation tools were extracted from official Ubuntu Noble packages: Nginx 1.24.0 and Docker Compose 2.40.3. Production Compose uses the `nginx:1.28-alpine` image. A successful native configuration check and Compose model check are not an executed container build or a production-host acceptance test.
