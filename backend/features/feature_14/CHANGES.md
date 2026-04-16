# Feature 14 — ZoneGuard Pulse — CHANGES.md

## What was built

**ZoneGuard Pulse** is a real-time rider risk intelligence feed.

### New files (Feature 14 scope only)

| Path | Purpose |
|---|---|
| `backend/features/feature_14/__init__.py` | Package marker |
| `backend/features/feature_14/pulse_service.py` | All business logic (QuadSignal meter, 72h chart, coverage, activity, WhatsApp brief, notification trigger) |
| `backend/features/feature_14/pulse_router.py` | FastAPI router — all endpoints under `/api/v1/pulse` |
| `frontend/src/features/Feature14/PulseDashboard.tsx` | Self-contained React dashboard component |
| `.env.feature-14.example` | All env vars (FEATURE14_ prefix) |
| `requirements.feature-14.txt` | Feature-14-specific pip requirements (none net-new) |

### Existing files touched

**None.** Feature 14 is fully self-contained. No existing files were
modified.

---

## INTEGRATION — manual steps required by the integrating developer

The following changes must be applied **by the developer integrating
features** once all parallel feature branches land. This feature's author
intentionally did not touch shared files.

### 1. backend/main.py — add router

Add two lines to `backend/main.py` alongside the existing router includes:

```python
# Feature 14 — ZoneGuard Pulse
from features.feature_14.pulse_router import router as pulse_router
app.include_router(pulse_router)
```

The import path assumes the backend is run from the `backend/` directory
(i.e. `python -m uvicorn main:app`), which matches the existing project
convention.

### 2. frontend/src/App.tsx — add route

Add to the import block:

```typescript
import PulseDashboard from './features/Feature14/PulseDashboard'
```

Add a route inside `<Routes>`:

```tsx
<Route path="/pulse/:zoneId" element={<PulseDashboardRoute />} />
```

Where `PulseDashboardRoute` reads the zone param:

```tsx
import { useParams } from 'react-router-dom'

function PulseDashboardRoute() {
  const { zoneId } = useParams<{ zoneId: string }>()
  return <PulseDashboard zoneId={zoneId ?? 'hsr'} />
}
```

Alternatively, embed `<PulseDashboard zoneId="hsr" />` directly inside
an existing page component (e.g. `RiderDashboard.tsx`) — no new route needed.

---

## API endpoints

All mounted at `/api/v1/pulse` once the router is integrated.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pulse/{zone_id}` | Full Pulse snapshot (all data in one call) |
| `GET` | `/api/v1/pulse/{zone_id}/quad-signals` | QuadSignal meter only |
| `GET` | `/api/v1/pulse/{zone_id}/chart-72h` | 72-hour disruption probability buckets |
| `GET` | `/api/v1/pulse/{zone_id}/coverage` | Policy coverage status |
| `GET` | `/api/v1/pulse/{zone_id}/activity` | Anonymised zone activity |
| `POST` | `/api/v1/pulse/whatsapp-brief` | Generate WhatsApp brief text |
| `POST` | `/api/v1/pulse/{zone_id}/notify-check` | Trigger threshold push notifications |

---

## Design decisions

### QuadSignal meter
- Reads `signal_readings` table (populated by existing `/api/v1/signals/poll/{zone_id}`)
- Expresses each signal as a **percentage of its trigger threshold** using
  the same `THRESHOLDS` dict from `ml/signal_fusion.py`
- S2 and S3 invert the scale (lower value = higher risk)
- Alert fires at ≥75% (`FEATURE14_ALERT_THRESHOLD_PCT`)

### 72-hour disruption chart
- Uses `counterfactual_inactivity()` from `ml/zone_twin.py` (ZoneTwin v1) — no new ML
- Derives projected rainfall from `ZONE_BASELINES` (same dict) using a
  deterministic sine-wave modulation seeded by zone + hour offset
- Outputs 12 × 6-hour buckets = 72 hours

### Coverage status
- Reads `policies` + `riders` tables (no schema changes)
- Reports active policy count, coverage %, and expiry within 7 days

### Zone activity signal (anonymised)
- Reads `zones.active_riders` (existing column)
- Applies noise floor rounding (`FEATURE14_ZONE_ACTIVITY_NOISE_FLOOR=3`) to
  prevent individual rider identification

### WhatsApp brief
- Pure text generation, no external service call
- Stays under `FEATURE14_WHATSAPP_MAX_CHARS` (default 800)

### Push notifications
- Reuses `create_notification()` from `models/notification.py`
- Uses existing `NotificationType.SIGNAL_ALERT` enum — no schema change
- Only creates notifications for riders with **active policies** in the zone

### Imports
- Only imports from `ml/`, `models/`, `db/`, and `services/` — no cross-feature imports
- Does not import from any other `feature_NN` directory

---

## Environment variables

All prefixed `FEATURE14_`. See `.env.feature-14.example` for full reference.

| Variable | Default | Description |
|---|---|---|
| `FEATURE14_ALERT_THRESHOLD_PCT` | `75.0` | % of threshold that triggers alerts |
| `FEATURE14_ZONE_ACTIVITY_NOISE_FLOOR` | `3` | Anonymisation rounding unit |
| `FEATURE14_72H_BUCKETS` | `12` | Number of 6-hour chart buckets |
| `FEATURE14_WHATSAPP_MAX_CHARS` | `800` | WhatsApp brief character cap |
| `VITE_FEATURE14_POLL_INTERVAL_MS` | `30000` | Frontend auto-refresh interval (ms) |
