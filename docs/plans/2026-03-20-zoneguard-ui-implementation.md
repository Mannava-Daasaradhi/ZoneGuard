# ZoneGuard UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a polished, static React + TypeScript + Tailwind CSS UI for ZoneGuard with Rider Dashboard, Insurer Admin Dashboard, and Onboarding — deployed to GitHub Pages.

**Architecture:** Single Vite+React app with HashRouter (GH Pages compatible). Two visual themes (warm amber for Rider, dark slate for Admin) controlled by route. All data mocked in `/src/data/mock.ts`. No backend calls.

**Tech Stack:** Vite, React 18, TypeScript, Tailwind CSS v3, Recharts, react-router-dom (HashRouter), gh-pages (deploy)

---

### Task 1: Scaffold Vite + React + TypeScript project

**Files:**
- Create: `frontend/` (project root)
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

**Step 1: Scaffold the project**

```bash
cd /home/pranaav/Work/guidewire/ZoneGuard
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 2: Install dependencies**

```bash
npm install react-router-dom recharts
npm install -D tailwindcss postcss autoprefixer gh-pages
npx tailwindcss init -p
```

**Step 3: Configure Tailwind**

Edit `frontend/tailwind.config.js`:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'sans-serif'] },
      colors: {
        saffron: { DEFAULT: '#D97706', light: '#FEF3C7', dark: '#92400E' },
      },
    },
  },
  plugins: [],
}
```

**Step 4: Set up index.css**

Replace `frontend/src/index.css` with:
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

* { box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; margin: 0; }
```

**Step 5: Configure package.json for GH Pages**

Add to `frontend/package.json`:
```json
{
  "homepage": "https://<your-github-username>.github.io/ZoneGuard",
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  }
}
```
> Replace `<your-github-username>` with actual username.

**Step 6: Configure vite.config.ts for GH Pages base path**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/ZoneGuard/',
})
```

**Step 7: Verify dev server starts**

```bash
npm run dev
```
Expected: Vite dev server at http://localhost:5173, default React page loads.

**Step 8: Commit**

```bash
cd /home/pranaav/Work/guidewire/ZoneGuard
git add frontend/
git commit -m "feat: scaffold Vite+React+TS+Tailwind frontend"
```

---

### Task 2: Mock data layer

**Files:**
- Create: `frontend/src/data/mock.ts`
- Create: `frontend/src/types/index.ts`

**Step 1: Create types**

Create `frontend/src/types/index.ts`:
```ts
export type RiskTier = 'low' | 'medium' | 'high' | 'flood-prone';
export type SignalStatus = 'active' | 'inactive' | 'firing';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'NOISE';
export type DayStatus = 'normal' | 'disrupted' | 'payout';

export interface Zone {
  id: string;
  name: string;
  pinCode: string;
  riskTier: RiskTier;
  riskScore: number;        // 0–100
  weeklyPremium: number;    // ₹29 / 49 / 69 / 99
  maxWeeklyPayout: number;
  activeRiders: number;
  disruptions: number;      // disruption days/year
}

export interface WeekDay {
  day: string;              // 'Mon', 'Tue', etc.
  date: string;             // '2026-03-16'
  status: DayStatus;
  earnings: number;
  payoutAmount?: number;
  disruptionType?: string;
}

export interface Payout {
  id: string;
  date: string;
  amount: number;
  zone: string;
  trigger: string;
  confidence: ConfidenceLevel;
  upiRef: string;
}

export interface Signal {
  id: 'S1' | 'S2' | 'S3' | 'S4';
  name: string;
  description: string;
  status: SignalStatus;
  value: string;
  threshold: string;
  firedAt?: string;
}

export interface ClaimEvent {
  id: string;
  zone: string;
  date: string;
  confidence: ConfidenceLevel;
  signals: number;
  recommendedPayout: number;
  auditSummary: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface KPI {
  label: string;
  value: string;
  delta: string;
  trend: 'up' | 'down' | 'stable';
  sparkline: number[];
}
```

**Step 2: Create mock data**

