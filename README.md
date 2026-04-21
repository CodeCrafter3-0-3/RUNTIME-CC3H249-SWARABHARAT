# SWARABHARAT

AI-powered civic issue reporting platform with real-time citizen intake, analytics, and department-wise operational stations.

## Overview

SwaraBharat helps citizens report local problems and helps response teams act faster.

- Citizens submit issues by text or voice.
- Backend classifies reports into issue, urgency, emotion, and summary.
- Admin panel visualizes trends, maps incidents, and manages case status.
- Cases are routed into department stations: Government, Hospital, Fire, Police.

## What Is Implemented

### Citizen App (`FRONTEND/index1.html`)

- Voice + text input
- Real-time user context:
  - local clock
  - online/offline network state
  - geolocation + live mini map
  - weather snapshot (Open-Meteo)
- Evidence photo upload
- Live case classification preview:
  - issue class
  - urgency
  - routed departments
  - case type
- Offline queue with IndexedDB + service worker sync
- Runtime submit endpoint override

### Admin App (`FRONTEND/admin/admin.html`)

- Dashboard cards and live map
- Emotion and issue charts
- Search/filter/export report table
- Status update workflow (`Submitted`, `Acknowledged`, `In Progress`, `Resolved`)
- Analytics section with trend and alert signals
- AI lab (`/demo_analyze`, model selection, semantic search)
- Department Stations section:
  - Government queue
  - Hospital queue
  - Fire queue
  - Police queue

### Backend (`BACKEND/app.py`)

- Core reporting API: `/submit`, `/reports`, `/dashboard`
- Case status update: `/update_status/<report_id>`
- Analytics APIs: trends, insights, routing, explain priority
- AI APIs: demo analysis, model status, semantic search/index
- Department portal blueprint: `/department/*`
- Health and metrics endpoints

## Project Structure

```text
SWARABHARAT/
|- FRONTEND/
|  |- index.html                 # Landing page
|  |- index1.html                # Citizen reporting app
|  |- js/script.js               # Citizen app logic
|  |- sw.js                      # Offline sync + cache
|  |- runtime-config.html        # Runtime submit endpoint UI
|  |- admin/
|     |- admin.html              # Admin dashboard
|     |- admin.js                # Admin logic
|
|- BACKEND/
|  |- app.py                     # Flask API
|  |- ai_engine.py               # AI/heuristic analysis
|  |- ml_engine.py               # Priority + analytics helpers
|  |- data_handler.py            # File-based report storage
|  |- department_portal.py       # Department auth/stats/report views
|  |- wsgi.py                    # Gunicorn entrypoint
|  |- requirements.txt
|
|- api/index.py                  # Vercel serverless handler
|- Dockerfile
|- Procfile
|- DEPLOYMENT_GUIDE.md
```

## Local Setup

### 1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r BACKEND/requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure environment

```powershell
copy .env.example .env
```

Edit `.env` as needed.

### 4. Start backend

```powershell
python BACKEND/app.py
```

Backend default: `http://localhost:5000`

### 5. Start frontend static server (recommended)

```powershell
cd FRONTEND
python -m http.server 5500
```

Open:

- Citizen app: `http://localhost:5500/index1.html`
- Admin app: `http://localhost:5500/admin/admin.html`

## Runtime Endpoint Configuration

### Citizen app submit endpoint

- Use `FRONTEND/runtime-config.html` or the `Quick Endpoint` button.
- Saved in browser storage key: `SWARA_API_SUBMIT`.

Fallback order used by citizen app:

1. custom endpoint from `SWARA_API_SUBMIT` (if set)
2. `https://backend-swarabharat.onrender.com/submit`
3. `<current-origin>/submit` (non-file protocol only)
4. `http://localhost:5000/submit`

### Admin API base

- Use `API Endpoint` button in admin header.
- Saved in browser storage key: `SWARA_ADMIN_API_BASE`.

Fallback order used by admin app:

1. custom base from `SWARA_ADMIN_API_BASE` (if set)
2. `https://backend-swarabharat.onrender.com`
3. `<current-origin>` (non-file protocol only)
4. `http://localhost:5000`

## Key API Endpoints

### Core

- `POST /submit`
- `GET /reports`
- `GET /dashboard`
- `POST /update_status/<report_id>`

### AI / Demo

- `POST /demo_analyze`
- `GET /demo_models`
- `GET /demo_status`
- `GET /demo_quota`
- `GET /demo_examples`

### Analytics

- `GET /analytics/trends`
- `GET /analytics/insights`
- `POST /analytics/predict`
- `POST /analytics/route`
- `GET /analytics/explain_priority?report_id=...`
- `GET /analytics/priority`

### Semantic Search

- `POST /ai/search_similar`
- `POST /ai/build_index`
- `GET /ai/index_status`

### Ops

- `GET /health`
- `GET /metrics`
- `GET /stats`

## Testing

```powershell
$env:PYTHONPATH="BACKEND"
pytest BACKEND/tests -q
```

## Deployment

See full production instructions in [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Notes

- Frontend routing/classification logic is client-side and designed to be resilient.
- Backend currently persists reports in JSON by default, with optional DB mode.
- This repo includes both demo-friendly and production-friendly components.
