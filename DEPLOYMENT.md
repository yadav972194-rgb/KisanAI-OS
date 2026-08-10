# KisanAI OS — Production Deployment Guide

Deploying the FastAPI backend on a public HTTPS server. The API contract is
unchanged from local development; only configuration and the server process
differ.

---

## 1. Required environment variables

| Variable | Purpose | Example / notes |
|---|---|---|
| `APP_MODE` | `development` \| `production` | `production` |
| `DEBUG` | Enables API docs + dev reload behavior | `false` in production |
| `SECRET_KEY` | JWT signing key — **must be strong, ≥32 chars** | generate: `python -c "import secrets; print(secrets.token_hex(32))"`. Startup **fails** in production if weak/missing |
| `DATABASE_URL` | SQLAlchemy database URL | PostgreSQL: `postgresql+psycopg://user:pass@host:5432/kisanai`; SQLite: `sqlite:////data/kisanai.db` |
| `HOST` | Bind address | `0.0.0.0` (behind reverse proxy) |
| `PORT` | Listen port | `8000` |
| `CORS_ALLOW_ORIGINS` | Comma-separated allowed browser origins | `https://app.example.com,https://admin.example.com`. Empty = CORS off (native app needs no CORS). Do **not** set `*` with credentials |
| `UPLOAD_DIR` | Persistent media/upload directory | `media/uploads` (must be a mounted volume) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Bootstrapped admin (idempotent on startup) | leave empty if using the API to register users |
| `DISEASE_MODEL_PATH` / `PREDICTION_MODEL_PATH` / `RECOMMENDATION_*` | Optional AI models | leave empty for the safe `MODEL_NOT_CONFIGURED` state |

Optional: `JWT_EXPIRE_MINUTES`, `LOG_LEVEL`, `TIME_ZONE`, `DEFAULT_LANGUAGE`,
`WEATHER_LOCATION`, `WEATHER_COUNTRY_CODE`, `WEATHER_CACHE_TTL_SECONDS`,
`MAX_UPLOAD_SIZE_MB`.

> **Never commit `.env`.** Provide these via the hosting platform's secret
> store or the environment. A single leaked `SECRET_KEY` compromises all JWTs.

## 2. Production startup command

Linux (recommended) — Gunicorn with Uvicorn workers:

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

Or plain Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

`python main.py` also honors `HOST`/`PORT` and never reloads when
`DEBUG=false`. **Never run with `--reload` in production.**

Run migrations before first start:

```bash
alembic upgrade head
```

## 3. HTTPS requirement

Terminate TLS at the edge. The app itself serves HTTP on an internal port:

- **Managed platforms** (Render, Fly.io, Railway, Vercel-friendly PAAS): the
  platform issues HTTPS automatically for the public URL.
- **VPS/self-managed:** put **Caddy** (auto-HTTPS) or **Nginx** in front:

```nginx
server {
    listen 443 ssl;
    server_name api.your-domain.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The mobile app must be built with
`--dart-define=API_BASE_URL=https://api.your-domain.com`.

## 4. Database requirement

**Recommendation: use PostgreSQL before public launch.**

- SQLite works today but is single-writer; concurrent users will hit
  `database is locked`. It also needs a persistent file volume on any
  ephemeral container host.
- PostgreSQL provides concurrency, backups and managed hosting.
- The app already reads `DATABASE_URL`; point it at PostgreSQL
  (`postgresql+psycopg://...`) and run `alembic upgrade head` against the
  new database. **The current SQLite data can be migrated separately** — no
  automatic migration is performed by this project. Keep a backup of
  `kisanai.db` until the switch is verified.

### Data migration from SQLite to PostgreSQL (manual, offline)

1. Back up SQLite: copy `kisanai.db`.
2. Create the PostgreSQL database/user.
3. Point `DATABASE_URL` at PostgreSQL and run `alembic upgrade head`.
4. Copy data with a tool such as `pgloader` (`pgloader sqlite.db postgresql://...`)
   or export/import tables, then verify counts and run `alembic check`.

## 5. Persistent media requirement

Uploaded images are stored under `UPLOAD_DIR` (default `media/uploads`) on the
**local filesystem**. Container hosts erase local disk on redeploy/restart:

- Mount a persistent volume at `media/` (see `docker-compose.yml`), or
- Use an object store (S3/R2/GCS) before public launch — requires a small
  storage-layer change (out of scope for this milestone, documented as a
  follow-up).

Back up `media/` alongside the database.

## 6. Health check

```bash
curl https://api.your-domain.com/health
# 200: {"status":"ok","service":"KisanAI OS","version":"3.4.0"}
# 503: database unreachable (response contains no connection details)
```

`GET /` remains the public home/welcome endpoint. The health endpoint never
exposes `DATABASE_URL`, `SECRET_KEY`, hostnames or error internals.

## 7. CORS

The Android app performs no browser preflight and needs **no** CORS config.
Only set `CORS_ALLOW_ORIGINS` when a web frontend is served from a different
origin than the API.

## 8. Exact deployment steps (single-host example)

1. Create the hosting project/VM and a PostgreSQL database.
2. Copy the repo (or a build artifact) to the server; run `pip install -r requirements.txt`.
3. Set all required environment variables in the platform's secret store.
4. Run `alembic upgrade head`.
5. Start Gunicorn/Uvicorn (command above) behind the HTTPS proxy.
6. Verify `curl https://<host>/health`.
7. Rebuild the Flutter app with `--dart-define=API_BASE_URL=https://<host>`.
8. Run migrations on future schema changes: `alembic upgrade head` then restart workers.

### Docker (optional)

```bash
cp .env.example .env          # fill in real secrets
docker compose up -d --build  # PostgreSQL + backend + volumes
curl http://localhost:8000/health
```

or the standalone image per the `Dockerfile` header comments.