Create `frontend/src/data/mock.ts`:
```ts
import { Zone, WeekDay, Payout, Signal, ClaimEvent, KPI } from '../types';

export const ZONES: Zone[] = [
  { id: 'hsr', name: 'HSR Layout', pinCode: '560102', riskTier: 'medium', riskScore: 58, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 142, disruptions: 3 },
  { id: 'koramangala', name: 'Koramangala', pinCode: '560034', riskTier: 'medium', riskScore: 54, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 198, disruptions: 3 },
  { id: 'whitefield', name: 'Whitefield', pinCode: '560066', riskTier: 'low', riskScore: 22, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 215, disruptions: 1 },
  { id: 'indiranagar', name: 'Indiranagar', pinCode: '560038', riskTier: 'medium', riskScore: 61, weeklyPremium: 49, maxWeeklyPayout: 2200, activeRiders: 167, disruptions: 3 },
  { id: 'electronic-city', name: 'Electronic City', pinCode: '560100', riskTier: 'low', riskScore: 31, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 289, disruptions: 1 },
  { id: 'bellandur', name: 'Bellandur', pinCode: '560103', riskTier: 'flood-prone', riskScore: 87, weeklyPremium: 99, maxWeeklyPayout: 3500, activeRiders: 94, disruptions: 8 },
  { id: 'btm-layout', name: 'BTM Layout', pinCode: '560076', riskTier: 'high', riskScore: 72, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 131, disruptions: 5 },
  { id: 'jp-nagar', name: 'JP Nagar', pinCode: '560078', riskTier: 'high', riskScore: 68, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 112, disruptions: 5 },
  { id: 'yelahanka', name: 'Yelahanka', pinCode: '560064', riskTier: 'low', riskScore: 19, weeklyPremium: 29, maxWeeklyPayout: 1800, activeRiders: 178, disruptions: 1 },
  { id: 'hebbal', name: 'Hebbal', pinCode: '560024', riskTier: 'high', riskScore: 74, weeklyPremium: 69, maxWeeklyPayout: 2800, activeRiders: 103, disruptions: 5 },
];

export const RAVI_WEEK: WeekDay[] = [
  { day: 'Mon', date: '2026-03-16', status: 'normal', earnings: 2600 },
  { day: 'Tue', date: '2026-03-17', status: 'normal', earnings: 2800 },
  { day: 'Wed', date: '2026-03-18', status: 'payout', earnings: 0, payoutAmount: 1950, disruptionType: 'Flash flood — all 4 signals fired' },
  { day: 'Thu', date: '2026-03-19', status: 'payout', earnings: 0, payoutAmount: 1950, disruptionType: 'Flood continues — signals sustained' },
  { day: 'Fri', date: '2026-03-20', status: 'normal', earnings: 2400 },
  { day: 'Sat', date: '2026-03-21', status: 'normal', earnings: 2200 },
  { day: 'Sun', date: '2026-03-22', status: 'normal', earnings: 0 },
];

export const PAYOUTS: Payout[] = [
  { id: 'P001', date: '2026-03-19', amount: 1950, zone: 'HSR Layout', trigger: 'Flash Flood (ENV-01)', confidence: 'HIGH', upiRef: 'ZG-2026-3819' },
  { id: 'P002', date: '2026-03-18', amount: 1950, zone: 'HSR Layout', trigger: 'Flash Flood (ENV-01)', confidence: 'HIGH', upiRef: 'ZG-2026-3818' },
  { id: 'P003', date: '2026-02-11', amount: 1950, zone: 'HSR Layout', trigger: 'Transport Strike (SOC-02)', confidence: 'HIGH', upiRef: 'ZG-2026-2111' },
  { id: 'P004', date: '2026-01-08', amount: 1650, zone: 'HSR Layout', trigger: 'Severe AQI (ENV-02)', confidence: 'MEDIUM', upiRef: 'ZG-2026-0801' },
];

export const QUAD_SIGNALS: Signal[] = [
  { id: 'S1', name: 'Environmental', description: 'OpenWeatherMap + NDMA', status: 'inactive', value: 'Rainfall: 12mm/hr', threshold: '>65mm/hr', },
  { id: 'S2', name: 'Mobility', description: 'OSRM Zone Index', status: 'inactive', value: 'Mobility: 94% of baseline', threshold: '<25% of baseline' },
  { id: 'S3', name: 'Economic', description: 'Order Volume Proxy', status: 'inactive', value: 'Orders: 98% of baseline', threshold: '<30% of baseline' },
  { id: 'S4', name: 'Crowd', description: 'WhatsApp Check-ins', status: 'inactive', value: 'Check-ins: 3% inactivity', threshold: '≥40% inactivity' },
];

export const CLAIMS_QUEUE: ClaimEvent[] = [
  {
    id: 'CE-001', zone: 'BTM Layout', date: '2026-03-19', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 2100, status: 'pending',
    auditSummary: 'Signals S1, S2, S3 converged at 14:32 IST. S4 check-in response rate was 31% (threshold 40%) — below threshold but trending upward. Rainfall measured at 58mm/hr against 65mm/hr threshold. Mobility index dropped to 28% of baseline. Historical comparison: 3 similar events in BTM Layout over 24 months all qualified. Recommendation: APPROVE with 90-minute recheck on S4.',
  },
  {
    id: 'CE-002', zone: 'Hebbal', date: '2026-03-18', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 1800, status: 'pending',
    auditSummary: 'Signals S1, S3, S4 converged. S2 (mobility) showed 34% baseline drop — below 75% threshold. Fog event consistent with IMD winter forecast. 47 of 103 registered riders confirmed inactivity (46%). Order volume at 22% of baseline. ZoneTwin counterfactual: fog events of this severity historically produce 38–52% rider inactivity. Pattern consistent. Recommendation: APPROVE.',
  },
  {
    id: 'CE-003', zone: 'JP Nagar', date: '2026-03-17', confidence: 'MEDIUM', signals: 3,
    recommendedPayout: 2100, status: 'approved',
    auditSummary: 'All thresholds near-boundary. Approved after 1-hour recheck confirmed S2 dropped to 22%. Payout disbursed.',
  },
];

export const KPIS: KPI[] = [
  { label: 'Loss Ratio', value: '54.2%', delta: '-2.1%', trend: 'down', sparkline: [58, 57, 61, 55, 56, 54, 54] },
  { label: 'Active Policies', value: '1,624', delta: '+47', trend: 'up', sparkline: [1420, 1490, 1530, 1558, 1580, 1601, 1624] },
  { label: 'Payouts This Week', value: '₹3.8L', delta: '+₹1.2L', trend: 'up', sparkline: [18000, 22000, 19000, 31000, 28000, 38000, 38000] },
  { label: 'Zones at Risk', value: '3', delta: '+1', trend: 'up', sparkline: [1, 2, 1, 2, 3, 3, 3] },
];

export const RIDER = {
  name: 'Ravi Kumar',
  riderId: 'AMZFLEX-BLR-04821',
  zone: ZONES[0],
  weeklyEarningsBaseline: 2600,
  tenureWeeks: 28,
  coverageActive: true,
  premiumPaidThisWeek: true,
};
```

**Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: add types and mock data layer"
```

---

### Task 3: App shell — routing + themes

**Files:**
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/components/Layout/RiderLayout.tsx`
- Create: `frontend/src/components/Layout/AdminLayout.tsx`

**Step 1: Set up main.tsx with HashRouter**

```tsx
// frontend/src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </React.StrictMode>
)
```

**Step 2: Create App.tsx with routes**

```tsx
// frontend/src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/Landing'
import RiderDashboard from './pages/RiderDashboard'
import AdminDashboard from './pages/AdminDashboard'
import OnboardingPage from './pages/Onboarding'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/rider" element={<RiderDashboard />} />
      <Route path="/admin" element={<AdminDashboard />} />
      <Route path="/onboarding" element={<OnboardingPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
```

**Step 3: Create stub pages (so routes resolve)**

Create `frontend/src/pages/Landing.tsx`, `RiderDashboard.tsx`, `AdminDashboard.tsx`, `Onboarding.tsx` each with a placeholder `<div>` returning the page name.

