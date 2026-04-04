#!/usr/bin/env bash
# Local development setup without Docker (works behind institutional firewalls)
set -e

echo "=== ZoneGuard Phase 2 — Local Dev Setup ==="

# 1. Start PostgreSQL + Redis via Docker (only infra, not the app)
echo "[1/4] Starting database and Redis..."
docker compose up db redis -d

echo "Waiting for PostgreSQL to be ready..."
until docker compose exec db pg_isready -U zoneguard 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL ready."

# 2. Python backend (runs natively, not in Docker)
echo "[2/4] Setting up Python backend..."
cd backend

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Created virtualenv."
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo "Dependencies installed."

# 3. Seed database
echo "[3/4] Seeding database..."
python db/seed.py

# 4. Start backend
echo "[4/4] Starting FastAPI backend on :8000"
echo "---"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "In a separate terminal, run: cd frontend && npm run dev"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
