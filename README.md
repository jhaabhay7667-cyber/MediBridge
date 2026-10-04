# MediBridge — Emergency Coordination Platform

Phase 1 (backend core). Coordination and information only; it does not contact government
emergency services, dispatch ambulances, or provide medical advice. Seeded facilities are
**demo data**, not verified live availability.

## Run (Windows PowerShell)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then set SECRET_KEY (and SMTP_* for real email)
python -m app.seed_facilities
uvicorn app.main:app --reload
pytest
```
Swagger docs: http://127.0.0.1:8000/docs

## Render
Build: `pip install -r requirements.txt` — Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
Set SECRET_KEY, DATABASE_URL (PostgreSQL), CORS_ORIGINS (your Netlify URL), FRONTEND_URL, SMTP_*.

## Status
Done: auth, emergencies + timeline, contacts, facilities (haversine search), SMTP notify with
per-contact status/retry, ambulance/hospital coordination, tests.
Frontend (Phase 2): login/register, dashboard with press-and-hold SOS, emergency page (contacts, email alerts,
ambulance/hospital status, nearby facilities, timeline, print/PDF), contacts, facilities search, history filters,
light/dark theme, English/Hindi/Bengali nav and safety text.
Not yet: profile page, AI layer, rate limiting, full string translation, PWA, in-app notification center page.

## Frontend
```powershell
cd frontend
python -m http.server 5500
```
Open http://localhost:5500/login.html. For production set `API_BASE` in `frontend/config.js` to your Render URL,
deploy `frontend/` to Netlify, and add the Netlify URL to `CORS_ORIGINS` on Render.
