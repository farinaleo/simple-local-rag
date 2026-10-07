# Production deployment checklist (DEBUG=false)

This is the validated profile for running the stack outside development.
With `DEBUG=false`, Django stops serving `/media/` itself, stops rendering
debug error pages, and enforces `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.

## Required environment variables

Copy `.env.example` to `.env` at the repository root, then set:

| Variable | Production value | Why |
|---|---|---|
| `DEBUG` | `false` | Disables Django debug pages and dev media serving |
| `SECRET_KEY` | long random string | Signs sessions and tokens; never keep the dev key |
| `ALLOWED_HOSTS` | your host(s), comma-separated | Django rejects requests with other `Host` headers |
| `CSRF_TRUSTED_ORIGINS` | your origin(s), e.g. `https://rag.example.com` | Login and admin forms are rejected otherwise |
| `CORS_ALLOWED_ORIGINS` | your web origin(s) | Browser API calls from other origins fail otherwise |
| `POSTGRES_PASSWORD` | strong password | Used by compose for the `postgres` service |
| `ADMIN_PASSWORD` | strong password, then change it | Bootstrap admin account created by migration |
| `API_VERSION` | e.g. `4.0.0` | Version reported in the OpenAPI schema |

## What changes with DEBUG=false

- **Media files**: Django no longer serves `MEDIA_URL`; the nginx reverse
  proxy serves them from the shared `/media/` volume (already configured in
  `nginx/reverse-proxy.conf`). Avatars keep working with no extra step.
- **Error pages**: errors return plain 40x/50x responses without stack
  traces or settings dumps.
- **Host validation**: any request whose `Host` header is not in
  `ALLOWED_HOSTS` returns 400.

## Validation steps

After `docker compose up -d --build`:

1. `curl -f http://<host>/api/health/` returns `{"status": "ok"}`
2. Log in from the web UI — the login form must succeed (CSRF origins)
3. Upload an avatar on `Mon compte` — the picture must render (nginx media)
4. Upload a document and ask a question — the answer streams
5. `GET /api/docs/` renders the Swagger UI
6. `GET /<nonexistent>/` returns a plain 404 (no debug page)

## CI coverage

`tests/test_production_profile.py` locks the profile: the API surface
(health, schema, docs) keeps working under `DEBUG=False`, and the media
routes are not registered outside debug mode.