**Step 4: Verify routing works**

```bash
npm run dev
```
Navigate to `/#/rider`, `/#/admin`, `/#/onboarding` — each should render the stub text.

**Step 5: Commit**

```bash
git commit -am "feat: add routing shell with HashRouter"
```

---

### Task 4: Landing page (persona selector)

**Files:**
- Modify: `frontend/src/pages/Landing.tsx`

**Step 1: Implement Landing page**

```tsx
// frontend/src/pages/Landing.tsx
import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col items-center justify-center px-4">
      {/* Ambient grid background */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=60 height=60 xmlns=http://www.w3.org/2000/svg%3E%3Cpath d=M 60 0 L 0 0 0 60 fill=none stroke=%23334155 stroke-width=1/%3E%3C/svg%3E')] opacity-30 pointer-events-none" />

      <div className="relative z-10 text-center mb-12">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-amber-500 flex items-center justify-center shadow-lg shadow-amber-500/30">
            <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">ZoneGuard</h1>
        </div>
        <p className="text-slate-400 text-lg max-w-md mx-auto leading-relaxed">
          When the zone goes dark,<br />
          <span className="text-amber-400 font-medium">your income doesn't have to.</span>
        </p>
        <p className="text-slate-500 text-sm mt-3">AI-powered parametric income protection for Amazon Flex riders</p>
      </div>

      {/* Persona cards */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
        {/* Rider card */}
        <button
          onClick={() => navigate('/rider')}
          className="group bg-amber-500/10 border border-amber-500/30 rounded-2xl p-8 text-left hover:bg-amber-500/20 hover:border-amber-400 transition-all duration-200 hover:shadow-xl hover:shadow-amber-500/10 hover:-translate-y-1"
        >
          <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center mb-4 group-hover:bg-amber-500/30 transition-colors">
            <span className="text-2xl">🛵</span>
          </div>
          <h2 className="text-white font-bold text-xl mb-2">I'm a Rider</h2>
          <p className="text-slate-400 text-sm leading-relaxed">View your coverage, track this week's protection, and see payout history</p>
          <div className="mt-4 flex items-center gap-2 text-amber-400 text-sm font-medium">
            <span>Enter Rider Dashboard</span>
            <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>

        {/* Insurer card */}
        <button
          onClick={() => navigate('/admin')}
          className="group bg-blue-500/10 border border-blue-500/30 rounded-2xl p-8 text-left hover:bg-blue-500/20 hover:border-blue-400 transition-all duration-200 hover:shadow-xl hover:shadow-blue-500/10 hover:-translate-y-1"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4 group-hover:bg-blue-500/30 transition-colors">
            <span className="text-2xl">📊</span>
          </div>
          <h2 className="text-white font-bold text-xl mb-2">I'm an Insurer</h2>
          <p className="text-slate-400 text-sm leading-relaxed">Monitor zone risk, review claims, track loss ratios, and manage the QuadSignal engine</p>
          <div className="mt-4 flex items-center gap-2 text-blue-400 text-sm font-medium">
            <span>Enter Admin Dashboard</span>
            <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </button>
      </div>

      {/* Onboarding link */}
      <div className="relative z-10 mt-8">
        <button onClick={() => navigate('/onboarding')} className="text-slate-500 hover:text-slate-300 text-sm underline underline-offset-4 transition-colors">
          New rider? Get covered in 90 seconds →
        </button>
      </div>
    </div>
  )
}
```

**Step 2: Verify visually**

```bash
npm run dev
```
Expected: Dark landing page with two glowing persona cards and ZoneGuard branding.

**Step 3: Commit**

```bash
git commit -am "feat: landing page with persona selector"
```

---

### Task 5: Rider Dashboard — layout + week timeline

**Files:**
- Modify: `frontend/src/pages/RiderDashboard.tsx`
- Create: `frontend/src/components/Rider/WeekTimeline.tsx`
- Create: `frontend/src/components/Rider/CoverageCard.tsx`

**Step 1: Create WeekTimeline component**

```tsx
// frontend/src/components/Rider/WeekTimeline.tsx
import { WeekDay } from '../../types'

interface Props { week: WeekDay[] }

export default function WeekTimeline({ week }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
      <h2 className="text-stone-800 font-bold text-lg mb-1">This Week's Protection</h2>
      <p className="text-stone-500 text-sm mb-6">HSR Layout · Week of Mar 16–22, 2026</p>

      <div className="flex gap-2 md:gap-4 items-end justify-between">
        {week.map((day) => (
          <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
            {/* Earnings / payout label */}
            <div className="text-center min-h-[48px] flex flex-col justify-end">
              {day.status === 'payout' && (
                <>
                  <span className="text-emerald-600 font-bold text-sm">+₹{day.payoutAmount?.toLocaleString()}</span>
                  <span className="text-stone-400 text-xs">ZG payout</span>
                </>
              )}
              {day.status === 'normal' && day.earnings > 0 && (
                <>
                  <span className="text-stone-700 font-semibold text-sm">₹{day.earnings.toLocaleString()}</span>
                  <span className="text-stone-400 text-xs">earned</span>
                </>
              )}
              {day.status === 'normal' && day.earnings === 0 && (
                <span className="text-stone-300 text-xs">Rest day</span>
              )}
            </div>

            {/* Bar */}
            <div className="w-full rounded-xl overflow-hidden flex flex-col justify-end" style={{ height: '80px' }}>
              {day.status === 'payout' && (
                <div
                  className="w-full bg-emerald-500 rounded-xl flex items-center justify-center"
                  style={{ height: '70px' }}
                >
                  <span className="text-white text-lg">⚡</span>
                </div>
              )}
              {day.status === 'normal' && day.earnings > 0 && (
                <div
                  className="w-full bg-amber-400 rounded-xl"
                  style={{ height: `${Math.round((day.earnings / 3000) * 70)}px` }}
                />
              )}
              {day.status === 'normal' && day.earnings === 0 && (
                <div className="w-full bg-stone-100 rounded-xl" style={{ height: '20px' }} />
              )}
            </div>

            {/* Day label */}
            <span className={`text-xs font-semibold ${day.status === 'payout' ? 'text-emerald-600' : 'text-stone-500'}`}>
              {day.day}
            </span>

            {/* Status dot */}
            <div className={`w-2 h-2 rounded-full ${
              day.status === 'payout' ? 'bg-emerald-500' :
              day.status === 'disrupted' ? 'bg-red-400' : 'bg-amber-400'
            }`} />
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-6 pt-4 border-t border-stone-100">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-400" />
          <span className="text-stone-500 text-xs">Normal earnings</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-stone-500 text-xs">ZoneGuard payout</span>
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Create CoverageCard component**

```tsx
// frontend/src/components/Rider/CoverageCard.tsx
import { Zone } from '../../types'

