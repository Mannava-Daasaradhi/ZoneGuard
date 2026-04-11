# ZoneGuard — Phase 3 Complete

**Guidewire DEVTrails 2026 · Phase 3 Submitted: April 11, 2026**

---

## What We Built in Phase 3

Phase 3 completed the four remaining items from the DEVTrails roadmap, plus produced the final pitch deck and wired everything into the existing Phase 2 full-stack.

---

### 1. FraudShield v2 — Federated Learning (`backend/ml/federated/`)

**The problem:** Phase 2 had a heuristic rule-based fraud scorer. Phase 3 upgrades it to a real ML model trained across multiple cities without centralising raw rider data — required for DPDP Act 2023 compliance.

**What we built:**
- `client.py` — Each city (Bengaluru, Mumbai, Hyderabad, Pune, Chennai) runs a `FederatedFraudClient` that trains a local `IsolationForest` on its own claim data. The client serialises the model into a 51-dimensional weight vector (estimator threshold means + global offset). Raw GPS and activity data never leaves the city.
- `server.py` — `FederatedFraudServer` implements **FedAvg** (McMahan et al., 2017): collects weight vectors from all clients, computes `w_global = Σ (n_k / N) × w_k`, pushes the aggregated weights back. Runs in-process for the demo (identical aggregation math to a production gRPC deployment).
- `__init__.py` — `run_federated_round(n_rounds)` convenience function called by the admin API.

**Admin API endpoints added to `routers/admin.py`:**
- `POST /api/v1/admin/fraudshield/federated-round?n_rounds=3` — triggers a full FL session, returns per-round stats
- `POST /api/v1/admin/fraudshield/ring-detection-demo` — runs temporal clustering on synthetic genuine vs. coordinated attack batches

---

### 2. Temporal Ring Detection (`backend/ml/fraud_shield.py`)

**The problem:** The Phase 2 fraud scorer scored individual claims. It couldn't detect a Telegram-coordinated fraud ring where 500 people all go dark simultaneously.

**What we built** (added to existing `fraud_shield.py`):

- `detect_coordination_ring(zone_id, claim_timestamps, expected_claims_mean)` — analyses a batch of claim timestamps using 4 signals:
  1. **Inter-arrival CV** — genuine Poisson disruptions: CV ≈ 1.0. Telegram "go now" spike: CV ≈ 0.1–0.3
  2. **Temporal spike detector** — flags ≥ 8 claims within any 15-minute window
  3. **Clustering coefficient** — treats 5-minute time buckets as graph nodes; adjacent bucket density reveals coordination
  4. **ZoneTwin Poisson z-score** — compares observed claim count against historical expected count; 20× expected = automatic liquidity protection

- `analyze_zone_event_batch(zone_id, claims, expected_claims_mean)` — convenience wrapper that runs both individual scoring and ring detection in one call

**Verdict tiers:** `genuine` / `suspicious` / `ring_detected` / `insufficient_data`

**Key insight:** A GPS spoofer can fake their own location. They cannot simultaneously fake the Poisson distribution of 40 other independent riders in the same zone.

---

### 3. e-Shram KYC Integration

**The problem:** Phase 2 KYC was just UPI + phone. Budget 2025 mandated e-Shram registration for gig workers. Phase 3 adds full UAN verification.

**What we built:**

- `backend/models/rider.py` — added 4 new columns: `eshram_id` (unique), `eshram_verified`, `eshram_income_verified`, `eshram_verified_at`
- `backend/schemas/rider.py` — added `RiderEShramKYC` (with UAN format validator: `UW-XXXXXXXXXX-X` or 12-digit) and `EShramVerificationResponse`
- `backend/routers/riders.py` — added `POST /api/v1/riders/{rider_id}/eshram-kyc`:
  - Deduplication check: rejects if another rider already holds the same e-Shram ID
  - Income cross-check: compares declared earnings against portal estimate; flags `deviation_minor` (< 40%) or `deviation_major` (> 40%)
  - Simulates e-Shram portal API deterministically from rider ID (reproducible demo)
  - Elevates `kyc_verified = True` on successful verification
- `backend/db/migrations/versions/003_eshram_kyc.py` — Alembic migration with partial unique index on `eshram_id`

**Frontend (`EShramKYCCard.tsx`):** Collapsible card on the Onboarding Step 4 success screen. Shows benefits grid, validates UAN format client-side, handles all three income match outcomes with appropriate messaging.

---

### 4. Forward Premium Lock — Frontend UI

**The problem:** The backend already supported Forward Premium Lock (8% discount for 4-week commitment) since Phase 2. Phase 3 surfaces it in the UI.

**What we verified:** `PolicyPage.tsx` already had a complete Forward Premium Lock card showing:
- Regular weekly premium vs. locked premium (×0.92)
- 4-week total savings calculation
- Actuarial rationale copy

No additional work needed — already shipped in Phase 2.

---

### 5. FraudShieldPanel — Admin Dashboard Component

**What we built (`frontend/src/components/Admin/FraudShieldPanel.tsx`):**

Two-tab panel added to the Admin Dashboard after `<ClaimsQueue />`:

- **Federated Learning tab:** Round selector (1/2/3 rounds), "Run FedAvg" button, results showing participating cities, total training samples, weight norm convergence per round, and the privacy guarantee string
- **Ring Detection Demo tab:** "Run Ring Detection Demo" button triggers the backend demo endpoint; side-by-side display of genuine disruption analysis vs. coordinated ring analysis with CV, clustering coefficient, confidence score, and verdict badges

---

### 6. Pitch Deck PDF

**`ZoneGuard_Phase3_PitchDeck.pdf`** — 10-slide A4 deck built with ReportLab:

| Slide | Content |
|-------|---------|
| 1 | Cover — branding, badges, quote |
| 2 | The Problem — comparison table vs. motor insurance and PMJJBY |
| 3 | Solution Overview — B2B2C flow, 4 pillars, exclusions |
| 4 | Ravi's Week — side-by-side with/without ZoneGuard scenario |
| 5 | QuadSignal Fusion Engine — signal breakdown + confidence matrix |
| 6 | AI/ML Architecture — 4 modules + system architecture |
| 7 | FraudShield v2 — FL architecture + temporal ring detection |
| 8 | Premium Model — 4 tiers + ZoneRisk Scorer factors |
| 9 | Business Case — unit economics + regulatory path |
| 10 | Phase 3 Complete — full deliverable checklist |

---

## Files Changed / Added in Phase 3

| File | Change |
|------|--------|
| `backend/ml/fraud_shield.py` | Added temporal clustering ring detection |
| `backend/ml/federated/__init__.py` | New — FL package init |
| `backend/ml/federated/client.py` | New — FederatedFraudClient (IsolationForest + FedAvg weights) |
| `backend/ml/federated/server.py` | New — FederatedFraudServer (FedAvg aggregation) |
| `backend/models/rider.py` | Added e-Shram fields |
| `backend/schemas/rider.py` | Added RiderEShramKYC + EShramVerificationResponse |
| `backend/routers/riders.py` | Added /eshram-kyc endpoint |
| `backend/routers/admin.py` | Added /fraudshield/federated-round + /ring-detection-demo |
| `backend/db/migrations/versions/003_eshram_kyc.py` | New — Alembic migration |
| `backend/requirements.txt` | Added scipy |
| `frontend/src/services/api.ts` | Added submitEShramKYC, triggerFederatedRound, ringDetectionDemo |
| `frontend/src/types/index.ts` | Added EShramVerificationResponse, FederatedRoundResult, RingDetectionDemoResult, RingAnalysis |
| `frontend/src/pages/Onboarding.tsx` | Added EShramKYCCard to Step 4 success screen |
| `frontend/src/components/Admin/FraudShieldPanel.tsx` | New — FL round trigger + ring detection demo |
| `frontend/src/components/Rider/EShramKYCCard.tsx` | New — e-Shram verification UI |
| `frontend/vite.config.ts` | Fixed base path for Docker (was `/ZoneGuard/` in production, now `/`) |
| `ZoneGuard_Phase3_PitchDeck.pdf` | New — 10-slide submission deck |

---

## Phase 3 Deliverables vs. DEVTrails Checklist

| Deliverable | Status |
|-------------|--------|
| FraudShield v2 — Federated Learning (Flower framework) | ✅ Implemented as in-process FedAvg (identical math, no network infra needed for demo) |
| Temporal clustering analysis for collusion ring detection | ✅ CV + spike + clustering coefficient + ZoneTwin z-score |
| Rider Analytics Dashboard | ✅ Already complete in Phase 2 |
| Insurer Admin Analytics Dashboard | ✅ Already complete in Phase 2 + FraudShieldPanel added |
| Disruption simulation engine | ✅ Already complete in Phase 2 |
| Forward Premium Lock feature | ✅ Backend Phase 2, Frontend UI Phase 2, verified Phase 3 |
| e-Shram KYC integration | ✅ Model + schema + endpoint + migration + frontend card |
| Final pitch deck (PDF) | ✅ 10-slide ReportLab PDF |
| 5-minute demo video | ⬜ Must be recorded by team (8-step judge walkthrough from README) |

---

## Running Phase 3 Features in the Demo

### Federated Learning Round
Admin Dashboard → FraudShield v2 panel → Federated Learning tab → select rounds → Run FedAvg

### Ring Detection Demo  
Admin Dashboard → FraudShield v2 panel → Ring Detection Demo tab → Run Ring Detection Demo

### e-Shram KYC
Onboarding → complete all 3 steps → Step 4 success screen → expand "Link e-Shram ID" card → enter `UW-1234567890-1`

### Full 8-Step Judge Flow
1. http://localhost:5173 — Landing page
2. "Get Covered" → Onboarding (Rider ID → Zone → Earnings)
3. Rider Dashboard — active coverage card
4. Admin Dashboard → Disruption Simulator → HSR Layout → Flash Flood
5. QuadSignal panel: S1+S2+S3+S4 all fire → HIGH confidence
6. Claims Queue — auto-created claim, FraudShield score, exclusion check passed
7. Approve payout — UPI ref ZG-2026-XXXXXXXX generated
8. KPIs update — total payouts ↑, loss ratio ↑, active claims ↓

---

*ZoneGuard · Guidewire DEVTrails 2026 · Team Zenith Tribe*