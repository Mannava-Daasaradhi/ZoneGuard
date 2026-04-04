# ZoneGuard

## About the Project

### 💡 Inspiration

India's gig economy is projected to reach **2.35 crore platform workers by 2030** (NITI Aayog, 2022). Amazon Flex last-mile delivery riders earn ₹600–₹800/day under normal conditions — but when a flash flood hits, when AQI spikes to hazardous levels, or when a sudden curfew is announced, their income drops to **zero, instantly**.

We asked ourselves: *What if insurance could be as fast as the disruption itself?*

Traditional insurance fails gig workers completely:
- **Motor insurance** doesn't cover income loss
- **PMJJBY/PMSBY** only covers death/disability
- **Claims take 7–30 days** — riders need money *today*

ZoneGuard was born from a simple insight: **if we can detect disruptions in real-time, we can pay out in real-time**. No claim forms. No waiting. No proof required.

> *"A flash flood doesn't wait for a claims adjuster. Neither should a delivery rider's rent."*

---

### 📚 What We Learned

1. **Parametric insurance is the future for gig workers** — traditional indemnity models are too slow and documentation-heavy for people living week-to-week.

2. **Multi-signal fusion prevents fraud structurally** — requiring 4 independent signals (weather, mobility, orders, crowd) to converge makes single-signal gaming mathematically impossible.

3. **Weekly pricing matches gig worker psychology** — monthly premiums feel abstract; ₹39–₹225/week feels concrete and manageable.

4. **Exclusions must be explicit** — Phase 1 feedback taught us that clear exclusions (war, pandemic, terrorism, vehicle defects) build trust, not suspicion.

5. **AI/ML is only as good as its explainability** — our FraudShield model uses transparent heuristics so every flagged claim can be justified to regulators.

---