interface Props {
  zone: Zone
  premiumPaid: number
  maxPayout: number
  isActive: boolean
}

const tierColors = {
  low: 'text-emerald-600 bg-emerald-50',
  medium: 'text-amber-600 bg-amber-50',
  high: 'text-orange-600 bg-orange-50',
  'flood-prone': 'text-red-600 bg-red-50',
}

export default function CoverageCard({ zone, premiumPaid, maxPayout, isActive }: Props) {
  return (
    <div className="bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl p-6 text-white shadow-lg shadow-amber-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-amber-100 text-sm font-medium">Weekly Coverage</p>
          <h2 className="text-2xl font-bold mt-0.5">{zone.name}</h2>
          <p className="text-amber-100 text-sm">{zone.pinCode}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-bold ${isActive ? 'bg-white/20 text-white' : 'bg-white/10 text-amber-200'}`}>
          {isActive ? '✓ ACTIVE' : 'INACTIVE'}
        </div>
      </div>

      {/* Premium + Payout */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-white/10 rounded-xl p-3">
          <p className="text-amber-100 text-xs">Premium Paid</p>
          <p className="text-white font-bold text-xl">₹{premiumPaid}</p>
          <p className="text-amber-200 text-xs">this week</p>
        </div>
        <div className="bg-white/10 rounded-xl p-3">
          <p className="text-amber-100 text-xs">Max Payout</p>
          <p className="text-white font-bold text-xl">₹{maxPayout.toLocaleString()}</p>
          <p className="text-amber-200 text-xs">if 4 signals fire</p>
        </div>
      </div>

      {/* Zone risk */}
      <div className="flex items-center justify-between bg-white/10 rounded-xl px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse" />
          <span className="text-amber-100 text-sm">Signals monitored · Live</span>
        </div>
        <span className="text-white text-sm font-semibold capitalize">{zone.riskTier} risk</span>
      </div>
    </div>
  )
}
```

**Step 3: Wire up RiderDashboard**

```tsx
// frontend/src/pages/RiderDashboard.tsx
import { useNavigate } from 'react-router-dom'
import { RIDER, RAVI_WEEK, PAYOUTS } from '../data/mock'
import WeekTimeline from '../components/Rider/WeekTimeline'
import CoverageCard from '../components/Rider/CoverageCard'

export default function RiderDashboard() {
  const navigate = useNavigate()
  const totalEarned = RAVI_WEEK.reduce((s, d) => s + d.earnings, 0)
  const totalPayout = RAVI_WEEK.reduce((s, d) => s + (d.payoutAmount ?? 0), 0)

  return (
    <div className="min-h-screen bg-[#FFFBF3]">
      {/* Top bar */}
      <header className="bg-white border-b border-amber-100 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-amber-600 hover:text-amber-800 transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-stone-800 font-bold text-base">{RIDER.name}</h1>
            <p className="text-stone-500 text-xs">{RIDER.riderId}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-emerald-700 text-xs font-semibold">Covered</span>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-5">
        {/* Coverage card */}
        <CoverageCard
          zone={RIDER.zone}
          premiumPaid={RIDER.zone.weeklyPremium}
          maxPayout={RIDER.zone.maxWeeklyPayout}
          isActive={RIDER.coverageActive}
        />

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Earned this week', value: `₹${totalEarned.toLocaleString()}` },
            { label: 'ZG paid out', value: `₹${totalPayout.toLocaleString()}`, highlight: true },
            { label: 'Total protected', value: `₹${(totalEarned + totalPayout).toLocaleString()}` },
          ].map(({ label, value, highlight }) => (
            <div key={label} className={`rounded-xl p-3 text-center border ${highlight ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-amber-100'}`}>
              <p className={`font-bold text-base ${highlight ? 'text-emerald-700' : 'text-stone-800'}`}>{value}</p>
              <p className="text-stone-500 text-xs mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* Week timeline */}
        <WeekTimeline week={RAVI_WEEK} />

        {/* Payout history */}
        <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
          <h2 className="text-stone-800 font-bold text-lg mb-4">Payout History</h2>
          <div className="space-y-3">
            {PAYOUTS.map((p, i) => (
              <div key={p.id} className={`flex items-center justify-between p-3 rounded-xl border ${i === 0 ? 'bg-emerald-50 border-emerald-200' : 'bg-stone-50 border-stone-100'}`}>
                <div>
                  <p className="text-stone-800 font-semibold text-sm">{p.trigger}</p>
                  <p className="text-stone-500 text-xs">{p.date} · {p.zone} · Ref: {p.upiRef}</p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${i === 0 ? 'text-emerald-600' : 'text-stone-700'}`}>+₹{p.amount.toLocaleString()}</p>
                  <p className="text-stone-400 text-xs">{p.confidence}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Zone signal status */}
        <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center">
              <span className="text-lg">📡</span>
            </div>
            <div>
              <p className="text-stone-800 font-semibold text-sm">Zone Signals Normal</p>
              <p className="text-stone-500 text-xs">All 4 signals monitored · Last checked 3 min ago</p>
            </div>
          </div>
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        </div>
      </main>
    </div>
  )
}
```

**Step 4: Verify visually**

```bash
npm run dev
```
Navigate to `/#/rider`. Expected: warm amber dashboard with timeline, coverage card, payout history.

**Step 5: Commit**

```bash
git commit -am "feat: rider dashboard with week timeline and coverage card"
```

---

### Task 6: Admin Dashboard — layout + KPI strip + zone heatmap

**Files:**
- Modify: `frontend/src/pages/AdminDashboard.tsx`
- Create: `frontend/src/components/Admin/KPIStrip.tsx`
- Create: `frontend/src/components/Admin/ZoneHeatmap.tsx`

**Step 1: Create KPIStrip**

```tsx
// frontend/src/components/Admin/KPIStrip.tsx
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { KPI } from '../../types'

interface Props { kpis: KPI[] }

export default function KPIStrip({ kpis }: Props) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="bg-slate-800 border border-slate-700 rounded-xl p-4">
          <p className="text-slate-400 text-xs font-medium mb-1">{kpi.label}</p>
          <p className="text-white font-bold text-2xl">{kpi.value}</p>
          <div className="flex items-center justify-between mt-2">
            <span className={`text-xs font-medium ${kpi.trend === 'down' && kpi.label === 'Loss Ratio' ? 'text-emerald-400' : kpi.trend === 'up' ? 'text-blue-400' : 'text-slate-400'}`}>
              {kpi.delta} vs last week
            </span>
          </div>
          <div className="h-8 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={kpi.sparkline.map((v, i) => ({ v, i }))}>
                <Line type="monotone" dataKey="v" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ))}
    </div>
  )
}
```

**Step 2: Create ZoneHeatmap**

```tsx
// frontend/src/components/Admin/ZoneHeatmap.tsx
import { useState } from 'react'
import { Zone } from '../../types'

interface Props { zones: Zone[] }

const riskColor = (score: number) => {
  if (score < 30) return '#10B981'   // emerald
  if (score < 55) return '#F59E0B'   // amber
  if (score < 75) return '#F97316'   // orange
  return '#EF4444'                    // red
}

// Approximate SVG positions for 10 Bengaluru zones (normalized 0–100)
const ZONE_POSITIONS: Record<string, { x: number; y: number }> = {
  hsr:             { x: 50, y: 60 },
  koramangala:     { x: 45, y: 55 },
  whitefield:      { x: 78, y: 48 },
  indiranagar:     { x: 52, y: 48 },
  'electronic-city': { x: 55, y: 80 },
  bellandur:       { x: 65, y: 65 },
  'btm-layout':    { x: 48, y: 68 },
  'jp-nagar':      { x: 42, y: 70 },
  yelahanka:       { x: 48, y: 20 },
  hebbal:          { x: 50, y: 32 },
}

export default function ZoneHeatmap({ zones }: Props) {
  const [selected, setSelected] = useState<Zone | null>(null)

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-bold text-lg">Bengaluru Zone Risk Map</h2>
        <div className="flex items-center gap-3 text-xs">
          {[['#10B981','Low'],['#F59E0B','Med'],['#F97316','High'],['#EF4444','Flood']].map(([color, label]) => (
            <div key={label} className="flex items-center gap-1">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              <span className="text-slate-400">{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* SVG Map */}
        <div className="md:col-span-2">
          <svg viewBox="0 0 100 100" className="w-full h-64 bg-slate-900 rounded-xl border border-slate-700">
            {/* City outline approximation */}
            <ellipse cx="50" cy="50" rx="38" ry="44" fill="#1e293b" stroke="#334155" strokeWidth="0.5" />

            {zones.map((zone) => {
              const pos = ZONE_POSITIONS[zone.id]
              if (!pos) return null
              const color = riskColor(zone.riskScore)
              const isSelected = selected?.id === zone.id
              return (
                <g key={zone.id} onClick={() => setSelected(zone)} className="cursor-pointer">
                  <circle
                    cx={pos.x} cy={pos.y}
                    r={isSelected ? 5.5 : 4}
                    fill={color}
                    fillOpacity={0.85}
                    stroke={isSelected ? 'white' : color}
                    strokeWidth={isSelected ? 1 : 0.5}
                  />
                  {zone.riskScore >= 70 && (
                    <circle cx={pos.x} cy={pos.y} r="6" fill={color} fillOpacity="0.15">
                      <animate attributeName="r" values="4;8;4" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="fill-opacity" values="0.15;0;0.15" dur="2s" repeatCount="indefinite" />
                    </circle>
                  )}
                  <text x={pos.x} y={pos.y + 8} textAnchor="middle" fontSize="3" fill="#94a3b8">
                    {zone.name.split(' ')[0]}
                  </text>
                </g>
              )
            })}
          </svg>
        </div>

        {/* Zone detail panel */}
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-4 flex flex-col justify-between">
          {selected ? (
            <>
              <div>
                <h3 className="text-white font-bold text-base">{selected.name}</h3>
                <p className="text-slate-400 text-xs mb-4">{selected.pinCode}</p>
                {[
                  ['Risk Score', `${selected.riskScore}/100`],
                  ['Risk Tier', selected.riskTier],
                  ['Weekly Premium', `₹${selected.weeklyPremium}`],
                  ['Active Riders', selected.activeRiders],
                  ['Disruptions/yr', selected.disruptions],
                  ['Max Payout', `₹${selected.maxWeeklyPayout.toLocaleString()}`],
                ].map(([k, v]) => (
                  <div key={String(k)} className="flex justify-between py-1.5 border-b border-slate-800 last:border-0">
                    <span className="text-slate-400 text-xs">{k}</span>
                    <span className="text-white text-xs font-medium capitalize">{String(v)}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <p className="text-slate-500 text-sm">Click a zone on the map to view risk details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

**Step 3: Stub AdminDashboard page to verify imports**

Wire `KPIStrip` and `ZoneHeatmap` into `frontend/src/pages/AdminDashboard.tsx` (full wire-up continues in Task 7).

**Step 4: Verify**

```bash
npm run dev
```
Expected: `/#/admin` shows dark KPI cards with sparklines and interactive zone map.

**Step 5: Commit**

```bash
git commit -am "feat: admin KPI strip and zone heatmap"
```

---

### Task 7: Admin Dashboard — QuadSignal panel with demo mode

**Files:**
- Create: `frontend/src/components/Admin/QuadSignalPanel.tsx`
- Modify: `frontend/src/pages/AdminDashboard.tsx`

**Step 1: Create QuadSignalPanel**

```tsx
// frontend/src/components/Admin/QuadSignalPanel.tsx
import { useState, useEffect, useRef } from 'react'
import { Signal, SignalStatus, ConfidenceLevel } from '../../types'
import { QUAD_SIGNALS } from '../../data/mock'

const DEMO_SEQUENCE = [
  { signalIdx: 0, value: 'Rainfall: 71mm/hr ⚡', status: 'firing' as SignalStatus, delay: 0 },
  { signalIdx: 1, value: 'Mobility: 18% of baseline ⚡', status: 'firing' as SignalStatus, delay: 1800 },
  { signalIdx: 2, value: 'Orders: 22% of baseline ⚡', status: 'firing' as SignalStatus, delay: 3200 },
  { signalIdx: 3, value: '47/103 riders inactive (46%) ⚡', status: 'firing' as SignalStatus, delay: 4800 },
]

const confidenceLabel = (fired: number): ConfidenceLevel =>
  fired === 4 ? 'HIGH' : fired === 3 ? 'MEDIUM' : fired === 2 ? 'LOW' : 'NOISE'

const confidenceStyle: Record<ConfidenceLevel, string> = {
  HIGH: 'bg-emerald-500/20 border-emerald-400 text-emerald-400',
  MEDIUM: 'bg-amber-500/20 border-amber-400 text-amber-400',
  LOW: 'bg-orange-500/20 border-orange-400 text-orange-400',
  NOISE: 'bg-slate-500/20 border-slate-400 text-slate-400',
}

export default function QuadSignalPanel() {
  const [signals, setSignals] = useState<Signal[]>(QUAD_SIGNALS)
  const [isDemoRunning, setIsDemoRunning] = useState(false)
  const [payoutFired, setPayoutFired] = useState(false)
  const timeouts = useRef<ReturnType<typeof setTimeout>[]>([])

  const firedCount = signals.filter(s => s.status === 'firing').length
  const confidence = confidenceLabel(firedCount)

  const runDemo = () => {
    if (isDemoRunning) return
    // Reset
    setSignals(QUAD_SIGNALS.map(s => ({ ...s, status: 'inactive' })))
    setPayoutFired(false)
    setIsDemoRunning(true)
    timeouts.current.forEach(clearTimeout)
    timeouts.current = []

    DEMO_SEQUENCE.forEach(({ signalIdx, value, status, delay }) => {
      const t = setTimeout(() => {
        setSignals(prev => prev.map((s, i) => i === signalIdx ? { ...s, status, value } : s))
      }, delay)
      timeouts.current.push(t)
    })

    // AUTO-PAYOUT after all signals fire
    const payoutT = setTimeout(() => {
      setPayoutFired(true)
      setIsDemoRunning(false)
    }, 6500)
    timeouts.current.push(payoutT)
  }

  const reset = () => {
    timeouts.current.forEach(clearTimeout)
    setSignals(QUAD_SIGNALS)
    setPayoutFired(false)
    setIsDemoRunning(false)
  }

  useEffect(() => () => timeouts.current.forEach(clearTimeout), [])

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-white font-bold text-lg">QuadSignal Fusion Engine</h2>
          <p className="text-slate-400 text-xs">HSR Layout · 2-hour rolling window · 15-min refresh</p>
        </div>
        <div className="flex gap-2">
          {!isDemoRunning && !payoutFired && (
            <button
              onClick={runDemo}
              className="bg-amber-500 hover:bg-amber-400 text-white font-bold text-xs px-4 py-2 rounded-lg transition-colors"
            >
              ▶ TRIGGER DEMO
            </button>
          )}
          {(isDemoRunning || payoutFired) && (
            <button onClick={reset} className="bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs px-4 py-2 rounded-lg transition-colors">
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Signal cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {signals.map((sig) => (
          <div
            key={sig.id}
            className={`rounded-xl border p-3 transition-all duration-500 ${
              sig.status === 'firing'
                ? 'bg-amber-500/10 border-amber-400 shadow-lg shadow-amber-500/20'
                : 'bg-slate-900 border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-400 text-xs font-bold">{sig.id}</span>
              <div className={`w-2.5 h-2.5 rounded-full ${sig.status === 'firing' ? 'bg-amber-400 animate-pulse' : 'bg-slate-600'}`} />
            </div>
            <p className={`font-semibold text-sm mb-0.5 ${sig.status === 'firing' ? 'text-amber-300' : 'text-white'}`}>{sig.name}</p>
            <p className="text-slate-500 text-xs">{sig.description}</p>
            <div className="mt-2 pt-2 border-t border-slate-700">
              <p className={`text-xs ${sig.status === 'firing' ? 'text-amber-400 font-medium' : 'text-slate-400'}`}>{sig.value}</p>
              <p className="text-slate-600 text-xs">Threshold: {sig.threshold}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Confidence badge */}
      <div className={`border rounded-xl px-4 py-3 flex items-center justify-between transition-all duration-500 ${confidenceStyle[confidence]}`}>
        <div>
          <p className="font-bold text-sm">Confidence: {confidence}</p>
          <p className="text-xs opacity-70">
            {firedCount}/4 signals fired · {
              firedCount === 4 ? 'Automatic payout initiating...' :
              firedCount === 3 ? '1-hour recheck scheduled' :
              firedCount === 2 ? 'Flagged for human review' :
              'No action — monitoring'
            }
          </p>
        </div>
        <span className="text-2xl">{firedCount === 4 ? '⚡' : firedCount >= 2 ? '⚠️' : '📡'}</span>
      </div>

      {/* AUTO-PAYOUT banner */}
      {payoutFired && (
        <div className="mt-4 bg-emerald-500/20 border border-emerald-400 rounded-xl p-4 flex items-center justify-between animate-pulse">
          <div>
            <p className="text-emerald-400 font-bold">AUTO-PAYOUT TRIGGERED</p>
            <p className="text-emerald-300 text-xs">142 riders · HSR Layout · ₹1,950 each · Disbursing via UPI...</p>
          </div>
          <span className="text-3xl">⚡</span>
        </div>
      )}
    </div>
  )
}
```

**Step 2: Create ClaimsQueue component**

```tsx
// frontend/src/components/Admin/ClaimsQueue.tsx
import { useState } from 'react'
import { ClaimEvent } from '../../types'

interface Props { claims: ClaimEvent[] }

export default function ClaimsQueue({ claims }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null)

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-white font-bold text-lg">MEDIUM-Confidence Claims Queue</h2>
        <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2 py-1 rounded-full">
          {claims.filter(c => c.status === 'pending').length} pending
        </span>
      </div>
      <div className="space-y-3">
        {claims.map((claim) => (
          <div key={claim.id} className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
            <div
              className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/50 transition-colors"
              onClick={() => setExpanded(expanded === claim.id ? null : claim.id)}
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${claim.status === 'pending' ? 'bg-amber-400' : claim.status === 'approved' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                <div>
                  <p className="text-white font-semibold text-sm">{claim.zone} · {claim.date}</p>
                  <p className="text-slate-400 text-xs">{claim.signals}/4 signals · ₹{claim.recommendedPayout.toLocaleString()} payout</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${claim.status === 'pending' ? 'bg-amber-500/20 text-amber-400' : claim.status === 'approved' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                  {claim.status}
                </span>
                <svg className={`w-4 h-4 text-slate-500 transition-transform ${expanded === claim.id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
            {expanded === claim.id && (
              <div className="px-4 pb-4 border-t border-slate-800">
                <div className="mt-3 bg-slate-800 rounded-lg p-3">
                  <p className="text-slate-400 text-xs font-semibold mb-1">Claude AI Audit Report</p>
                  <p className="text-slate-300 text-xs leading-relaxed">{claim.auditSummary}</p>
                </div>
                {claim.status === 'pending' && (
                  <div className="flex gap-2 mt-3">
                    <button className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2 rounded-lg transition-colors">Approve Payout</button>
                    <button className="flex-1 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-bold py-2 rounded-lg transition-colors">Reject</button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 3: Wire up full AdminDashboard**

```tsx
// frontend/src/pages/AdminDashboard.tsx
import { useNavigate } from 'react-router-dom'
import { ZONES, KPIS, CLAIMS_QUEUE } from '../data/mock'
import KPIStrip from '../components/Admin/KPIStrip'
import ZoneHeatmap from '../components/Admin/ZoneHeatmap'
import QuadSignalPanel from '../components/Admin/QuadSignalPanel'
import ClaimsQueue from '../components/Admin/ClaimsQueue'

export default function AdminDashboard() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-950 border-b border-slate-800 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-slate-400 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-500 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-white font-bold">ZoneGuard Admin</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          <span className="text-slate-400 text-xs">Live · Bengaluru · 10 zones monitored</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 lg:px-6 py-6 space-y-5">
        <KPIStrip kpis={KPIS} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <ZoneHeatmap zones={ZONES} />
          <QuadSignalPanel />
        </div>
        <ClaimsQueue claims={CLAIMS_QUEUE} />
      </main>
    </div>
  )
}
```

**Step 4: Verify demo mode**

```bash
npm run dev
```
Navigate to `/#/admin`. Click "TRIGGER DEMO" — signals should fire one by one, then AUTO-PAYOUT banner appears.

**Step 5: Commit**

```bash
git commit -am "feat: admin QuadSignal panel with live demo mode and claims queue"
```

---

### Task 8: Onboarding flow (3 steps)

**Files:**
- Modify: `frontend/src/pages/Onboarding.tsx`

**Step 1: Implement 3-step onboarding**

```tsx
// frontend/src/pages/Onboarding.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ZONES } from '../data/mock'

type Step = 1 | 2 | 3 | 4

const tierLabel: Record<string, string> = {
  low: 'Low Risk · ₹29/week',
  medium: 'Medium Risk · ₹49/week',
  high: 'High Risk · ₹69/week',
  'flood-prone': 'Flood-Prone · ₹99/week',
}

export default function OnboardingPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(1)
  const [riderId, setRiderId] = useState('')
  const [selectedZoneId, setSelectedZoneId] = useState('')
  const [earnings, setEarnings] = useState('')

  const selectedZone = ZONES.find(z => z.id === selectedZoneId)

  return (
    <div className="min-h-screen bg-[#FFFBF3] flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => step === 1 ? navigate('/') : setStep((step - 1) as Step)} className="text-amber-600">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-stone-800 font-bold text-lg">Get Covered in 90 Seconds</h1>
            <p className="text-stone-500 text-xs">Step {step} of 3</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1.5 bg-amber-100 rounded-full mb-8">
          <div
            className="h-1.5 bg-amber-500 rounded-full transition-all duration-500"
            style={{ width: `${(Math.min(step, 3) / 3) * 100}%` }}
          />
        </div>

        {/* Step 1: Rider ID */}
        {step === 1 && (
          <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
            <div className="text-4xl mb-4">🪪</div>
            <h2 className="text-stone-800 font-bold text-xl mb-1">What's your Rider ID?</h2>
            <p className="text-stone-500 text-sm mb-6">Find it in your Amazon Flex app under Account → Partner ID</p>
            <input
              value={riderId}
              onChange={e => setRiderId(e.target.value)}
              placeholder="AMZFLEX-BLR-XXXXX"
              className="w-full border border-amber-200 rounded-xl px-4 py-3 text-stone-800 placeholder-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-400 font-mono text-sm"
            />
            <button
              onClick={() => riderId.length >= 5 && setStep(2)}
              disabled={riderId.length < 5}
              className="w-full mt-4 bg-amber-500 hover:bg-amber-400 disabled:bg-amber-200 text-white font-bold py-3 rounded-xl transition-colors"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 2: Zone selector */}
        {step === 2 && (
          <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
            <div className="text-4xl mb-4">📍</div>
            <h2 className="text-stone-800 font-bold text-xl mb-1">Which zone do you primarily work in?</h2>
            <p className="text-stone-500 text-sm mb-4">Select your main delivery zone in Bengaluru</p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {ZONES.map(zone => (
                <button
                  key={zone.id}
                  onClick={() => setSelectedZoneId(zone.id)}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${
                    selectedZoneId === zone.id
                      ? 'border-amber-400 bg-amber-50'
                      : 'border-stone-100 hover:border-amber-200 hover:bg-amber-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-stone-800 font-medium text-sm">{zone.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      zone.riskTier === 'low' ? 'bg-emerald-100 text-emerald-700' :
                      zone.riskTier === 'medium' ? 'bg-amber-100 text-amber-700' :
                      zone.riskTier === 'high' ? 'bg-orange-100 text-orange-700' :
                      'bg-red-100 text-red-700'
                    }`}>₹{zone.weeklyPremium}/wk</span>
                  </div>
                  <p className="text-stone-400 text-xs mt-0.5">{zone.pinCode} · {tierLabel[zone.riskTier]}</p>
                </button>
              ))}
            </div>
            <button
              onClick={() => selectedZoneId && setStep(3)}
              disabled={!selectedZoneId}
              className="w-full mt-4 bg-amber-500 hover:bg-amber-400 disabled:bg-amber-200 text-white font-bold py-3 rounded-xl transition-colors"
            >
              Continue
            </button>
          </div>
        )}

        {/* Step 3: Earnings + quote */}
        {step === 3 && selectedZone && (
          <div className="bg-white rounded-2xl border border-amber-100 shadow-sm p-6">
            <div className="text-4xl mb-4">💰</div>
            <h2 className="text-stone-800 font-bold text-xl mb-1">What do you earn in a typical week?</h2>
            <p className="text-stone-500 text-sm mb-4">We'll use this to calculate your payout if a disruption occurs</p>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-stone-500 font-medium">₹</span>
              <input
                value={earnings}
                onChange={e => setEarnings(e.target.value.replace(/\D/g, ''))}
                placeholder="15000"
                className="w-full border border-amber-200 rounded-xl pl-8 pr-4 py-3 text-stone-800 placeholder-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
            </div>

            {/* Quote card */}
            <div className="mt-5 bg-amber-50 border border-amber-200 rounded-xl p-4">
              <p className="text-stone-600 text-xs font-semibold mb-3 uppercase tracking-wide">Your Coverage Quote</p>
              {[
                ['Zone', selectedZone.name],
                ['Risk tier', selectedZone.riskTier],
                ['Weekly premium', `₹${selectedZone.weeklyPremium}`],
                ['Max payout/week', `₹${selectedZone.maxWeeklyPayout.toLocaleString()}`],
                ['Per-day payout', earnings ? `₹${Math.round(parseInt(earnings) * 0.75 / 7).toLocaleString()} (75% of daily avg)` : '—'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between py-1 border-b border-amber-100 last:border-0">
                  <span className="text-stone-500 text-sm capitalize">{k}</span>
                  <span className="text-stone-800 font-semibold text-sm capitalize">{v}</span>
                </div>
              ))}
            </div>

            <button
              onClick={() => setStep(4)}
              className="w-full mt-4 bg-amber-500 hover:bg-amber-400 text-white font-bold py-3 rounded-xl transition-colors"
            >
              Confirm & Activate Coverage →
            </button>
          </div>
        )}

        {/* Step 4: Success */}
        {step === 4 && selectedZone && (
          <div className="bg-white rounded-2xl border border-emerald-200 shadow-sm p-8 text-center">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-stone-800 font-bold text-2xl mb-1">You're covered!</h2>
            <p className="text-stone-500 text-sm mb-6">{selectedZone.name} · ₹{selectedZone.weeklyPremium}/week · Active now</p>
            <p className="text-stone-400 text-xs mb-8">If all 4 signals converge in your zone, ₹{selectedZone.maxWeeklyPayout.toLocaleString()} lands in your UPI — automatically, within 2 hours.</p>
            <button
              onClick={() => navigate('/rider')}
              className="w-full bg-amber-500 hover:bg-amber-400 text-white font-bold py-3 rounded-xl transition-colors"
            >
              View My Dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Verify all 4 steps**

```bash
npm run dev
```
Navigate to `/#/onboarding`. Walk through all 4 steps, verify the quote updates with earnings input, confirm navigation to `/rider` from success screen.

**Step 3: Commit**

```bash
git commit -am "feat: 3-step onboarding flow with quote calculator"
```

---

### Task 9: GH Pages deployment

**Files:**
- Modify: `frontend/package.json` (add homepage + deploy script)
- Modify: `frontend/vite.config.ts` (set base)

**Step 1: Add homepage to package.json**

Replace `<your-github-username>` with the actual GitHub username:
```json
"homepage": "https://<your-github-username>.github.io/ZoneGuard"
```

**Step 2: Add deploy scripts**

```json
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "predeploy": "npm run build",
  "deploy": "gh-pages -d dist"
}
```

**Step 3: Set vite base path**

```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  base: '/ZoneGuard/',
})
```

**Step 4: Build and verify locally**

```bash
npm run build
```
Expected: `dist/` folder created with `index.html` and assets.

**Step 5: Deploy**

```bash
npm run deploy
```
Expected: gh-pages branch created/updated, site live at `https://<username>.github.io/ZoneGuard/`.

**Step 6: Final commit**

```bash
git add .
git commit -m "feat: configure GH Pages deployment"
```

---

## Summary

| Task | What it builds |
|------|---------------|
| 1 | Vite + React + TS + Tailwind scaffold |
| 2 | Type definitions + full mock data layer |
| 3 | HashRouter app shell with 4 routes |
| 4 | Landing page — persona selector |
| 5 | Rider Dashboard — timeline, coverage, payout history |
| 6 | Admin KPI strip + interactive zone heatmap |
| 7 | QuadSignal panel with live demo mode + claims queue |
| 8 | 3-step onboarding with premium quote calculator |
| 9 | GitHub Pages deployment |
