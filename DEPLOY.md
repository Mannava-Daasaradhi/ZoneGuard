# Deployment Guide

## Option A: Local Dev (Behind Firewall) — Recommended for Demo

**Problem**: Docker containers can't reach PyPI behind institutional DNS.
**Solution**: Run infra (DB/Redis) in Docker, backend natively.

```bash
# One-time: fix Docker DNS (if you ever need full docker-compose)
./fix-docker-dns.sh

# For daily dev: run infra in Docker, backend natively
./dev-setup.sh
# In another terminal:
cd frontend && npm run dev
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

---

## Option B: Railway (Production Backend) + GitHub Pages (Frontend)

### Step 1: Deploy backend to Railway

1. Create account at [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo → select `ZoneGuard`
3. Set **Root Directory** to `backend`
4. Railway auto-detects the `Dockerfile`
5. Add environment variables in Railway dashboard:
   ```
   DATABASE_URL=<Railway PostgreSQL URL>  ← add PostgreSQL service first
   REDIS_URL=<Railway Redis URL>          ← add Redis service
   GEMINI_API_KEY=<your key>
   OPENWEATHERMAP_API_KEY=<your key>
   CORS_ORIGINS=https://pranaav2409.github.io,http://localhost:5173
   APP_ENV=production
   DEBUG=false
   ```
6. Add PostgreSQL service → copy the connection string → set as `DATABASE_URL`
7. Deploy → get your Railway URL (e.g. `https://zoneguard-backend-prod.up.railway.app`)
8. Run seed: Railway → backend service → Shell → `python db/seed.py`

### Step 2: Wire frontend to Railway backend

In GitHub repo settings → Secrets and variables → Actions:
```
VITE_API_URL = https://zoneguard-backend-prod.up.railway.app
```

Push to `main` → GitHub Actions builds frontend with the API URL → deploys to GitHub Pages.

### Step 3: Verify

```bash
# Check backend health
curl https://zoneguard-backend-prod.up.railway.app/health

# Check zones seeded
curl https://zoneguard-backend-prod.up.railway.app/api/v1/zones

# Trigger simulator
curl -X POST https://zoneguard-backend-prod.up.railway.app/api/v1/simulator/trigger \
  -H "Content-Type: application/json" \
  -d '{"zone_id": "hsr", "scenario": "flash_flood"}'
```

---

## Option C: Full Docker Compose (after DNS fix)

```bash
# Fix Docker DNS first (one-time)
./fix-docker-dns.sh

# Then rebuild and run
cd ZoneGuard
docker compose up --build

# Seed in another terminal
docker compose exec backend python db/seed.py
```

---

## Frontend-Only Mode (No Backend)

The frontend gracefully degrades to mock data when the backend is unreachable.
The Phase 1 GitHub Pages site still works standalone.