### 🛠️ How We Built It

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    ZONEGUARD PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│  FRONTEND (React 19 + TypeScript + Tailwind)                │
│  ├── Landing Page with persona-driven onboarding            │
│  ├── Rider Dashboard (coverage, signals, payouts)           │
│  ├── Admin Dashboard (KPIs, claims queue, analytics)        │
│  └── Interactive Leaflet zone map with risk choropleth      │
├─────────────────────────────────────────────────────────────┤
│  BACKEND (FastAPI + PostgreSQL + SQLAlchemy 2.0)            │
│  ├── 9 API routers (riders, zones, policies, claims, etc.)  │
│  ├── QuadSignal Fusion Engine (4-signal convergence)        │
│  ├── FraudShield (8-feature anomaly detection)              │
│  ├── ZoneTwin (counterfactual simulation)                   │
│  └── Background Signal Poller (15-min APScheduler)          │
├─────────────────────────────────────────────────────────────┤
│  INTEGRATIONS                                                │
│  ├── OpenWeatherMap API (real weather data)                 │
│  ├── Google Gemini 1.5 Flash (AI audit reports)             │
│  ├── Simulated: OSRM mobility, WhatsApp check-ins, UPI      │
│  └── NDMA flood alerts (pre-validated S1 override)          │
└─────────────────────────────────────────────────────────────┘
```

#### QuadSignal Fusion Engine

The core innovation — 4 independent signals must converge within a 2-hour window:

| Signal | Source | Threshold |
|--------|--------|-----------|
| **S1 Environmental** | Weather API | Rainfall >65mm/hr, AQI >300, Temp >43°C |
| **S2 Mobility** | OSRM/Maps | Zone mobility drops >75% from baseline |
| **S3 Economic** | Platform API | Order volume drops >70% from baseline |
| **S4 Crowd** | WhatsApp | ≥40% of zone riders report inactivity |

**Confidence levels:**
- 4 signals = **HIGH** → Auto-payout within 2 hours
- 3 signals = **MEDIUM** → Gemini AI audit + 1hr recheck
- 2 signals = **LOW** → Human review required
- 1 signal = **NOISE** → No action

#### Payout Formula

$$\text{Payout} = 0.55 \times \frac{\text{Weekly Earnings Baseline}}{7}$$

We retain 45% to mitigate moral hazard — riders still have incentive to work when conditions are marginal. For Ravi (₹18,200/week baseline): ₹2,600/day × 55% = **₹1,430 per disrupted day**.

#### Premium Calculation

ZoneRisk Scorer computes a **0–100 risk score** from 5 weighted factors, then maps to an actuarially-derived tier:

| Factor | Weight | Description |
|--------|--------|-------------|
| Historical disruption frequency | **35%** | Last 24 months of disruption events per zone |
| IMD seasonal forecast | **25%** | Upcoming week's predicted monsoon/heat risk |
| Rider tenure band | **15%** | New riders (<4 weeks) carry higher risk |
| Zone-type classification | **15%** | Warehouse-adjacent vs. flood-prone residential |
| Prior week's claim history | **10%** | Zone-level loss ratio adjustment |

**Premium tiers (actuarially derived):**

| Risk Score | Tier | Weekly Premium | Max Payout |
|-----------|------|---------------|------------|
| 0–29 | Low | ₹39 | ₹1,430 |
| 30–54 | Medium | ₹89 | ₹4,290 |
| 55–74 | High | ₹139 | ₹7,150 |
| 75–100 | Flood-Prone | ₹225 | ₹11,440 |

---

### 🚧 Challenges We Faced

#### 1. **Signal Synchronization**
Ensuring 4 independent data sources align within the same 2-hour window required careful timestamp handling and a rolling window algorithm. We solved this with UTC normalization and a sliding window buffer.

#### 2. **Fraud Surface Minimization**
GPS spoofing and coordinated inactivity fraud were real concerns. Our multi-signal approach means a rider can't just turn off their phone — they'd need to simultaneously:
- Control weather data
- Shut down city traffic
- Crash platform order systems
- Coordinate 40% of zone riders

This is structurally infeasible.

#### 3. **Basis Risk**
Parametric insurance has basis risk — what if signals fire but a specific rider wasn't actually affected? We addressed this with:
- Zone-level granularity (10 Bengaluru zones, not city-wide)
- ZoneTwin counterfactual modeling
- 24-hour social trigger waiting periods

#### 4. **Regulatory Compliance**
IRDAI's parametric sandbox requires clear trigger definitions and exclusions. We embedded 10 standard exclusions directly into the platform with enforcement at 3 phases: policy creation, claim trigger, and claim review.

#### 5. **Mobile-First UX**
Gig workers primarily use mobile. We rebuilt all 5 pages for 375px viewport, added touch-friendly map controls, and implemented a WhatsApp-style notification system that feels native.

---

### 🎯 Key Features

- ✅ **90-second onboarding** — Rider ID → Zone selection → Coverage active
- ✅ **Zero-touch claims** — No forms, no uploads, no waiting
- ✅ **Real-time signal dashboard** — See exactly why coverage triggered
- ✅ **Transparent exclusions** — 10 standard exclusions, clearly displayed
- ✅ **AI-powered audits** — Gemini generates human-readable claim reports
- ✅ **Disruption simulator** — Demo flash floods, AQI events, strikes in real-time
- ✅ **Admin analytics** — Claims trends, loss ratios, zone risk heatmaps

---

## Built With

React 19, TypeScript, Tailwind CSS, Vite, Leaflet, Recharts, FastAPI, Python, PostgreSQL, SQLAlchemy, APScheduler, OpenWeatherMap API, Google Gemini API, Docker

---

## Try It Out

🔗 **Live Demo:** [https://zenith-tribe.github.io/ZoneGuard/](https://zenith-tribe.github.io/ZoneGuard/)

---

## GitHub Repository

💻 **Source Code:** [https://github.com/zenith-tribe/ZoneGuard](https://github.com/zenith-tribe/ZoneGuard)

---

## Demo Video

🎬 **2-Minute Demo:** [YouTube Link - TO BE ADDED]

---

## Team

**Zenith Tribe** — Guidewire DEVTrails 2026

---

*Built with ❤️ for India's gig workers*
