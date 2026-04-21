# SWARABHARAT Deployment Guide

This guide covers production deployment for the current codebase, including:

- Backend API deployment
- Frontend static deployment
- Runtime endpoint configuration
- Validation and monitoring

## 1. Pre-Deployment Checklist

- Python 3.11+ available in runtime
- Environment variables configured (`.env.example` as baseline)
- CORS allowed for frontend domain(s)
- Writable storage path for reports if using file mode
- Optional: external database configured if using DB mode

## 2. Environment Variables

Minimum recommended variables:

```env
PORT=5000
FLASK_DEBUG=False

OPENAI_API_KEY=
HUGGINGFACE_API_KEY=
AI_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini

REPORTS_FILE=BACKEND/data/reports.json
AUTO_BUILD_INDEX=1

RATE_LIMIT=60
RATE_WINDOW=60
MAX_DAILY_REQUESTS=1000
MAX_REQUESTS_PER_MINUTE=60
```

Optional DB/department/auth related variables:

```env
USE_DATABASE=true
DATABASE_URL=postgresql://...
JWT_SECRET=change-this-in-production
```

## 3. Backend Deployment Options

### Option A: Docker (recommended)

Use the included `Dockerfile`:

```bash
docker build -t swarabharat:latest .
docker run -p 5000:5000 --env-file .env swarabharat:latest
```

Container entrypoint uses:

```bash
gunicorn BACKEND.wsgi:application -w 2 -b 0.0.0.0:5000
```

### Option B: Procfile-based platforms (Render/Heroku-like)

The repo includes:

```text
web: gunicorn BACKEND.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

Deploy with build command:

```bash
pip install -r BACKEND/requirements.txt
```

Start command:

```bash
gunicorn BACKEND.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

### Option C: Vercel serverless API (advanced)

Serverless handler exists at `api/index.py`, but static frontend paths and rewrites should be validated for your hosting layout before production.

Use this option only if you intentionally run Flask via Vercel serverless constraints.

## 4. Frontend Deployment

Frontend is static and located in `FRONTEND/`.

Deploy this directory to any static host:

- Netlify
- Vercel static hosting
- S3 + CloudFront
- Nginx static root

Important pages:

- Citizen app: `/index1.html`
- Admin app: `/admin/admin.html`
- Runtime submit config page: `/runtime-config.html`

## 5. Runtime Endpoint Wiring

Citizen and admin apps support runtime endpoint switching in browser storage.

### Citizen submit endpoint (`SWARA_API_SUBMIT`)

Set via:

- `runtime-config.html`, or
- `Quick Endpoint` button on citizen page

Fallback order:

1. custom endpoint (`SWARA_API_SUBMIT`)
2. `https://backend-swarabharat.onrender.com/submit`
3. `<frontend-origin>/submit`
4. `http://localhost:5000/submit`

### Admin API base (`SWARA_ADMIN_API_BASE`)

Set via `API Endpoint` button in admin header.

Fallback order:

1. custom base (`SWARA_ADMIN_API_BASE`)
2. `https://backend-swarabharat.onrender.com`
3. `<frontend-origin>`
4. `http://localhost:5000`

## 6. Service Worker and Offline Mode

`FRONTEND/sw.js` enables:

- asset caching
- queued report sync (`sync-reports`)
- offline fallback page

Requirements:

- Serve frontend over `http://` or `https://` (not `file://`)
- Ensure `sw.js` is available at expected path

## 7. Department Station Flow (Admin)

Admin now includes a dedicated `Stations` tab with queues for:

- Government
- Hospital
- Fire
- Police

Cases are auto-routed by issue + keyword + urgency logic in frontend admin controller.

## 8. Health and Smoke Tests

After deployment, verify:

### Backend

```bash
curl https://<backend-domain>/health
curl https://<backend-domain>/dashboard
curl https://<backend-domain>/reports
```

### Frontend

1. Open citizen app and submit a test issue.
2. Confirm report appears in admin reports table.
3. Confirm station routing appears in `Stations` tab.
4. Change report status and verify persistence.
5. Test offline mode by disconnecting network and submitting report.

## 9. Monitoring Recommendations

- Poll `/health` for uptime checks
- Use `/metrics` and `/stats` for lightweight observability
- Track queue size and report ingestion rate
- Alert on repeated `/submit` failures

## 10. Common Issues and Fixes

### Issue: Admin cannot fetch data

- Check CORS on backend
- Set `SWARA_ADMIN_API_BASE` to correct domain
- Verify `/reports` returns JSON

### Issue: Citizen submits fail in production

- Verify `/submit` endpoint is reachable from browser
- Set `SWARA_API_SUBMIT` explicitly
- Check rate limiting thresholds

### Issue: Offline queue not syncing

- Confirm service worker is registered
- Confirm browser supports background sync
- Check `IndexedDB` object store `pending-reports`

### Issue: Map markers not visible

- Ensure reports include valid coordinates
- Confirm Leaflet assets are loading

## 11. Production Hardening

- Set strong `JWT_SECRET`
- Move from JSON file storage to managed DB
- Configure TLS-only endpoints
- Add WAF/rate limiting at edge
- Rotate AI provider keys regularly

## 12. Suggested Deployment Topology

- Backend API: Render/Railway/Fly/Cloud Run (container)
- Frontend static: Netlify/Vercel/S3
- Storage: PostgreSQL for reports (optional but recommended)
- Observability: uptime ping + logs + metrics dashboard
